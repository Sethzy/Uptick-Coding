# 🏗️ Scoring API Architecture Diagram

## Overview

The `scoring/api.py` file implements a lightweight LLM scoring pipeline for domain classification using OpenRouter API calls. It automatically handles both raw crawler data and enriched HubSpot data.

## 🎯 Core Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SCORING API (api.py)                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────────┐ │
│  │   Input Data    │    │  LLM Processing │    │    Output Results       │ │
│  │                 │    │                 │    │                         │ │
│  │ • Raw Crawler   │───▶│ • OpenRouter    │───▶│ • Classification       │ │
│  │ • Enriched      │    │ • JSON Parsing  │    │ • Numerical Scores     │ │
│  │ • JSONL Files   │    │ • Retry Logic   │    │ • All Fields Preserved │ │
│  └─────────────────┘    └─────────────────┘    └─────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 🔄 Data Flow Diagram

```
┌─────────────────┐
│   Input JSONL   │
│   (Raw/Enriched)│
└─────────┬───────┘
          │
          ▼
┌─────────────────────────────────────────────────┐
│           score_raw_crawler_file()              │
│  ┌─────────────────────────────────────────────┐ │
│  │ 1. Auto-detect data type                   │ │
│  │    • Check for HubSpot indicators          │ │
│  │    • Choose appropriate parser             │ │
│  └─────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────┐ │
│  │ 2. Process each record                     │ │
│  │    • Extract domain & context              │ │
│  │    • Call score_domain()                   │ │
│  │    • Preserve all original fields          │ │
│  └─────────────────────────────────────────────┘ │
└─────────┬───────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────┐
│              score_domain()                     │
│  ┌─────────────────────────────────────────────┐ │
│  │ 1. Build LLM prompt                        │ │
│  │    • Classification criteria               │ │
│  │    • Market fit assessment                 │ │
│  │    • JSON schema requirements              │ │
│  └─────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────┐ │
│  │ 2. Call OpenRouter API                      │ │
│  │    • Retry logic (3 attempts)              │ │
│  │    • Error handling                         │ │
│  │    • JSON response parsing                  │ │
│  └─────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────┐ │
│  │ 3. Calculate numerical scores               │ │
│  │    • Use numerical_scoring module           │ │
│  │    • Generate score breakdown               │ │
│  └─────────────────────────────────────────────┘ │
└─────────┬───────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────┐
│              Output JSONL                       │
│  • All original fields preserved               │
│  • Classification results added                │
│  • Numerical scores included                   │
└─────────────────────────────────────────────────┘
```

