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

from .models import ClassificationResult, LlmInput, LabeledDatasetRecord, LabeledDatasetResult
from .config import get_openrouter_api_key, get_openrouter_endpoint
from .io_jsonl import iter_llm_inputs_from_jsonl, write_results_jsonl, iter_labeled_dataset_from_jsonl, write_labeled_results_jsonl
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
        "Goal: Classify the company's business mix.\n"
        "Definitions:\n"
        "- Classification categories:\n"
        "  - \"Maintenance & Service Only\"\n"
        "  - \"Install Only\"\n"
        "  - \"50/50 Split\"\n"
        "  - \"Other\"\n"
        "  - \"Not Classifiable\"\n"
        "\n"
        "Detailed Classification Criteria:\n"
        "\n"
        "1. MAINTENANCE & SERVICE ONLY:\n"
        "   - Companies focused exclusively on ongoing upkeep and repair of existing fire protection systems\n"
        "   - Work is primarily scheduled and recurring, based on mandated inspection cycles\n"
        "   - Job tickets: service calls, inspections, testing, preventative maintenance\n"
        "   - High volume of recurring, small-to-medium-sized tickets and maintenance agreements\n"
        "   - RULE: If website mentions ANY installations, automatically classify as Install Only or 50/50 Split\n"
        "\n"
        "2. INSTALL ONLY:\n"
        "   - Companies engaged in design and installation of new fire protection systems\n"
        "   - Project-based work in new construction or major renovation projects\n"
        "   - Job tickets: large, complex projects with multiple phases and significant financial value\n"
        "   - Focus on blueprints, design, and initial capital expenditure projects\n"
        "   - RULE: If website mentions ANY maintenance or service, automatically classify as Maintenance & Service Only or 50/50 Split\n"
        "\n"
        "3. 50/50 SPLIT:\n"
        "   - Balanced business model between new installations and ongoing service/maintenance\n"
        "   - Capacity for large new construction projects AND steady stream of recurring service work\n"
        "   - Job tickets: mix of large multi-phase install jobs and smaller frequent service calls\n"
        "   - RULE: If website mentions BOTH installations AND maintenance/service, classify here\n"
        "\n"
        "4. OTHER:\n"
        "   - Specialized fire protection services not fitting other categories\n"
        "   - Includes: Firestopping, Fireproofing, Kitchen Suppression Systems, Fire Alarms, Portable Extinguishers\n"
        "   - Highly diverse jobs from small single-item services to complex specialized equipment\n"
        "   - Not directly related to large-scale water-based suppression systems or general recurring maintenance\n"
        "\n"
        "5. NOT CLASSIFIABLE:\n"
        "   - Use when website data is insufficient or contains no useful business information\n"
        "   - Cases include: blank/empty aggregated context, website scrape failures\n"
        "   - Websites showing 'Coming Soon', 'Under Construction', or placeholder content\n"
        "   - Content that doesn't mention fire protection services, business activities, or company focus\n"
        "   - RULE: Classify here if aggregated_context is empty, very short (<50 chars), or contains no business-relevant information\n"
        "\n"
        "Market Fit Assessment:\n"
        "\n"
        "1. Website Investment Quality:\n"
        "   Poor:\n"
        "   Pages: 1 page\n"
        "   Indicators: Basic placeholder, minimal content, \"Coming Soon\" sites\n"
        "   Average:\n"
        "   Pages: 1-2 pages\n"
        "   Indicators: Basic company info, some service descriptions, functional but minimal\n"
        "   High Quality:\n"
        "   Pages: 3+ pages\n"
        "   Indicators: Comprehensive website with multiple sections, detailed content, strong online presence\n"
        "\n"
        "2. mostly_does_maintenance_and_service:\n"
        "   Question: Does the company primarily focus on maintenance and service rather than new installations or other services?\n"
        "   Look for: Inspection schedules, maintenance contracts, testing services, recurring service offerings\n"
        "   Target: This helps with scoring 50/50 split companies.\n"
        "   Output: Assess either yes or no.\n"
        "\n"
        "3. participates_in_industry_associations:\n"
        "   Question: Does the company mention membership in fire protection industry associations?\n"
        "   Look for: NFSA, AFSA, local fire protection chapters, industry certifications\n"
        "   Output: Provide a short answer detailing what was found. If nothing was found, output N/A.\n"
        "\n"
        "4. has_multiple_service_territories:\n"
        "   Question: Does the company serve multiple states or regions?\n"
        "   Look for: Multi-state coverage, regional offices, service territory maps\n"
        "   Output: Provide a short answer detailing how many. If nothing was found, output N/A.\n"
        "\n"
        "Schema:\n"
        "{\n"
        "  \"classification_category\": \"Maintenance & Service Only|Install Only|50/50 Split|Other|Not Classifiable\",\n"
        "  \"classification_category_rationale\": \"Brief explanation of why this classification was chosen based on the website content\",\n"
        "  \"website_quality\": \"Poor|Average|High Quality\",\n"
        "  \"mostly_does_maintenance_and_service\": \"yes|no\",\n"
        "  \"participates_in_industry_associations\": \"short answer or N/A\",\n"
        "  \"has_multiple_service_territories\": \"short answer or N/A\"\n"
        "}\n"
        "Rules:\n"
        "- Temperature: 0. Output JSON only.\n"
        "- Provide a clear, concise rationale (2-3 sentences max).\n"
        "- Apply the automatic classification rules strictly.\n"
        "- Consider the overall business focus, not just individual mentions.\n"
        "- If aggregated_context is empty or contains no useful business information, classify as 'Not Classifiable'.\n"
        "- Website quality should be determined based on the number of pages and content depth in the aggregated context.\n"
        "- Website quality assessment is independent of business classification - a \"Poor\" quality site can still be classified into any business category if sufficient information exists.\n"
        "- Market fit assessments should be based on explicit mentions in the website content.\n\n"
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
    record_id: Optional[str] = None,
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
                    website_quality=obj.get("website_quality", "Not Assessed"),
                    mostly_does_maintenance_and_service=obj.get("mostly_does_maintenance_and_service", "Not Assessed"),
                    participates_in_industry_associations=obj.get("participates_in_industry_associations", "Not Assessed"),
                    has_multiple_service_territories=obj.get("has_multiple_service_territories", "Not Assessed"),
                    record_id=record_id,
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
                record_id=getattr(item, 'record_id', None),
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


