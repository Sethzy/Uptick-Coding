<!--
/**
 * Purpose: Independent PRD for building an aggregated, LLM-friendly text context per domain.
 * Description: Defines the minimal, deterministic rules to combine crawled pages into one text block with
 *              page headers and spacing, suitable for strict evidence citation downstream.
 * Key Sections: Overview; Goals; Inputs/Outputs; Functional Requirements; Non-Goals; Design Rules; Technical;
 *               Acceptance Criteria; Open Questions; Phasing.
 */
-->

### PRD — Aggregated Context Builder (Independent Component)

<!-- AIDEV-NOTE: Standalone upstream for scorer; avoids Top‑N heuristics per scope decision. -->

## 1) Overview

Build a deterministic, audit-friendly aggregated text string per domain from an existing crawl artifact. The output is consumed by the Scoring Classifier. This component does not do any LLM calls, page ranking, or Top‑N selection logic.

## 2) Goals

- Produce a single `aggregated_context` string per domain that preserves page provenance for citations.
- Ensure deterministic ordering and formatting so runs are reproducible.
- Enforce simple token/size limits by truncating at page boundaries and marking overflow.

## 3) Inputs and Outputs

### 3.1 Inputs

- Per-domain crawl artifact including:
  - `domain` (string)
  - A list of pages with for each page:
    - `url` (string)
    - `markdown_scoped` (string, optional)
    - `markdown_fit` (string, optional)

### 3.2 Output (JSONL shape for downstream scorer)

```json
{
  "domain": "example.com",
  "aggregated_context": "### [PAGE] https://example.com/\n...page text...\n\n\n### [PAGE] https://example.com/services\n...page text...",
  "included_urls": ["https://example.com/", "https://example.com/services"],
  "overflow": false,
  "length": { "chars": 12345, "approx_tokens": 2500 }
}
```

## 4) Functional Requirements

1. Page Ordering (Deterministic)

   - Order pages as:
     - Homepage first (prefer exact `/` or canonical root).
     - All remaining pages by (path length asc, URL asc).

2. Section Header and Separation

   - Each page section must begin with a single line: `### [PAGE] <url>`.
   - Insert exactly two blank lines between page sections.

3. Content Selection Per Page

   - Homepage: Must be `markdown_scoped`.
   - Subpages: Must be `markdown_fit`;
   - If empty for a page, skip that page.

4. Normalization

   - Collapse repeated whitespace.
   - Strip link targets (keep anchor text), cookie banners, and boilerplate nav/footers when easily identifiable.
   - Preserve headings and any content used for verbatim citation downstream.

5. Deduplication

   - If two pages normalize to identical content, keep the first by order and drop duplicates.

6. Token/Size Budgeting (No Top‑N Heuristics)

   - Maintain a running approximate token count.
   - If the budget would be exceeded when adding the next page, stop before adding it.
   - Set `overflow=true` when truncation occurs; do not attempt relevance heuristics or Top‑N selection.

7. Determinism and Auditability
   - Given the same inputs and config, the output must be byte-identical.
   - Record `included_urls` in order and a `length` object with character count and approximate tokens.

## 5) Non-Goals (Out of Scope)

- No page ranking or Top‑N fallback heuristics.
- No LLM calls or JSON validation of downstream responses.
- No dashboards or metrics beyond basic length bookkeeping.

## 6) Design Rules (Authoritative)

- Header format: exactly `### [PAGE] <url>` on its own line.
- Separation: exactly two blank lines between sections.
- Encoding: UTF‑8; normalize newlines to `\n`.
- Approximate token estimation: any simple estimator (e.g., chars / 4) is acceptable initially; implementation detail.

## 7) Technical Considerations

- Performance: linear pass over pages; avoid extra allocations where possible.
- Config:
  - `max_tokens` (or `max_chars`) with a reasonable default (e.g., ~8k tokens equivalent).
  - `high_intent_routes` list is configurable but defaults provided above.
- Logging: write included URL list and overflow flag; keep logs human‑readable.

## 8) Acceptance Criteria

1. Given a crawl artifact, the tool outputs a JSON object containing `domain`, `aggregated_context`, `included_urls`, `overflow`, and `length`.
2. The `aggregated_context` uses the exact header and separation rules defined above.
3. With the same inputs/config, two runs produce byte‑identical outputs.
4. When the size limit would be exceeded, the tool truncates at the prior page boundary and sets `overflow=true`.

## 9) Open Questions

- Default size budget (proposed: ~8k tokens equivalent). OK?
- Should certain routes (e.g., `/blog/`) be deprioritized or excluded by default? Initial proposal: include by deterministic order; revisit later.

## 10) Phasing

- Phase 1 (MLS): Implement sections 1–7 exactly as specified; no heuristics.
- Phase 2 (Optional later): Allow configurable exclusions or soft filters (still deterministic) if needed.

---

<!-- AIDEV-NOTE: This PRD replaces any aggregator details previously embedded in the Scoring PRD. -->
