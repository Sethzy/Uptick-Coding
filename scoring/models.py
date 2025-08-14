"""
Purpose: Model invocation wrapper for the scoring pipeline.
Description: Calls Qwen3 30B A3B via OpenRouter, enforces JSON-only response, performs single repair on parse failure.
Key Functions/Classes: classify_domain_with_model.
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, Optional, Tuple
import random
import asyncio

import httpx

from .config import ScoringConfig
from .schema import ModelClassification, get_model_classification_json_schema


# AIDEV-NOTE: For v1, keep a simple single-model wrapper; do not generalize prematurely.


def _build_prompt(aggregated_context: str, prompt_version: str) -> str:
    schema_snippet = get_model_classification_json_schema()
    # AIDEV-NOTE: Evidence removed per PRD; instruct JSON-only with exact fields.
    user = (
        "Goal: Classify the company’s business mix and output ONLY JSON (json). Include a confidence value.\n"
        "Definitions (base your decision on the ticket/project mix described in the context):\n"
        "- Maintenance & Service Only: Companies focused exclusively on ongoing upkeep and repair of existing systems; recurring inspections; service calls, testing, preventative maintenance.\n"
        "- Install Focus: Primarily design and installation of new systems for new construction or major renovations; project-based; higher revenue per project.\n"
        "- 50/50 Split: Balanced mix of new installations and ongoing service/maintenance.\n"
        "- Other: Use only if none of the above clearly applies. When selecting Other, also provide a concise sublabel (3-6 words, e.g., 'Security company') and a 2-3 sentence definition explaining it.\n"
        "- Confidence: integer 0–100 indicating how sure you are about the assigned category.\n\n"
        "Schema (required JSON fields):\n"
        f"{schema_snippet}\n\n"
        "Rules:\n"
        "- Output ONLY a single JSON object with EXACTLY these fields. No prose, no markdown, no extra keys.\n"
        "- If classification_category is 'Other', include both 'other_sublabel' (3-6 words) and 'other_sublabel_definition' (2-3 sentences).\n"
        "- Temperature: 0.\n\n"
        "Minimal example JSON (not evidence-based):\n"
        "{\n  \"classification_category\": \"Install Focus\",\n  \"confidence\": 80,\n  \"rationale\": \"Clear description of installation-focused services.\"\n}\n\n"
        "Context (Aggregated):\n"
        f"{aggregated_context}"
    )
    system = (
        "You are a strict classifier. Output ONLY valid JSON per the schema (json)."
    )
    # AIDEV-NOTE: prompt_version is currently unused in text; kept for future prompt routing.
    return json.dumps({"system": system, "user": user})


async def _request_with_retries(
    client: httpx.AsyncClient,
    cfg: ScoringConfig,
    prompt_payload: Dict[str, Any],
) -> httpx.Response:
    attempts = 0
    delay = cfg.retry.base_delay_ms / 1000.0
    last_error: Optional[Exception] = None
    while attempts < cfg.retry.max_attempts:
        try:
            resp = await _post_openrouter(
                client,
                cfg.model,
                prompt_payload,
                cfg.timeout_s,
                cfg.endpoint_base_url,
            )
            if resp.status_code >= 500 or resp.status_code == 429:
                raise httpx.HTTPStatusError("server error", request=resp.request, response=resp)
            return resp
        except (httpx.TimeoutException, httpx.RequestError, httpx.HTTPStatusError) as e:
            last_error = e
            attempts += 1
            if attempts >= cfg.retry.max_attempts:
                break
            # Respect Retry-After header if present
            retry_after = 0.0
            try:
                if isinstance(e, httpx.HTTPStatusError):
                    ra = e.response.headers.get("Retry-After")
                    if ra:
                        retry_after = float(ra)
            except Exception:
                retry_after = 0.0
            jitter = random.uniform(0, delay / 4)
            sleep_s = max(retry_after, delay + jitter)
            await asyncio.sleep(sleep_s)
            delay = min(delay * 2, cfg.retry.max_delay_ms / 1000.0)
            # Recreate client headers/state is handled by caller; here we assume the same client can be reused
            continue
    # If we exit loop, raise the last error
    if last_error:
        raise last_error
    raise httpx.HTTPError("request failed without error context")

def _extract_content_text(raw_text: str) -> Tuple[str, Optional[Dict[str, Any]]]:
    """Handle OpenRouter/OpenAI envelopes and return the content text containing the JSON object.

    Returns (content_text, usage_dict).
    """
    try:
        data = json.loads(raw_text)
        # If it's already the schema dict, return original text (no evidence expected)
        if isinstance(data, dict) and {"classification_category", "confidence", "rationale"}.issubset(data.keys()):
            return raw_text, data.get("usage") if isinstance(data.get("usage"), dict) else None
        # OpenAI/OpenRouter envelope
        if isinstance(data, dict) and "choices" in data:
            choices = data.get("choices") or []
            if choices:
                msg = choices[0].get("message") or {}
                content = msg.get("content")
                if isinstance(content, str):
                    return content, data.get("usage") if isinstance(data.get("usage"), dict) else None
                # Some providers return content as list of parts
                if isinstance(content, list) and content:
                    # Try to concatenate text fields
                    text_parts = []
                    for part in content:
                        if isinstance(part, dict) and "text" in part:
                            text_parts.append(part["text"])
                    if text_parts:
                        return "".join(text_parts), data.get("usage") if isinstance(data.get("usage"), dict) else None
        # Fallback: return original as content
        return raw_text, None
    except Exception:
        return raw_text, None


def _parse_model_json(text: str) -> Tuple[Optional[ModelClassification], Optional[str]]:
    # Extract potential content from envelopes first
    content_text, _usage = _extract_content_text(text)
    # Strip markdown fences if present
    content_text = _strip_markdown_code_fences(content_text)
    # Fast path: try to parse as-is
    try:
        data = json.loads(content_text)
    except Exception as e:
        # Try to extract a JSON object substring
        extracted = _extract_json_object(content_text)
        if extracted is None:
            return None, f"json_parse_error: {e}"
        try:
            data = json.loads(extracted)
        except Exception as e2:
            return None, f"json_parse_error: {e2}"
    try:
        return ModelClassification.model_validate(data), None
    except Exception as e:
        return None, f"schema_validation_error: {e}"


def _strip_markdown_code_fences(text: str) -> str:
    t = text.strip()
    if t.startswith("```") and t.endswith("```"):
        # remove first and last line fences
        lines = t.splitlines()
        if len(lines) >= 3 and lines[0].startswith("```") and lines[-1].startswith("```"):
            return "\n".join(lines[1:-1]).strip()
    return t


def _extract_json_object(text: str) -> Optional[str]:
    """Extract the first top-level JSON object using brace counting.

    Returns None if no plausible object is found.
    """
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(text)):
        ch = text[i]
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return text[start:i+1]
    return None


async def _post_openrouter(
    client: httpx.AsyncClient,
    model: str,
    payload: Dict[str, Any],
    timeout_s: int,
    base_url: str,
) -> httpx.Response:
    # AIDEV-NOTE: Reads OPENROUTER_KEY via client headers configured by caller.
    return await client.post(
        url=f"{base_url}/chat/completions",
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": payload["system"]},
                {"role": "user", "content": payload["user"]},
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "max_tokens": payload.get("max_tokens"),
        },
        timeout=timeout_s,
    )


async def classify_domain_with_model(
    client: httpx.AsyncClient,
    cfg: ScoringConfig,
    aggregated_context: str,
    prompt_version: str,
) -> Tuple[Optional[ModelClassification], Dict[str, Any]]:
    """
    Execute a single classification call with strict JSON enforcement and one repair attempt.

    Returns a tuple of (parsed_model, metadata). On failure, parsed_model is None and metadata contains error info and raw text.
    """
    prompt_payload = json.loads(_build_prompt(aggregated_context, prompt_version))
    # Inject max_tokens from config to reduce truncation risk
    prompt_payload["max_tokens"] = cfg.max_tokens

    meta: Dict[str, Any] = {
        "model_name": cfg.model,
        "prompt_version": prompt_version,
        "request_ms": 0,
        "token_counts": {"input": None, "output": None},
        "status": "ok",
        "error": None,
        "raw": None,
    }

    t0 = time.perf_counter()
    try:
        resp = await _request_with_retries(client, cfg, prompt_payload)
        meta["request_ms"] = int((time.perf_counter() - t0) * 1000)
        raw_text = resp.text
        meta["raw"] = raw_text
        parsed, err = _parse_model_json(raw_text)
        # Handle empty content in JSON mode: quick retry
        if parsed is None:
            try:
                content_text, _ = _extract_content_text(raw_text)
                if not (content_text or "{}"):  # empty string -> retry path
                    resp = await _request_with_retries(client, cfg, prompt_payload)
                    meta["raw"] = resp.text
                    parsed, err = _parse_model_json(resp.text)
            except Exception:
                pass
        if parsed is not None:
            return parsed, meta
        # Attempt single repair on parse/schema failure
        repair_text = raw_text + "\n\nOutput ONLY valid JSON per the schema."
        resp2 = await _request_with_retries(client, cfg, {**prompt_payload, "user": repair_text})
        meta["request_ms"] += int((time.perf_counter() - t0) * 1000)
        meta["raw"] = resp2.text
        parsed2, err2 = _parse_model_json(resp2.text)
        if parsed2 is not None:
            return parsed2, meta
        meta["status"] = "invalid_json"
        meta["error"] = err2 or err or "invalid_json_after_repair"
        return None, meta
    except httpx.TimeoutException as e:
        meta["status"] = "timeout"
        meta["error"] = str(e)
        return None, meta
    except httpx.HTTPStatusError as e:
        meta["status"] = "http_error"
        meta["error"] = str(e)
        return None, meta
    except Exception as e:
        meta["status"] = "unhandled_error"
        meta["error"] = str(e)
        return None, meta


