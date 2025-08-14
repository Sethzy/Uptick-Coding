"""
Purpose: Python API for the lightweight LLM scoring pipeline.
Description: Implements `score_domain` and `score_file` to call an LLM on a
pre-built aggregated context per domain and emit JSONL/CSV outputs.
Key Functions/Classes: `score_domain`, `score_file`.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Iterable, List, Optional

import httpx

from .models import ClassificationResult, LlmInput
from .config import get_openrouter_api_key, get_openrouter_endpoint
from .io_jsonl import iter_llm_inputs_from_jsonl, write_results_jsonl
from .io_csv import write_results_csv
from .logging import log_info, log_error


# AIDEV-NOTE: Minimal schema to satisfy simplified PRD v1.


@dataclass
class LlmConfig:
    model: str = "qwen/qwen3-30b-a3b"
    temperature: float = 0.0
    top_p: float = 1.0
    max_tokens: int = 512
    timeout_seconds: int = 90
    # AIDEV-NOTE: Keep config minimal; prompt is fixed.


OPENROUTER_API_BASE = get_openrouter_endpoint()


def _build_prompt(aggregated_context: str) -> dict:
    system = (
        "You are a strict classifier. Read the aggregated website text. "
        "Output ONLY valid JSON per the schema."
    )
    user = (
        "Goal: Classify the company’s business mix.\n"
        "Definitions:\n"
        "- Classification categories:\n"
        "  - \"Maintenance & Service Only\"\n"
        "  - \"Install Focus\"\n"
        "  - \"50/50 Split\"\n"
        "  - \"Other\"\n"
        "Schema:\n"
        "{\n"
        "  \"classification_category\": \"Maintenance & Service Only|Install Focus|50/50 Split|Other\",\n"
        "  \"rationale\": \"Brief explanation of why this classification was chosen based on the website content\"\n"
        "}\n"
        "Rules:\n"
        "- Temperature: 0. Output JSON only.\n"
        "- Provide a clear, concise rationale (2-3 sentences max).\n\n"
        f"Context (Aggregated):\n{aggregated_context}"
    )
    return {
        "role": "user",
        "content": f"System: {system}\n\nUser:\n{user}",
    }


def _parse_llm_json(raw_text: str) -> dict:
    # AIDEV-NOTE: Strict JSON parse; one simple repair attempt if wrapped in code fences.
    text = raw_text.strip()
    if text.startswith("```") and text.endswith("```"):
        text = text.strip("`")
        # Remove optional language tag lines
        if "\n" in text:
            parts = text.split("\n", 1)
            text = parts[1] if len(parts) > 1 else parts[0]
    return json.loads(text)


def _call_openrouter_sync(client: httpx.Client, cfg: LlmConfig, prompt: dict) -> tuple[dict, dict]:
    api_key = get_openrouter_api_key() or ""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": cfg.model,
        "messages": [
            {"role": "system", "content": "You are a strict JSON-only classifier."},
            prompt,
        ],
        "temperature": cfg.temperature,
        "top_p": cfg.top_p,
        "max_tokens": cfg.max_tokens,
        "response_format": {"type": "json_object"},
    }
    started = time.monotonic()
    resp = client.post(
        f"{OPENROUTER_API_BASE}/chat/completions",
        json=payload,
        headers=headers,
        timeout=cfg.timeout_seconds,
    )
    elapsed_ms = int((time.monotonic() - started) * 1000)
    resp.raise_for_status()
    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    obj = _parse_llm_json(content)
    usage = data.get("usage", {})
    return obj, {"request_ms": elapsed_ms, "token_counts": usage}


def score_domain(
    *,
    domain: str,
    aggregated_context: str,
    model: str = "qwen/qwen3-30b-a3b",
    timeout_seconds: int = 90,
) -> ClassificationResult:
    cfg = LlmConfig(model=model, timeout_seconds=timeout_seconds)
    prompt = _build_prompt(aggregated_context)

    log_info(f"Processing domain: {domain}")
    
    # Simple sync retries on transient errors.
    with httpx.Client() as client:
        attempts = 0
        last_exc: Optional[Exception] = None
        while attempts < 3:
            attempts += 1
            try:
                log_info(f"  Calling LLM (attempt {attempts}/3)...")
                obj, _meta = _call_openrouter_sync(client, cfg, prompt)
                log_info(f"  ✅ Classified as: {obj.get('classification_category', 'Other')}")
                return ClassificationResult(
                    domain=domain,
                    classification_category=obj.get("classification_category", "Other"),
                    rationale=obj.get("rationale", "No rationale provided"),
                )
            except httpx.HTTPStatusError as e:
                if 400 <= e.response.status_code < 500 and e.response.status_code not in (429,):
                    log_error(f"  ❌ HTTP error: {e.response.status_code}")
                    raise
                last_exc = e
                log_error(f"  ⚠️  Retryable error: {e.response.status_code}")
            except Exception as e:
                last_exc = e
                log_error(f"  ⚠️  Network error: {type(e).__name__}")
            time.sleep(0.8 * attempts)
        assert last_exc is not None
        log_error(f"  ❌ Failed after {attempts} attempts")
        raise last_exc


def _iter_llm_inputs_from_jsonl(path: str) -> Iterable[LlmInput]:
    # Backward shim to keep api small; delegate to io_jsonl
    return iter_llm_inputs_from_jsonl(path)


def score_file(
    *,
    input_jsonl: str,
    output_jsonl: Optional[str] = None,
    output_csv: Optional[str] = None,
    model: str = "qwen/qwen3-30b-a3b",
    timeout_seconds: int = 90,
) -> List[ClassificationResult]:
    inputs = list(_iter_llm_inputs_from_jsonl(input_jsonl))
    
    log_info(f"Starting classification of {len(inputs)} domains using model: {model}")
    log_info(f"Outputs: JSONL={output_jsonl or 'none'}, CSV={output_csv or 'none'}")

    results: List[ClassificationResult] = []
    for i, item in enumerate(inputs, 1):
        log_info(f"\n[{i}/{len(inputs)}] Processing domain: {item.domain}")
        try:
            result = score_domain(
                domain=item.domain,
                aggregated_context=item.aggregated_context,
                model=model,
                timeout_seconds=timeout_seconds,
            )
            results.append(result)
        except Exception as e:
            log_error(f"Failed to process {item.domain}: {e}")
            # Continue with next domain instead of failing completely
            continue

    log_info(f"\n✅ Completed {len(results)}/{len(inputs)} domains successfully")
    
    if output_jsonl:
        log_info(f"Writing JSONL to: {output_jsonl}")
        write_results_jsonl(output_jsonl, results)
    if output_csv:
        log_info(f"Writing CSV to: {output_csv}")
        write_results_csv(output_csv, results)

    return results


