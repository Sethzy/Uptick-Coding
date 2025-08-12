## Relevant Files

- `crawler/run_crawl.py` - Orchestrates homepage crawl; integrate link preview/scoring, selection pipeline, tie-breakers, cap, blog/news rule, logging.
- `crawler/link_selection.py` - Implement whitelist/service-area filters, bucket mapping, deterministic ranking helpers.
- `crawler/extraction.py` - Persist diagnostics on selected pages: `bucket`, scores, `selection_reason`, `matched_slugs`.
- `crawler/config.json` - Add optional toggles/thresholds (query, score_threshold, max_links, concurrency) if config-driven.
- `crawler/tests/test_link_selection.py` - Unit tests for filters, whitelist tiers, tie-breakers determinism.
- `crawler/tests/test_extraction.py` - Tests for persisted fields and blog/news constraint handling.
- `crawler/tests/test_output_writer.py` - JSON output integrity with new fields.

### Notes

- Keep selection deterministic with stable sorts and fixed epsilon for ties.
- Default contextual query: "fire protection sprinkler inspection testing alarm suppression"; field weights Title 0.50, Meta 0.25, Anchor 0.20, URL 0.05; total blend 0.6/0.4.
- Hard-exclude any `service-area`/`service area` before scoring. Top-level service pages must match whitelist; apply tiered boosts.

## Tasks

- [ ] 1.0 Integrate Crawl4AI link preview and scoring in homepage crawl

  - [ ] 1.1 Enable `score_links=True` in `CrawlerRunConfig` and add `LinkPreviewConfig` with `include_internal`, `max_links≈30`, `concurrency≈5`, `timeout≈5s`.
  - [ ] 1.2 Set default contextual query (overridable) and `score_threshold` (e.g., 0.3) for initial filtering.
  - [ ] 1.3 Ensure head extraction populates `head_data`; fall back to Anchor/URL if unavailable (scores may be lower).
  - [ ] 1.4 Wire in access to `intrinsic_score`, `contextual_score`, `total_score` per link from `result.links.internal`.

- [ ] 2.0 Implement pattern/slug rules (whitelist tiers, hard-exclude service-area, product de-prioritization)

  - [ ] 2.1 Hard-exclude: filter out links whose path/anchor contains `service-area` or `service area` (case-insensitive) pre-scoring.
  - [ ] 2.2 Detect services hub and children (`/services`, `/services/*`) and apply strong boost in selection.
  - [ ] 2.3 Top-level service pages without hub: eligible only if slug contains whitelisted terms; apply Tier 1 > Tier 2 boosts.
  - [ ] 2.4 De-prioritize product catalogs versus Services/About; optionally cap to at most one product link if competing for cap.

- [ ] 3.0 Rank and select links (total score blend, thresholding, deterministic tie-breakers, cap=4)

  - [ ] 3.1 Compute `total_score = 0.6*contextual + 0.4*intrinsic`; skip below threshold before final sort.
  - [ ] 3.2 Stable sort by `total_score` desc; for ties within epsilon, apply: bucket priority asc → path length asc → URL asc.
  - [ ] 3.3 Deduplicate by normalized URL; select top unique up to cap=4; ensure deterministic output.
  - [ ] 3.4 Preserve homepage as page 1; then append selected pages in ranked order.

- [ ] 4.0 Enforce blog/news constraint (at most one if strong signals)

  - [ ] 4.1 Identify `/blog` or `/news` pages.
  - [ ] 4.2 Keep at most one only if "strong signals" (per PRD): contextual score ≥ threshold and/or whitelisted slug hit; otherwise skip.

- [ ] 5.0 Add observability (persist scores, bucket, selection_reason, matched_slugs; log counts and exclusions)

  - [ ] 5.1 For each selected page, persist: `bucket`, `intrinsic_score`, `contextual_score`, `total_score`, `selection_reason`, `matched_slugs`.
  - [ ] 5.2 Log counts: candidates, filtered, threshold-passed, selected, blog/news skipped, service-area hard-exclusions.
  - [ ] 5.3 Ensure JSON output compatibility; document new fields.

- [ ] 6.0 Testing and validation (unit tests, deterministic behavior checks, smoke runs, docs)
  - [ ] 6.1 Unit tests: service-area hard-exclude; whitelist-only top-level selection; tiered boosts affect ordering; tie-breakers determinism.
  - [ ] 6.2 Unit tests: blog/news rule; ensure at most one when strong signals; none otherwise.
  - [ ] 6.3 Integration test: sample `result.links` fixture to validate total pipeline selection and output fields.
  - [ ] 6.4 Determinism test: same inputs produce identical selections across runs.
  - [ ] 6.5 Smoke runs on 3–5 domains; verify Success Metrics (coverage, zero service-area selection, runtime p90).
  - [ ] 6.6 Update README/PRD notes for operators (query override, thresholds, troubleshooting None scores).
