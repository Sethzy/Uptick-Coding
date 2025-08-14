<!--
/**
 * Purpose: PRD for an LLM-only lead scoring pipeline delivered in phases.
 * Description: Defines a monolithic-context LLM scoring workflow that outputs CSV + JSONL with A/B/C tiers, 0–100 score,
 *              and up to 3 evidence URLs/snippets per domain. Uses Qwen3 30B A3B; runs LLM on every domain.
 * Key Sections: Overview; Goals; User Stories; Functional Requirements; Non-Goals; Design; Technical; Operational Metrics;
 *               Open Questions; Phased Delivery with Acceptance Criteria.
 */
-->

### PRD — LLM-Only Lead Scoring Pipeline (Phased Delivery)

<!-- AIDEV-NOTE: Based on `/.claude/commands/3a-backend-phase/generate-prd.md` with user selections applied. -->
<!-- AIDEV-NOTE: Monolithic (aggregated) context default; Top‑N fallback handled upstream by aggregator; scorer does not implement it. -->

## 1) Introduction / Overview

This PRD specifies an LLM-first classifier that reads a domain’s crawled content, builds a single aggregated text context per domain (when feasible), and asks an LLM to produce:

- Business mix classification into one of the following buckets: `Maintenance & Service Only`, `Install Focus`, `50/50 Split`, or `Other` (definitions below)
- A confidence value for the classification
- Up to 2–3 strongest evidence URLs/snippets per domain

Outputs are written to both CSV and JSONL. The system runs the LLM for every domain (cost is assumed non-blocking) and uses Qwen3 30B A3B by default (via OpenRouter). Labels come directly from the LLM judgment; no learned model is used initially. Calibration is achieved via fixed thresholds.

## 2) Goals

- Maximize recall (catch as many good leads as possible) while maintaining reasonable precision.
- Provide clear, auditable evidence (URLs + snippets) for each decision.
- Accurately classify companies into the specified business mix buckets; if classification is accurate, the pipeline meets primary business needs.
- Report a confidence value for the assigned category.
- Enable CSV + JSONL output for pipeline and manual audit.
- Support prompt/model versioning.

## 2.1) Business Mix Classification Taxonomy

The LLM must classify each company into exactly one of the following categories based on website content and evidence:

1. Maintenance & Service Only

   Companies focused exclusively on ongoing upkeep and repair of existing fire protection systems. Work is scheduled/recurring (inspections, testing, preventative maintenance). They typically do not handle new installs. Indicators: many recurring small-to-medium jobs, maintenance agreements, service calls, inspection cycles.

2. Install Focus

   Companies primarily engaged in design and installation of new fire protection systems for new construction or major renovations. Work is project-based with longer sales cycles and higher per-project value. Indicators: blueprint/design focus, multi-phase projects, significant initial capex, lower frequency but large ticket size.

3. 50/50 Split

   Balanced model between new installations and ongoing service/maintenance. Indicators: mix of large multi-phase install jobs and smaller recurring service/inspection jobs, roughly even revenue/job count split across install vs service.

4. Other

   Does not clearly belong to the above categories based on available evidence.

The classifier must provide evidence URLs/snippets supporting the assigned category.

## 3) User Stories

- As a Sales Ops Analyst, I want each domain scored with clear evidence so I can quickly validate and approve outreach.
- As a Marketer, I want an A/B/C tier plus a numeric score so I can segment and prioritize campaigns.
- As a Data Engineer, I want deterministic configs, stable CSV/JSONL schemas, and simple CLI/Python APIs for integration.
- As a Founder, I want to hand-audit evidence early (full snippets + URLs) to tune thresholds and prompts.

## 4) Functional Requirements

1. Input Assumptions (Aggregated Context)

   - The classifier consumes an `aggregated_context` string per domain produced by a separate Aggregated Context Builder (see: PRD — Aggregated Context Builder).
   - Minimum expectations for downstream citation validation:
     - Page header format: each page begins with `### [PAGE] <url>`.
     - Separation: insert exactly two blank lines between page sections.
   - Authoritative details (ordering, normalization, deduplication, determinism, token handling) are specified in the Aggregated Context Builder PRD and are out of scope here.

2. LLM Classification

   - For each domain, send the aggregated context to the LLM with a strict JSON schema.
   - Require: `classification_category` (see taxonomy), `confidence` (0–100), `rationale` (short), and up to 3 `evidence` items `{url, snippet}`.
   - Force citation discipline: responses without at least 1 evidence item are invalid and must be retried.
   - Temperature set to 0 (or the model’s equivalent) for stability.

3. Model Support

   - Default model: Qwen3 30B A3B via OpenRouter (low/no cost path for Phase 1).
   - Record `model_name`, `model_version`, and `prompt_version` with each output.

4. Confidence Reporting

   - Require a numeric `confidence` in the classification on a 0–100 scale.
   - Confidence should reflect strength and clarity of evidence and internal agreement across pages.

5. Evidence Extraction & Retention

   - Return up to 3 strongest evidence items per domain by default.
   - Evidence items include full `snippet` text and `url` (no truncation beyond max snippet length config).

