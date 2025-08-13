<!--
/**
 * Purpose: PRD for an LLM-only lead scoring pipeline delivered in phases.
 * Description: Defines a monolithic-context LLM scoring workflow that outputs CSV + JSONL with A/B/C tiers, 0–100 score,
 *              and up to 3 evidence URLs/snippets per domain. Uses Qwen3 30B A3B and DeepSeek R1; runs LLM on every domain.
 * Key Sections: Overview; Goals; User Stories; Functional Requirements; Non-Goals; Design; Technical; Success Metrics;
 *               Open Questions; Phased Delivery with Acceptance Criteria.
 */
-->

### PRD — LLM-Only Lead Scoring Pipeline (Phased Delivery)

<!-- AIDEV-NOTE: Based on `/.claude/commands/3a-backend-phase/generate-prd.md` with user selections applied. -->
<!-- AIDEV-NOTE: Monolithic (aggregated) context default; Top‑N page fallback only on token overflow. -->

## 1) Introduction / Overview

This PRD specifies an LLM-first classifier that reads a domain’s crawled content, builds a single aggregated text context per domain (when feasible), and asks an LLM to produce:

- Business mix classification into one of the following buckets: `Maintenance & Service Only`, `Install Focus`, `50/50 Split`, or `Other` (definitions below)
- A confidence value for the classification
- Up to 2–3 strongest evidence URLs/snippets per domain

Outputs are written to both CSV and JSONL. The system runs the LLM for every domain (cost is assumed non-blocking) and compares two models: Qwen3 30B A3B and DeepSeek R1. Labels come directly from the LLM judgment; no learned model is used initially. Calibration is achieved via fixed thresholds and a small curated regression set (30–50 domains) for ongoing audit and stability.

## 2) Goals

- Maximize recall (catch as many good leads as possible) while maintaining reasonable precision.
- Provide clear, auditable evidence (URLs + snippets) for each decision.
- Accurately classify companies into the specified business mix buckets; if classification is accurate, the pipeline meets primary business needs.
- Report a confidence value for the assigned category.
- Enable CSV + JSONL output for pipeline and manual audit.
- Support prompt/model versioning and A/B evaluation across Qwen3 30B A3B and DeepSeek R1.

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

1. Context Building (Monolithic by Default)

   - Concatenate domain pages into a single normalized text block with page headers (e.g., `### [PAGE] <url>`), preserving source mapping for citations.
   - Normalize whitespace, remove boilerplate/duplicated blocks, and keep a running token estimate.
   - If token budget exceeded, fall back to Top‑N most relevant pages (auto-selected by heuristic relevance).

2. Relevance Heuristics (Fallback Only)

   - Rank pages by presence of domain-relevant cues (e.g., terms from services/industries/associations), recency, and uniqueness.
   - Select Top‑N (configurable; default 5) if monolithic context overflow occurs.

3. LLM Classification

   - For each domain, send the aggregated context to the LLM with a strict JSON schema.
   - Require: `classification_category` (see taxonomy), `confidence` (0–100), `rationale` (short), and up to 3 `evidence` items `{url, snippet}`.
   - Force citation discipline: responses without at least 1 evidence item are invalid and must be retried.
   - Temperature set to 0 (or the model’s equivalent) for stability.

4. Model Support

   - Support both Qwen3 30B A3B and DeepSeek R1; allow running one or both per domain.
   - Record `model_name`, `model_version`, and `prompt_version` with each output.

5. Confidence Reporting

   - Require a numeric `confidence` in the classification on a 0–100 scale.
   - Confidence should reflect strength and clarity of evidence and internal agreement across pages.

6. Evidence Extraction & Retention

   - Return up to 3 strongest evidence items per domain by default.
   - Evidence items include full `snippet` text and `url` (no truncation beyond max snippet length config).

7. Output Schemas

   - JSONL: one object per domain with fields listed in Section 6 (Design Considerations).
   - CSV: flat columns including tier, score, top evidence URLs/snippets (up to 3), model/prompt metadata, and run IDs.

8. CLI Interface

   - Provide a CLI command to score a file of domains and produce CSV and/or JSONL.
   - Flags for model selection(s), output formats, thresholds, and max-evidence count.

9. Python API

   - Provide a simple `score_domain()` and `score_file()` API returning structured objects and writing outputs.

10. Configurability

- YAML/JSON config for thresholds, evidence count, Top‑N fallback size, token budget, model(s), and temperature.

11. Logging & Audit

- Log per-domain run metadata: `domain`, `run_id`, `timestamp`, `model`, `prompt_version`, token counts.
- Save the raw LLM response payload alongside parsed outputs for debugging.

12. Regression Set & Metrics

- Maintain a small curated set (30–50 domains) with human-checked expected outcomes for weekly regression.
- Compute and report Precision@K and PR‑AUC on the regression set (using curated expectations).

13. Error Handling & Retries

- Retry transient LLM/API failures with exponential backoff.
- Validate JSON strictly; re-prompt once with a repair instruction if parsing fails.