## 🧩 Function Relationships

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FUNCTION HIERARCHY                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                    PUBLIC API FUNCTIONS                                 │ │
│  │                                                                         │ │
│  │  score_raw_crawler_file() ◄─── Main entry point for all scoring        │ │
│  │  │                              • Handles both raw & enriched data     │ │
│  │  │                              • Auto-detects data type               │ │
│  │  │                              • Preserves all fields                 │ │
│  │  └─────────────────────────────────────────────────────────────────────┘ │
│  │                                                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                    CORE SCORING FUNCTION                               │ │
│  │                                                                         │ │
│  │  score_domain() ◄─── Processes individual domains                      │ │
│  │  │                    • Builds LLM prompts                            │ │
│  │  │                    • Calls OpenRouter API                           │ │
│  │  │                    • Handles retries & errors                       │ │
│  │  │                    • Calculates numerical scores                    │ │
│  │  └─────────────────────────────────────────────────────────────────────┘ │
│  │                                                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                    HELPER FUNCTIONS                                     │ │
│  │                                                                         │ │
│  │  _build_prompt() ◄─── Creates LLM prompts                              │ │
│  │  _parse_llm_json() ◄─── Parses LLM responses                          │ │
│  │  _call_openrouter_sync() ◄─── Makes API calls                          │ │
│  │                                                                         │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 🔍 Data Type Detection Logic

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DATA TYPE AUTO-DETECTION                             │
├─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │ 1. Read first line of JSONL file                                       │ │
│  │ 2. Parse JSON object                                                    │ │
│  │ 3. Check for HubSpot indicators:                                        │ │
│  │    • 'Company name'                                                     │ │
│  │    • 'Record ID'                                                        │ │
│  │    • 'Employee Count'                                                   │ │
│  │    • 'Founded'                                                          │ │
│  └─────────────────────────────────────────────┬───────────────────────────┘ │
│                                                │                            │
│  ┌─────────────────┐    ┌─────────────────────┐ │                            │
│  │   ENRICHED      │    │      RAW CRAWLER    │ │                            │
│  │     DATA        │    │        DATA         │ │                            │
│  │                 │    │                     │ │                            │
│  │ • HubSpot +     │    │ • Crawler only      │ │                            │
│  │   Crawler       │    │ • Basic fields      │ │                            │
│  │ • Business      │    │ • No enrichment     │ │                            │
│  │   context       │    │                     │ │                            │
│  │                 │    │                     │ │                            │
│  └─────────────────┘    └─────────────────────┘ │                            │
│                                                │                            │
│  ┌─────────────────────────────────────────────┴───────────────────────────┐ │
│  │ 4. Choose appropriate parser:                                            │ │
│  │    • Enriched: iter_enriched_records_from_jsonl()                      │ │
│  │    • Raw: iter_crawler_records_from_jsonl()                            │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 🎯 LLM Prompt Structure

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            LLM PROMPT ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                           SYSTEM MESSAGE                                │ │
│  │  "You are a strict classifier. Read the aggregated website text.      │ │
│  │   Output ONLY valid JSON per the schema."                              │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                           USER MESSAGE                                  │ │
│  │  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  │ 1. Classification Categories                                        │ │
│  │  │    • Maintenance & Service Only                                     │ │
│  │  │    • Install Only                                                   │ │
│  │  │    • 50/50 Split                                                    │ │
│  │  │    • Other                                                          │ │
│  │  │    • Not Classifiable                                               │ │
│  │  └─────────────────────────────────────────────────────────────────────┘ │
│  │  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  │ 2. Market Fit Assessment                                            │ │
│  │  │    • Website Investment Quality                                     │ │
│  │  │    • Maintenance vs Installation Focus                              │ │
│  │  │    • Certifications & Compliance                                    │ │
│  │  │    • Service Territories                                            │ │
│  │  │    • Parent Company Status                                          │ │
│  │  └─────────────────────────────────────────────────────────────────────┘ │
│  │  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  │ 3. JSON Schema Requirements                                         │ │
│  │  │    • Strict output format                                           │ │
│  │  │    • Temperature: 0                                                 │ │
│  │  │    • Clear rationale (2-3 sentences)                                │ │
│  │  └─────────────────────────────────────────────────────────────────────┘ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                           CONTEXT DATA                                  │ │
│  │  • Aggregated website content                                           │ │
│  │  • Crawler-extracted information                                        │ │
│  │  • Multiple page content                                                │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 🔄 Retry Logic & Error Handling

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        RETRY & ERROR HANDLING FLOW                         │
├─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                           RETRY LOOP                                    │ │
│  │  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  │  Attempt 1: Call OpenRouter API                                      │ │
│  │  │  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  │  │ Success: Return result                                            │ │
│  │  │  │ Failure: Log error, continue                                      │ │
│  │  │  └─────────────────────────────────────────────────────────────────┘ │
│  │  └─────────────────────────────────────────────────────────────────────┘ │
│  │  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  │  Attempt 2: Call OpenRouter API                                      │ │
│  │  │  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  │  │ Success: Return result                                            │ │
│  │  │  │ Failure: Log error, continue                                      │ │
│  │  │  └─────────────────────────────────────────────────────────────────┘ │
│  │  └─────────────────────────────────────────────────────────────────────┘ │
│  │  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  │  Attempt 3: Call OpenRouter API                                      │ │
│  │  │  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  │  │ Success: Return result                                            │ │
│  │  │  │ Failure: Raise final exception                                    │ │
│  │  │  └─────────────────────────────────────────────────────────────────┘ │
│  │  └─────────────────────────────────────────────────────────────────────┘ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                           ERROR TYPES                                   │ │
│  │  • HTTP 4xx (Client errors): Fail immediately                          │ │
│  │  • HTTP 5xx (Server errors): Retry                                     │ │
│  │  • HTTP 429 (Rate limit): Retry                                         │ │
│  │  • Network errors: Retry                                                │ │
│  │  • JSON parsing errors: Retry                                           │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                           BACKOFF STRATEGY                              │ │
│  │  • Wait time: 0.8 * attempt_number seconds                             │ │
│  │  • Attempt 1: 0.8s delay                                               │ │
│  │  • Attempt 2: 1.6s delay                                               │ │
│  │  • Attempt 3: 2.4s delay                                               │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 📊 Output Data Structure

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            OUTPUT DATA STRUCTURE                            │
├─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                        ORIGINAL FIELDS                                  │ │
│  │  • domain, aggregated_context, included_urls                           │ │
│  │  • html_keywords_found, length, record_id                              │ │
│  │  • crawl_status, failure_reason, pages_visited                         │ │
│  │  • overflow (if present)                                                │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                    HUBSPOT ENRICHMENT FIELDS                           │ │
│  │  • Company name, State, Country, Industry                              │ │
│  │  • Employee Count, Founded, Website                                     │ │
│  │  • Contact information, Lead status                                     │ │
│  │  • Current software, Core services                                      │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                      CLASSIFICATION RESULTS                             │ │
│  │  • classification_category                                              │ │
│  │  • rationale                                                            │ │
│  │  • website_quality                                                      │ │
│  │  • mostly_does_maintenance_and_service                                  │ │
│  │  • has_certifications_and_compliance_standards                          │ │
│  │  • has_multiple_service_territories                                     │ │
│  │  • has_parent_company                                                   │ │
│  │  • using_competitor_software                                            │ │
│  │  • part_of_known_fire_protection_association                            │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                        NUMERICAL SCORES                                │ │
│  │  • final_score (integer)                                                │ │
│  │  • score_breakdown (detailed scoring)                                   │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 🚀 Key Benefits

1. **🔄 Automatic Data Type Detection**: Works with both raw and enriched data
2. **🛡️ Robust Error Handling**: Retry logic with exponential backoff
3. **📊 Field Preservation**: Maintains all original data throughout processing
4. **🎯 Smart Classification**: Comprehensive business model analysis
5. **🔢 Numerical Scoring**: Automated scoring with detailed breakdowns
6. **⚡ Efficient Processing**: Batch processing with individual error isolation

## 🔧 Usage Examples

```python
# Score enriched data (recommended)
results = score_raw_crawler_file(
    input_jsonl="enriched_data.jsonl",
    output_jsonl="scored_results.jsonl",
    model="qwen/qwen3-30b-a3b-instruct-2507"
)

# Score raw crawler data
results = score_raw_crawler_file(
    input_jsonl="raw_crawler_data.jsonl",
    output_jsonl="scored_results.jsonl"
)
```

This architecture provides a robust, flexible scoring system that automatically adapts to different data types while preserving all information and providing comprehensive business classification results.