def score_labeled_domain(
    *,
    record: LabeledDatasetRecord,
    model: str = "qwen/qwen3-30b-a3b",
    timeout_seconds: int = 90,
) -> LabeledDatasetResult:
    """Score a single labeled dataset record using only the aggregated_context field."""
    # Extract only aggregated_context for scoring
    classification_result = score_domain(
        domain=record.domain,
        aggregated_context=record.aggregated_context,
        record_id=record.record_id,
        model=model,
        timeout_seconds=timeout_seconds,
    )
    
    # Create result with all original fields plus classification
    return LabeledDatasetResult(
        domain=record.domain,
        aggregated_context=record.aggregated_context,
        included_urls=record.included_urls,
        overflow=record.overflow,
        length=record.length,
        record_id=record.record_id,
        lead_status=record.lead_status,
        clay_score=record.clay_score,
        associated_note=record.associated_note,
        current_software=record.current_software,
        core_service=record.core_service,
        classification_category=classification_result.classification_category,
        rationale=classification_result.rationale,
    )


def score_labeled_file(
    *,
    input_jsonl: str,
    output_jsonl: Optional[str] = None,
    model: str = "qwen/qwen3-30b-a3b",
    timeout_seconds: int = 90,
) -> List[LabeledDatasetResult]:
    """Score a labeled dataset file, preserving all original fields and adding classification results."""
    records = list(iter_labeled_dataset_from_jsonl(input_jsonl))
    
    log_info(f"Starting classification of {len(records)} labeled dataset records using model: {model}")
    log_info(f"Output: JSONL={output_jsonl or 'none'}")
    log_info("🔒 Only 'aggregated_context' field will be used for classification")

    results: List[LabeledDatasetResult] = []
    for i, record in enumerate(records, 1):
        log_info(f"\n[{i}/{len(records)}] Processing domain: {record.domain}")
        try:
            result = score_labeled_domain(
                record=record,
                model=model,
                timeout_seconds=timeout_seconds,
            )
            results.append(result)
        except Exception as e:
            log_error(f"Failed to process {record.domain}: {e}")
            # Continue with next record instead of failing completely
            continue

    log_info(f"\n✅ Completed {len(results)}/{len(records)} records successfully")
    
    if output_jsonl:
        log_info(f"Writing labeled results to: {output_jsonl}")
        write_labeled_results_jsonl(output_jsonl, results)

    return results