## 5) Non-Goals (Out of Scope)

- No supervised learned ranker/model in initial phases (can be reconsidered later).
- No heavy rules engine beyond minimal page relevance heuristics used only as a fallback.
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

## 7) Technical Considerations

- Token Budgeting: Use monolithic context by default; estimate tokens; on overflow, switch to Top‑N pages (configurable).
- Page Markers: Prepend each page with a clear header containing the URL to keep citation source visible.
- Normalization: Strip navigation, repeated footers, cookie banners where possible.
- Determinism: Temperature 0; fixed prompt; record versions for reproducibility.
- Concurrency: Safe parallelism per-domain with rate limiting as needed.
- Cost: Ignored per user directive; still log token usage for awareness.

## 8) Success Metrics

- Primary: Accuracy and macro‑F1 for business mix categorization on the curated regression set.
- Operational: Percentage of outputs with ≥1 valid evidence item; JSON parse failure rate < 1%.
- Stability: Weekly runs over regression set show ≤ 5% variance in accuracy (same model/prompt).

## 9) Open Questions

- Default Top‑N value on overflow (proposed 5). OK?
- Default evidence max length per snippet (proposed 320 characters). OK?
- Exact score thresholds for A/B/C (proposed A≥75, B≥50). Confirm?
- Do we want dual‑model output per row (both models’ scores) or single selected model? Proposed: both.
- Should we collect a small hand-audited set labeled with the four business mix categories to measure classification accuracy explicitly?
- For future scoring enhancements, should we derive a rubric from the CEO’s write-up or from hand audits by sales reps, or both?

## 10) Phased Delivery

### Phase 1 — Baseline LLM Classifier (Monolithic Context)

Scope:

- Monolithic aggregated context per domain; Top‑N fallback on overflow.
- Run both Qwen3 30B A3B and DeepSeek R1 per domain.
- Strict JSON parsing; up to 3 evidence items.
- Output CSV + JSONL; include full snippets and URLs.
- CLI and Python API; record model/prompt versions and run IDs.
- Mandatory classification into one of: Maintenance & Service Only, Install Focus, 50/50 Split, Other.
- Confidence reported on 0–100 scale.
- Regression set (30–50) stored and runnable; compute classification accuracy and macro‑F1.

Acceptance Criteria:

1. Given an input list of domains and crawl artifacts, the CLI produces valid CSV and JSONL with required fields.
2. Each domain has classification_category, confidence, rationale, and ≥1 evidence item with URL + snippet.
3. Running with `--models qwen3-30b-a3b,deepseek-r1` yields two outputs per domain or a combined CSV with model columns.
4. Regression command runs the curated set and reports classification accuracy and macro‑F1.
5. All runs record `model_name`, `model_version`, `prompt_version`, `run_id`.

### Phase 2 — Monitoring, Governance, and A/B Controls

### Phase 3 — Calibration, Confidence Calibration, and Reporting

Scope:

- Tune fixed thresholds based on observed Precision@K on curated set; retain fixed-threshold policy.
- Optional reporting of percentile ranks (for dashboards) without changing decision thresholds.
- Add richer logs: token counts, overflow rate, fallback Top‑N usage rate.

Acceptance Criteria:

1. Thresholds configurable via a single config file and reflected in outputs.
2. Percentile rank reported in JSONL (non-binding) and optionally in CSV.
3. Weekly regression report includes stability metrics and token usage summary.

### Phase 4 — Future Enhancements (Out of Scope for Now)

Scope:

- Optional secondary scoring or prioritization scheme (deferred by user request).
- Potential confidence calibration analysis (e.g., ECE) once enough labeled audits exist.

Scope:

- Prompt versioning; changelog of prompt edits.
- Side-by-side model comparison mode (per run) and historical rollups.
- Simple dashboards or summary reports for Precision@K, PR‑AUC, and stability over time.

Acceptance Criteria:

1. Ability to run A/B with two prompts and/or two models in one command and compare metrics.
2. Prompt versions logged; a changelog file maintained with rationale for changes.
3. Summary report lists deltas vs prior week on key metrics.

## 11) Interfaces (Sketch)

### 11.1 CLI

```bash
scorer classify \
  --input domains.csv \
  --crawl-dir ./crawl/ \
  --output-csv out.csv \
  --output-jsonl out.jsonl \
  --models qwen3-30b-a3b,deepseek-r1 \
  --threshold-a 75 --threshold-b 50 \
  --max-evidence 3 \
  --topn-on-overflow 5 \
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
    models=["qwen3-30b-a3b", "deepseek-r1"],
    thresholds={"A": 75, "B": 50},
    max_evidence=3,
    topn_on_overflow=5,
    prompt_version="v1",
)
```

---

<!-- AIDEV-NOTE: Evidence-first for early audit; can reduce snippet length/count later. -->
<!-- AIDEV-NOTE: Keep temperature at 0; enforce strict JSON; retry on validation failure. -->
<!-- AIDEV-TODO: Decide dual-model output shape in CSV (split files vs extra columns). -->
