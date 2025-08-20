"""
Purpose: Python API for the lightweight LLM scoring pipeline.
Description: Implements `score_domain` and `score_labeled_file` to call an LLM on a
pre-built aggregated context per domain and emit JSONL outputs with classification results.
Key Functions/Classes: `score_domain`, `score_labeled_domain`, `score_labeled_file`.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple

import httpx

from .models import ClassificationResult, LabeledDatasetRecord, LabeledDatasetResult, CrawlerRecord
from .config import get_openrouter_api_key, get_openrouter_endpoint, get_default_model
from .io_jsonl import iter_labeled_dataset_from_jsonl, write_labeled_results_jsonl, iter_crawler_records_from_jsonl, iter_enriched_records_from_jsonl
from .scoring_logging import log_info, log_error
from .numerical_scoring import calculate_numerical_score


# AIDEV-NOTE: Minimal schema to satisfy simplified PRD v1.


@dataclass
class LlmConfig:
    model: str = None  # Will be set from environment if None
    temperature: float = 0.0
    top_p: float = 1.0
    max_tokens: int = 512
    timeout_seconds: int = 90
    # AIDEV-NOTE: Keep config minimal; prompt is fixed.
    
    def __post_init__(self):
        if self.model is None:
            self.model = get_default_model()


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
        "   - RULE: If website mentions ANY installations, automatically classify as Install Only or 50/50 Split\n"
        "\n"
        "2. INSTALL ONLY:\n"
        "   - Companies engaged in design and installation of new fire protection systems\n"
        "   - Project-based work in new construction or renovation projects\n"
        "   - RULE: If website mentions ANY maintenance or service, automatically classify as Maintenance & Service Only or 50/50 Split\n"
        "\n"
        "3. 50/50 SPLIT:\n"
        "   - Balanced business model between new fire protection installations and ongoing fire protection service/maintenance\n"
        "   - Capacity for installation projects AND steady stream of recurring maintenance and service work\n"
        "   - Job tickets: mix of install jobs and smaller frequent service calls\n"
        "   - RULE: If website mentions BOTH installations AND maintenance/service, classify here\n"
        "\n"
        "4. OTHER:\n"
        "   - All services provided are not directly related to fire protection (i.e. marketing company)\n"
        "\n"
        "5. NOT CLASSIFIABLE:\n"
        "   - Use when website data is insufficient or contains no useful business information\n"
        "   - Cases include: blank/empty aggregated context, website scrape failures\n"
        "   - Websites showing 'Coming Soon', 'Under Construction', or placeholder content\n"
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
        "   Question: Does the company primarily focus on ongoing upkeep and repair of existing fire protection systems rather than design and installation of new fire protection systems or other services?\n"
        "   Look for: service calls, inspections, testing, preventative maintenance, and recurring fire protection offerings\n"
        "   Target: This helps with scoring 50/50 split companies.\n"
        "   Output: Assess either yes or no.\n"
        "\n"
        "3. has_certifications_and_compliance_standards:\n"
        "   Question: Does the company mention any professional certifications, licenses, or compliance with specific regulatory standards?\n"
        "   Look for: State licenses, manufacturer certifications, technician credentials, NFPA standards (25, 72, 13), UL standards, specific code references, compliance certifications\n"
        "   Output: Provide a short answer detailing what was found. If nothing was found, output N/A.\n"
        "\n"
        "4. has_multiple_service_territories:\n"
        "   Question: Does the company operate in more than one distinct city/area, or does it have multiple branches or offices?\n"
        "   Output: If they operate in 2 or more distinct cities/areas OR have multiple branches/offices, list all locations. If they only operate in a single city/area with no mention of multiple branches, output N/A.\n"
        "   Examples:\n"
        "   - Multiple cities: 'Alhambra, CA; Artesia, CA; Burbank, CA' → List all\n"
        "   - Single city: 'Los Angeles, CA' → N/A\n"
        "   - Multiple branches in same city: 'Downtown LA office, West LA office' → List all\n"
        "   - Broad regions: 'Southern California' or 'Texas' → N/A (too vague)\n"
        "   - Multiple specific cities: 'Los Angeles, CA; San Diego, CA; Phoenix, AZ' → List all\n"
        "\n"
        "5. has_parent_company:\n"
        "   Question: Do they have a parent company?\n"
        "   Look for: any variations of. it does not need to be case sensitive or exact phrasing. use common sense.\n"
        "   Examples: Pye Barker, API Group, Summit Companies, Sciens Building Solutions, Cintas, Guardian Fire Protection, Hiller Fire, Impact Fire, Fortis Fire & Safety, Zeus Fire & Security\n"
        "   Output: Provide a short answer detailing what was found. If nothing was found, output N/A.\n"
        "\n"
        "6. Full list of services offered:\n"
        "   Question: What specific services does this company offer?\n"
        "   Look for: All mentioned services, both fire protection related and other business services\n"
        "   Output: Always output one of these 3 categories with the specific services listed:\n"
        "   - Fire Protection Only - [list fire protection services]\n"
        "   - Fire Protection and Other Services - [list fire protection services], [list other services]\n"
        "   - Other Services Only - [list other services]\n"
        "   Examples:\n"
        "   - Fire Protection Only - Fire alarm system installation, Fire sprinkler maintenance, Emergency lighting\n"
        "   - Fire and Other Services - Fire alarm installation, HVAC services, Plumbing, Electrical work\n"
        "   - Other Services Only - HVAC services, Plumbing, Electrical work, General contracting\n"
        "\n"
        "Schema:\n"
        "{\n"
        "  \"classification_category\": \"Maintenance & Service Only|Install Only|50/50 Split|Other|Not Classifiable\",\n"
        "  \"classification_category_rationale\": \"Brief explanation of why this classification was chosen based on the website content\",\n"
        "  \"website_quality\": \"Poor|Average|High Quality\",\n"
        "  \"mostly_does_maintenance_and_service\": \"yes|no\",\n"
        "  \"has_certifications_and_compliance_standards\": \"short answer or N/A\",\n"
        "  \"has_multiple_service_territories\": \"short answer or N/A\",\n"
        "  \"has_parent_company\": \"short answer or N/A\",\n"
        "  \"full_list_of_services_offered\": \"comprehensive list of services or N/A\"\n"
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


def _score_keyword_fields(html_keywords_found: List[str]) -> Tuple[str, str]:
    """
    Score the two keyword-based fields directly from html_keywords_found.
    
    Args:
        html_keywords_found: List of keywords found during crawling
        
    Returns:
        Tuple of (using_competitor_software, part_of_known_fire_protection_association)
    """
    # Initialize with N/A
    using_competitor_software = "N/A"
    part_of_known_fire_protection_association = "N/A"
    
    if not html_keywords_found:
        return using_competitor_software, part_of_known_fire_protection_association
    
    # Convert to lowercase for case-insensitive matching
    keywords_lower = [kw.lower() for kw in html_keywords_found]
    
    # Check for competitor software keywords
    competitor_keywords = [
        "building report", "buildingreports.com", "inspect point", "inspectpoint.com", 
        "inspectpoint", "buildops", "buildops.com", "service trade", "servicetrade.com"
    ]
    
    found_competitor = None
    for keyword in competitor_keywords:
        if keyword in keywords_lower:
            # Find the original case from html_keywords_found
            for original_kw in html_keywords_found:
                if keyword in original_kw.lower():
                    found_competitor = original_kw
                    break
            if found_competitor:
                break
    
    if found_competitor:
        using_competitor_software = found_competitor
    elif len([kw for kw in keywords_lower if any(comp in kw for comp in competitor_keywords)]) > 1:
        using_competitor_software = "Multiple platforms"
    
    # Check for fire protection association keywords
    association_keywords = [
        "nfpa", "national fire protection association", "nafed", 
        "national association of fire equipment distributors", "afsa", 
        "american fire sprinkler association", "nfsa", "national fire sprinkler association",
        "cfsa", "canadian fire safety association", "casa", 
        "canadian automatic sprinkler association"
    ]
    
    found_associations = []
    for keyword in association_keywords:
        for original_kw in html_keywords_found:
            if keyword in original_kw.lower():
                found_associations.append(original_kw)
                break
    
    if len(found_associations) == 1:
        part_of_known_fire_protection_association = found_associations[0]
    elif len(found_associations) > 1:
        part_of_known_fire_protection_association = "Multiple associations"
    
    return using_competitor_software, part_of_known_fire_protection_association


def score_domain(
    *,
    domain: str,
    aggregated_context: str,
    html_keywords_found: Optional[List[str]] = None,
    record_id: Optional[str] = None,
    model: str = None,
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
                
                # Score keyword-based fields directly from html_keywords_found
                if html_keywords_found:
                    using_competitor_software, part_of_known_fire_protection_association = _score_keyword_fields(html_keywords_found)
                    log_info(f"  🔍 Keywords found: {html_keywords_found}")
                    log_info(f"  💻 Competitor software: {using_competitor_software}")
                    log_info(f"  🏛️  Fire protection association: {part_of_known_fire_protection_association}")
                else:
                    using_competitor_software = "N/A"
                    part_of_known_fire_protection_association = "N/A"
                
                # Create base classification result
                classification_result = ClassificationResult(
                    domain=domain,
                    classification_category=obj.get("classification_category", "Other"),
                    rationale=obj.get("classification_category_rationale", "No rationale provided"),
                    website_quality=obj.get("website_quality", "Not Assessed"),
                    mostly_does_maintenance_and_service=obj.get("mostly_does_maintenance_and_service", "Not Assessed"),
                    has_certifications_and_compliance_standards=obj.get("has_certifications_and_compliance_standards", "Not Assessed"),
                    has_multiple_service_territories=obj.get("has_multiple_service_territories", "Not Assessed"),
                    has_parent_company=obj.get("has_parent_company", "Not Assessed"),
                    full_list_of_services_offered=obj.get("full_list_of_services_offered", "Not Assessed"),
                    using_competitor_software=using_competitor_software,
                    part_of_known_fire_protection_association=part_of_known_fire_protection_association,
                    record_id=record_id,
                )
                
                # Calculate numerical score
                try:
                    scoring_result = calculate_numerical_score(classification_result)
                    classification_result.final_score = scoring_result["final_score"]
                    classification_result.score_breakdown = scoring_result["score_breakdown"]
                    log_info(f"  🔢 Numerical score: {scoring_result['final_score']}")
                except Exception as e:
                    log_error(f"  ⚠️  Failed to calculate numerical score: {e}")
                    # Continue without numerical score
                
                return classification_result
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


# AIDEV-NOTE: Removed redundant score_enriched_hubspot_domain and score_enriched_hubspot_file functions
# score_raw_crawler_file now handles both raw and enriched data automatically with better field preservation


def score_raw_crawler_file(
    *,
    input_jsonl: str,
    output_jsonl: Optional[str] = None,
    model: str = None,
    timeout_seconds: int = 90,
) -> List[dict]:
    """
    Score raw crawler records, automatically detecting and preserving enriched data.
    
    This function preserves ALL fields from the input data (crawler + HubSpot fields)
    throughout the scoring process, even though only 'aggregated_context' is used
    for classification.
    """
    # Try to detect enriched data by checking if extra fields exist
    with open(input_jsonl, 'r') as f:
        first_line = f.readline().strip()
        if first_line:
            sample_obj = json.loads(first_line)
            # Check if this looks like enriched data (has HubSpot fields)
            hubspot_indicators = ['Company name', 'Record ID', 'Employee Count', 'Founded']
            is_enriched = any(field in sample_obj for field in hubspot_indicators)
        else:
            is_enriched = False
    
    if is_enriched:
        log_info("📊 Detected enriched data (crawler + HubSpot) - preserving ALL fields")
        records = list(iter_enriched_records_from_jsonl(input_jsonl))
    else:
        log_info("🔧 Detected raw crawler data - using CrawlerRecord model")
        records = list(iter_crawler_records_from_jsonl(input_jsonl))
    
    log_info(f"Starting classification of {len(records)} raw crawler records using model: {model}")
    log_info(f"Output: JSONL={output_jsonl or 'none'}")
    log_info("🔒 Only 'aggregated_context' field will be used for classification")
    log_info("📊 All crawler fields (html_keywords_found, included_urls, length, overflow, etc.) will be preserved")

    results: List[dict] = []
    for i, record in enumerate(records, 1):
        # Handle both dict (enriched) and CrawlerRecord objects
        if isinstance(record, dict):
            domain = record["domain"]
            aggregated_context = record["aggregated_context"]
            record_id = record.get("record_id") or record.get("Record ID")
            crawl_status = record.get("crawl_status", "UNKNOWN")
            pages_visited = record.get("pages_visited", 0)
            failure_reason = record.get("failure_reason")
        else:
            domain = record.domain
            aggregated_context = record.aggregated_context
            record_id = record.record_id
            crawl_status = record.crawl_status
            pages_visited = record.pages_visited
            failure_reason = record.failure_reason
        
        log_info(f"\n[{i}/{len(records)}] Processing domain: {domain}")
        log_info(f"   🎯 Status: {crawl_status}, Pages: {pages_visited}, Reason: {failure_reason}")
        
        try:
            classification_result = score_domain(
                domain=domain,
                aggregated_context=aggregated_context,
                html_keywords_found=record.get("html_keywords_found") if isinstance(record, dict) else getattr(record, "html_keywords_found", None),
                record_id=record_id,
                model=model,
                timeout_seconds=timeout_seconds,
            )
            
            # Create result preserving ALL original fields plus classification
            result = record.dict() if hasattr(record, 'dict') else dict(record)
            
            # Add classification results
            result.update({
                "classification_category": classification_result.classification_category,
                "rationale": classification_result.rationale,
                "website_quality": classification_result.website_quality,
                "mostly_does_maintenance_and_service": classification_result.mostly_does_maintenance_and_service,
                "has_certifications_and_compliance_standards": classification_result.has_certifications_and_compliance_standards,
                "has_multiple_service_territories": classification_result.has_multiple_service_territories,
                "has_parent_company": classification_result.has_parent_company,
                "full_list_of_services_offered": classification_result.full_list_of_services_offered,
                "using_competitor_software": classification_result.using_competitor_software,
                "part_of_known_fire_protection_association": classification_result.part_of_known_fire_protection_association,
                "final_score": classification_result.final_score,
                "score_breakdown": classification_result.score_breakdown,
            })
            results.append(result)
            
        except Exception as e:
            log_error(f"Failed to process {domain}: {e}")
            # Continue with next record instead of failing completely
            continue

    log_info(f"\n✅ Completed {len(results)}/{len(records)} records successfully")
    log_info("🎯 All crawler fields preserved through scoring process")
    
    if output_jsonl:
        log_info(f"Writing results to: {output_jsonl}")
        with open(output_jsonl, "w", encoding="utf-8") as f:
            for result in results:
                f.write(json.dumps(result, ensure_ascii=False))
                f.write("\n")

    return results