6. Output Schemas

   - JSONL: one object per domain with fields listed in Section 6 (Design Considerations).
   - CSV: flat columns including tier, score, top evidence URLs/snippets (up to 3), model/prompt metadata, and run IDs.

7. CLI Interface

   - Provide a CLI command to score a file of domains and produce CSV and/or JSONL.
   - Flags for model selection(s), output formats, thresholds, and max-evidence count.

8. Python API

   - Provide a simple `score_domain()` and `score_file()` API returning structured objects and writing outputs.

9. Configurability

- YAML/JSON config for thresholds, evidence count, token budget, model, and temperature.

10. Logging & Audit

- Log per-domain run metadata: `domain`, `run_id`, `timestamp`, `model`, `prompt_version`, token counts.
- Save the raw LLM response payload alongside parsed outputs for debugging.

11. Error Handling & Retries

- Retry transient LLM/API failures with exponential backoff.
- Validate JSON strictly; re-prompt once with a repair instruction if parsing fails.

## 5) Non-Goals (Out of Scope)

- No supervised learned ranker/model in initial phases (can be reconsidered later).
- No heavy rules engine; page selection heuristics are out of scope for this PRD and are handled upstream by the Aggregated Context Builder.
- No web crawling changes; assumes an existing crawl artifact per domain.

## 6) Design Considerations (Prompts, Schemas, Output)

### 6.1 Prompt (Sketch)

Explain the goal and require strict JSON. Ask for tier, score, rationale, and evidence. Emphasize citations.

```text
System: You are a strict classifier. Read the aggregated website text. Output ONLY valid JSON per the schema.
User:
Goal: Classify the company’s business mix and provide citations (URL + snippet). Include a confidence value.
Definitions:
- Classification categories:
  - "Maintenance & Service Only"
  - "Install Focus"
  - "50/50 Split"
  - "Other"
- Confidence: integer 0–100 indicating how sure you are about the assigned category.
Schema:
{
  "classification_category": "Maintenance & Service Only|Install Focus|50/50 Split|Other",
  "confidence": 0-100,
  "rationale": string,
  "evidence": [
    { "url": string, "snippet": string },
    { "url": string, "snippet": string },
    { "url": string, "snippet": string }
  ]
}
Rules:
- Provide at least 1 evidence item; up to 3.
- Snippets must be quoted from the provided text and include the source URL.
- Temperature: 0. Output JSON only.

Context (Aggregated):
### [PAGE] https://example.com/services
...page text...
### [PAGE] https://example.com/industries
...page text...
```

### 6.2 JSONL Output Object

```json
{
  "domain": "acme.com",
  "classification_category": "Install Focus",
  "confidence": 86,
  "rationale": "Offers fire protection services across industries.",
  "evidence": [
    {
      "url": "https://acme.com/services",
      "snippet": "Fire protection and sprinklers installation"
    },
    {
      "url": "https://acme.com/industries",
      "snippet": "Commercial and industrial fire safety"
    }
  ],
  "model_name": "qwen3-30b-a3b",
  "model_version": "2025-01-01",
  "prompt_version": "v1",
  "classifier_mode": "LLM",
  "run_id": "uuid-...",
  "token_counts": { "input": 5000, "output": 300 }
}
```

### 6.3 CSV Columns

- `domain`, `classification_category`, `confidence`, `rationale`
- `evidence_url_1`, `evidence_snippet_1`, `evidence_url_2`, `evidence_snippet_2`, `evidence_url_3`, `evidence_snippet_3`
- `model_name`, `model_version`, `prompt_version`, `classifier_mode`, `run_id`

### 6.4 LLM Input JSONL (Monolithic Context)

- Purpose: Replace the prior `pages[]` shape with a single, LLM‑friendly aggregated context per domain. Produced upstream by the Aggregated Context Builder; this scorer treats it as input. This is a breaking change; no backward compatibility required.
- Shape (one JSON object per line):

```json
{
  "domain": "example.com",
  "aggregated_context": "### [PAGE] https://example.com/\n...page text...\n\n\n### [PAGE] https://example.com/services\n...page text..."
}
```

- Rules:
  - Page sections must follow the Aggregated Context Builder PRD (ordering, headers, separation, content selection, normalization, deduplication, determinism).
  - The `aggregated_context` is the only content field consumed by the classifier.
  - Crawler/scorer must log the ordered list of included page URLs for audit.

### 6.5 Evidence Discipline

- Require 1–3 evidence items in every model response.
- Each item must include:
  - `url`: must be present in the aggregated page set (i.e., exactly matches a `### [PAGE] <url>` header)
  - `snippet`: verbatim quote from `aggregated_context`
- Snippet handling:
  - Trim to sentence boundaries when possible; cap length to ~320 characters (configurable).
  - Deduplicate across items; prefer diverse URLs/pages where available.
- Validation:
  - Reject responses with no valid evidence or with URLs not present in the aggregated set.
  - Perform a single “repair” re‑prompt on validation failure; if still invalid, record an explicit error and continue.

## 7) Technical Considerations

