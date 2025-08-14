<!-- AIDEV-NOTE: PRD for downstream classification and scoring of crawled content -->

### Product Requirements Document (PRD) — Scoring and Classification for Fire Industry

#### Introduction/Overview

This PRD defines the downstream classification and scoring of domains using the content bundles produced by the crawler PRD (`prd-targeted-domain-crawler.md`). It does not perform crawling; it consumes the JSONL content bundles.

### Goals

- Classify each domain for fire-company status, multi-vertical classification, and core services focus using crawled content.
- Provide per-criterion labels, confidence, and evidence URLs/snippets.

### Inputs

- JSONL content bundle produced by crawler PRD: one record per domain, with page arrays and page-level artifacts (title, URL, language, render_mode, text_length, headings, detected_keywords, evidence_snippets, markdown_path optional).

### Classification approach (LLM-first with guardrails)

- Primary: LLM classification over page-bundled context (top 2–4 pages by signal score) for each criterion; return label, confidence, and citation URLs.
- Guardrails: If token/window limits or cost triggers hit, downgrade to hybrid (keyword rules + smaller LLM) or rules-only with low confidence.
- Aggregate decision per domain from page-level votes using a simple majority with confidence weighting. Provide a single evidence URL/snippet per criterion (best supporting page).

### Scoring model (configurable weights)

- Fire company (0–30)
- Multi-vertical (0–30)
- Core services (install vs. maintenance) (0–30)
- Total (0–90)

### Scoring Rubric → Signal Mapping Matrix

The weights reflect the provided rubric and can be tuned at runtime via configuration.

| Criterion             | Target Labels                                                                       | Scoring                                                                                                                                                | Primary Signals (ordered)                                                                                                                                                       | Evidence Examples                                                        |
| --------------------- | ----------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| Fire company (0–30)   | Fire company vs. unrelated                                                          | +20 if the business clearly provides fire protection services; +10 if brand name contains “fire”, “fire protection”, or “fire & security”; 0 otherwise | Page title/H1 contains fire-related terms; Services mention fire protection; Mentions of NFPA/NAFED/AFSA, etc.; Active/operational website (200+ words on homepage or services) | “Fire protection services”, “fire suppression systems”, “NFPA-certified” |
| Multi-vertical (0–30) | Fire-only; Fire & Security; Fire + HVAC/Plumbing/Mechanical/Water/Energy/Electrical | 30 = Fire-only; 20 = Fire & Security; 10 = Fire plus other non-security trades                                                                         | “Industries/Markets” and Services pages; “About” claims; Footer service taxonomy                                                                                                | “Fire & Security”, “mechanical contracting”, “HVAC and fire”             |
| Core services (0–30)  | Maintenance-only; Both Install + Maintenance; Installation-only                     | 30 = Maintenance/Inspection-only; 20 = Both; 10 = Installation/Commissioning-only; 0 = No keywords found                                               | Keywords: “inspection”, “maintenance”, “protection”, “service contracts”, “monitoring”, “install”, “commissioning”; Look for explicit “maintenance program” pages               | “Annual inspections”, “service & maintenance plans”, “new installs”      |

Notes:

- If ambiguity persists after LLM review, assign the lower score and mark confidence accordingly.
- LLM prompts will require citation of specific page URLs and snippets backing the decision.

### Output Schema (CSV columns appended)

- `crawler_status` (OK | FAIL | RETRY | SKIPPED)
- `crawler_reason` (string; empty when OK)
- `crawl_pages_visited` (int)
- `crawl_ts` (ISO8601)
- `score_fire_company` (0–30)
- `score_multivertical` (0–30)
- `score_core_services` (0–30)
- `score_total` (0–90)
- `evidence_fire_company_url`
- `evidence_fire_company_snippet`
- `confidence_fire_company` (0–1)
- `evidence_multivertical_url`
- `evidence_multivertical_snippet`
- `confidence_multivertical` (0–1)
- `evidence_core_services_url`
- `evidence_core_services_snippet`
- `confidence_core_services` (0–1)
- `classifier_mode` (LLM | HYBRID | RULES)
- `classifier_model` (e.g., gpt-4o-mini, claude-3-haiku), optional

### Success Metrics

- Precision: ≥ 90% agreement with a 30-site golden set on top-level labels (Fire company / Multi-vertical / Core services).
- Auditability: 100% of scored rows include at least one evidence URL and snippet per criterion.

### Non-Goals (Out of Scope)

- Crawling or link discovery.
- Render settings and rate limiting (covered by crawler PRD).

### Acceptance Criteria

- A CSV named `final_merged_hubspot_tam_data_resolved_scored.csv` is produced with all columns above and the same number of rows as the input content bundle domains.
