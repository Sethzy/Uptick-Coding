<!--
/**
 * Purpose: PRD for the Octave Fit Assessor (OFA) module: evidence-first, rubric-driven scoring of company websites.
 * Description: Defines how an LLM evaluates a website strictly from on-site evidence to answer the Octave rubric,
 *              labeling each item Yes/No/Unknown with citations, computing conservative/optimistic scores, coverage,
 *              tiers, and generating a prioritized sales discovery checklist for Unknowns. Integrates alongside the
 *              existing LLM-only classifier pipeline.
 * Key Sections: Overview; Goals; User Stories; Functional Requirements; Non-Goals; Design Considerations; Technical;
 *               Success Metrics; Open Questions; Phased Delivery; Acceptance Criteria.
 */
-->

### PRD — Octave Fit Assessor (Rubric-Driven Evidence-Based Scoring)

<!-- AIDEV-NOTE: Aligns with `/3-tasks/3. scoring-classify/prd-final-llm-scoring-pipeline.md` aggregated-context input. -->
<!-- AIDEV-NOTE: Evidence-gated labels: Yes/No require citations; otherwise Unknown. No negative inference from silence. -->

## 1) Introduction / Overview

The Octave Fit Assessor (OFA) evaluates a company website against a rubric derived from the CEO’s Octave Scoring Rubric. It consumes a monolithic `aggregated_context` string per domain (ordered pages with `### [PAGE] <url>` markers), then answers each rubric item strictly from on‑site evidence.

For each rubric item, OFA returns a label `Yes | No | Unknown`, a confidence (0–100), and 0–3 evidence items `{url, snippet}`. Labels `Yes`/`No` require at least one valid citation; missing citations downgrade to `Unknown`. OFA computes both conservative and optimistic fit scores, coverage, and an A/B/C tier, and emits a prioritized sales discovery checklist for the Unknown items.

## 2) Goals

- Provide an evidence-first, low‑hallucination rubric assessment that abstains when evidence is missing.
- Convert information gaps into a prioritized, plain‑language sales discovery checklist.
- Produce conservative and optimistic overall scores, coverage, and tier for pipeline use.
- Integrate cleanly alongside the existing LLM classifier; share inputs, outputs, and logging.

## 3) User Stories

- As a Sales Rep, I want Unknown rubric items converted into concise questions so I can efficiently run discovery.
- As a Sales Ops Analyst, I want citations for every Yes/No so I can audit and trust the assessment.
- As a Marketer, I want an A/B/C tier and scores to segment accounts while acknowledging evidence coverage.
- As a Founder/CEO, I want strict abstention rules to avoid hallucinations and ensure credibility.

## 4) Functional Requirements

1. Input

   - Consume `{ domain, aggregated_context, included_urls }` per domain.
   - `aggregated_context` uses page headers: `### [PAGE] <url>` with two blank lines between sections.

2. Rubric Evaluation

   - For each rubric item, return: `item_id`, `label` (`Yes|No|Unknown`), `confidence` (0–100), `evidence` (0–3), `notes`.
   - Labels `Yes` or `No` require ≥1 evidence citation; otherwise downgrade to `Unknown`.
   - Ban negative inference: absence of text never implies `No`.

3. Evidence Validation

   - Evidence `url` must be present in `included_urls` (exact match against page headers).
   - Evidence `snippet` must be a verbatim substring of `aggregated_context` under that URL’s section.
   - On invalid evidence, set `label=Unknown` and record a validation error.

4. Scoring & Tiering

   - Maintain a rubric config: items with weights, optional must‑have gates, and business‑impact groups.
   - Compute two scores:
     - Conservative: `Yes = weight; No = 0; Unknown = -λ·weight` (λ default 0.3, configurable).
     - Optimistic: `Yes = weight; No = 0; Unknown = 0`.
   - Coverage = answered_items_with_citations / total_items.
   - Tiering: configurable thresholds (e.g., A ≥ 75, B ≥ 50) on the conservative score; tie‑break by coverage and must‑haves.
   - If coverage < coverage_min (e.g., 40%), force tier = `Needs Discovery`.

5. Sales Discovery Checklist

   - Transform `Unknown` items into 5–10 prioritized, plain‑language questions.
   - Order by weight, must‑have status, and proximity to tier thresholds.

6. Outputs

   - JSONL: per-domain object with per‑item results, scores, coverage, tier, checklist, model/prompt metadata, run_id.
   - CSV: flat columns for domain, scores, tier, coverage, top evidence URLs/snippets, and counts of Yes/No/Unknown.
   - Persist raw LLM response payloads for audit.

7. Reliability & Retries

   - Temperature 0; strict JSON. One repair attempt on parse/validation failure; otherwise emit explicit error.

8. Governance
   - Record `model_name`, `model_version` (if available), `prompt_version`, `run_id`, request_ms, token counts.

## 5) Non-Goals (Out of Scope for MVP)

- No off‑site enrichment sources (e.g., LinkedIn, PR) in MVP; first‑party website only.
- No CRM sync in MVP; export-only CSV/JSONL (CRM integration may follow in later phases).
- No supervised learning or dynamic weighting in MVP; fixed config only.

## 6) Design Considerations

### 6.1 Prompt (Sketch)