- Token Budgeting: The scorer does not implement Top‑N fallback or page selection. Upstream aggregation enforces any token limits.
- Page Markers: Prepend each page with a clear header containing the URL to keep citation source visible.
- Normalization: Strip navigation, repeated footers, cookie banners where possible.
- Determinism: Temperature 0; fixed prompt; record versions for reproducibility.
- Concurrency: Safe parallelism per-domain with rate limiting as needed.
- Cost: Ignored per user directive; still log token usage for awareness.

### 7.1 LLM Invocation Defaults (Qwen3 30B A3B via OpenRouter)

- Parameters: temperature 0, top_p 1, bounded `max_tokens`, request timeout 60–90s.
- Retries: Up to 2 on 5xx/429/network/timeout; respect `Retry-After` if provided; short jittered backoff. Do not retry on 4xx auth/validation.
- Logging per call: `model_name`, `model_version` (if available), `prompt_version`, `run_id`, `request_ms`, `token_counts` (input/output), `status`, `error`.
- Output enforcement: Require strict JSON. On parse failure, perform one repair attempt; if still invalid, emit an error record and proceed.

### 7.2 Scale Controls

- Concurrency: Global worker cap (start 3–5). Batch domains with checkpoints to support resume.
- Rate limiting: Token‑bucket with burst caps; centralized handling of 429s with backoff.
- Timeouts and safety: Per‑request timeout; per‑domain attempt cap; simple circuit breaker if sustained error rate exceeds threshold.
- Idempotency/resume: One output line per (domain, model); skip completed on rerun; persist last good state.

## 8) Operational Metrics

- Percentage of outputs with ≥1 valid evidence item.
- JSON parse failure rate < 1%.

## 9) Open Questions

- Default evidence max length per snippet (proposed 320 characters). OK?
- Exact score thresholds for A/B/C (proposed A≥75, B≥50). Confirm?
- For future scoring enhancements, should we derive a rubric from the CEO’s write-up or from hand audits by sales reps, or both?

Note on compatibility:

- The `llm-input.jsonl` format is now a single monolithic `aggregated_context` per domain (Section 6.4). The previous `pages[]` shape is removed and not supported.

## 10) Phased Delivery

### Phase 1 — Baseline LLM Classifier (Monolithic Context)

Scope:

- Monolithic aggregated context per domain (provided by the Aggregated Context Builder).
- Default model: Qwen3 30B A3B via OpenRouter per domain.
- Strict JSON parsing; up to 3 evidence items.
- Output CSV + JSONL; include full snippets and URLs.
- CLI and Python API; record model/prompt versions and run IDs.
- Mandatory classification into one of: Maintenance & Service Only, Install Focus, 50/50 Split, Other.
- Confidence reported on 0–100 scale.

Acceptance Criteria:

1. Given an input list of domains and crawl artifacts, the CLI produces valid CSV and JSONL with required fields.
2. Each domain has classification_category, confidence, rationale, and ≥1 evidence item with URL + snippet.
3. Running with `--model qwen3-30b-a3b` yields outputs per domain with required fields and metadata.
4. All runs record `model_name`, `model_version`, `prompt_version`, `run_id`.

### Phase 2 — Monitoring and Governance

### Phase 3 — Calibration and Reporting

Scope:

- Tune fixed thresholds based on qualitative audits; retain fixed-threshold policy.
- Add richer logs: token counts and overflow rate (if provided by upstream aggregator).

Acceptance Criteria:

1. Thresholds configurable via a single config file and reflected in outputs.
2. Weekly summary includes token usage if available.

### Phase 4 — Future Enhancements (Out of Scope for Now)

Scope:

- Optional secondary scoring or prioritization scheme (deferred by user request).
- Potential confidence calibration analysis once enough labeled audits exist.

Scope:

- Prompt versioning; changelog of prompt edits.

Acceptance Criteria:

1. Prompt versions logged; a changelog file maintained with rationale for changes.

## 11) Interfaces (Sketch)

### 11.1 CLI

```bash
scorer classify \
  --input domains.csv \
  --crawl-dir ./crawl/ \
  --output-csv out.csv \
  --output-jsonl out.jsonl \
  --model qwen3-30b-a3b \
  --threshold-a 75 --threshold-b 50 \
  --max-evidence 3 \
  --prompt-version v1
```

### 11.2 Python API

```python
from scoring import score_domain, score_file

result = score_domain(domain="acme.com", crawl_path="./crawl/acme.json")
score_file(
    input_csv="domains.csv",
    crawl_dir="./crawl/",
    output_csv="out.csv",
    output_jsonl="out.jsonl",
    model="qwen3-30b-a3b",
    thresholds={"A": 75, "B": 50},
    max_evidence=3,
    prompt_version="v1",
)
```

---

<!-- AIDEV-NOTE: Evidence-first for early audit; can reduce snippet length/count later. -->
<!-- AIDEV-NOTE: Keep temperature at 0; enforce strict JSON; retry on validation failure. -->
<!-- AIDEV-TODO: Review CSV column widths and evidence truncation after initial runs. -->