Explain the abstention policy, require strict JSON with per‑item results, enforce citations for Yes/No, otherwise `Unknown`.

```text
System: You are a strict, evidence-first assessor. Read the aggregated website text. Output ONLY valid JSON per the schema.
User:
Goal: Assess the company against the rubric using only on-site evidence. Absent evidence => label Unknown. No guessing.
Rules:
- Labels Yes/No require at least one citation: { url, snippet }. Otherwise label Unknown.
- Do not infer No from silence. Temperature: 0. Output JSON only.
Schema:
{
  "domain": string,
  "items": [
    {
      "item_id": string,
      "label": "Yes|No|Unknown",
      "confidence": 0-100,
      "evidence": [ { "url": string, "snippet": string } ],
      "notes": string
    }
  ],
  "rationale": string
}
Context (Aggregated):
### [PAGE] https://example.com/services
...page text...

### [PAGE] https://example.com/about
...page text...
```

### 6.2 JSONL Output Object (Sketch)

```json
{
  "domain": "acme.com",
  "items": [
    {
      "item_id": "asset_based_compliance",
      "label": "Unknown",
      "confidence": 42,
      "evidence": [],
      "notes": "No explicit mention of asset-level tracking"
    }
  ],
  "score_conservative": 61,
  "score_optimistic": 78,
  "coverage": 0.55,
  "tier": "B",
  "checklist": [
    "Do you provide owner/authority portals with real-time asset compliance visibility?"
  ],
  "model_name": "qwen3-30b-a3b",
  "prompt_version": "v1",
  "run_id": "uuid-...",
  "token_counts": { "input": 4800, "output": 400 }
}
```

### 6.3 CSV Columns (Sketch)

- `domain`, `score_conservative`, `score_optimistic`, `coverage`, `tier`
- `yes_count`, `no_count`, `unknown_count`
- `evidence_url_1`, `evidence_snippet_1`, `evidence_url_2`, `evidence_snippet_2`, `evidence_url_3`, `evidence_snippet_3`
- `model_name`, `model_version`, `prompt_version`, `run_id`

## 7) Technical Considerations

- Invocation Defaults: Qwen3 30B A3B via OpenRouter; temperature 0; top_p 1; bounded `max_tokens`; 60–90s timeout.
- Retries: Up to 2 on 5xx/429/network/timeout; one repair prompt on invalid JSON; no retry on 4xx auth/validation.
- Evidence Discipline: enforce URL membership and verbatim substring checks; downgrade to `Unknown` on failure.
- Determinism: fixed prompt and config; record versions and run metadata.
- Concurrency: per-domain parallelism with global worker cap; respect rate limits and backoff.
- Idempotency: one output per (domain, model); resume via checkpoints; skip completed.

## 8) Success Metrics

- ≥ 95% valid JSON outputs with required fields on non‑empty inputs.
- 0 hallucinated citations (verified via substring checks).
- ≥ 80% of Unknown items produce actionable checklist questions.
- Weekly summary includes coverage distribution and proportion of `Needs Discovery` outputs.

## 9) Open Questions

1. Rubric scope: Which 10–15 items constitute MVP? Confirm exact list and wording.
2. Weights: Assign relative weights per item and identify any must‑have gates.
3. Thresholds: Confirm A/B/C boundaries (proposal: A ≥ 75, B ≥ 50) and `coverage_min`.
4. λ (Unknown penalty): Default 0.3? Adjust per early audits?
5. Checklist length: cap at 5, 8, or 10 questions?
6. Evidence snippet length cap: 320 chars default?
7. CRM: Preferred destination and mapping when Phase 3 adds sync (HubSpot object/fields)?

## 10) Phased Delivery

### Phase 1 — MVP

- Fixed rubric config (10–15 items), conservative/optimistic scores, coverage, tier.
- Strict evidence validation; abstain to `Unknown` without citations.
- Sales discovery checklist for Unknowns.
- Outputs: JSONL + CSV, with model/prompt metadata and run IDs.

Acceptance Criteria

1. Given an input list of domains, the CLI produces valid JSONL/CSV including per‑item labels and citations (where applicable).
2. Every `Yes`/`No` item has ≥1 valid citation; otherwise `Unknown`.
3. Outputs include `score_conservative`, `score_optimistic`, `coverage`, `tier`, and a non‑empty checklist for domains with Unknowns.
4. Runs record `model_name`, `model_version` (if available), `prompt_version`, `run_id`, and token counts.

### Phase 2 — Calibration & Reporting

- Tune weights/thresholds based on audits; add must‑have gates.
- Weekly coverage and fit score reporting; anomaly surfacing (evidence failure rates).

### Phase 3 — Human-in-the-Loop & Integration

- Accept salesperson answers for Unknowns; re‑score deterministically with provenance.
- Optional CRM sync; attach checklist and evidence to account/opportunity.

### Phase 4 — Optional Enrichment (Out of Scope for MVP)

- Add clearly tagged non‑website sources (e.g., LinkedIn, press). Maintain source provenance and stricter gating.

---

<!-- AIDEV-TODO: Finalize MVP rubric items, weights, must-haves, thresholds, and checklist templates. -->
<!-- AIDEV-NOTE: Keep temperature at 0; require strict JSON; retry once on validation failure. -->
