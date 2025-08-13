<!--
/**
 * Purpose: Product-level documentation for the Targeted Domain Crawler feature
 * Description: Explains purpose, architecture, modules, data flow, setup,
 *              usage, and troubleshooting for the crawler implemented under
 *              `crawler/`. Serves as the definitive reference for the feature.
 * Key Sections: Feature Overview; Application Structure; Functionalities
 *               Overview; Technical Implementation; Integration Points;
 *               Development Status; Usage Examples; Troubleshooting Guide
 * AIDEV-NOTE: Keep this document in sync with code edits touching `crawler/*`.
 */
-->

## Feature Overview

The Targeted Domain Crawler discovers and extracts structured content from company websites with a focus on service-related pages (e.g., fire protection services). It prioritizes high-value internal links using deterministic rules and scoring signals, generates normalized page records, and emits machine-readable JSONL along with a human-friendly Markdown summary.

- Business value: Enables rapid enrichment of target accounts with verified website content and key signals (headings, keywords, evidence). Supports batch processing, resumability, politeness, and robots respect.
- Problems solved:
  - Canonical domain resolution and robots gating
  - Deterministic, service-oriented link selection with scoring
  - Lightweight, consistent page normalization and reporting
- Target users: Data/research ops, growth, and engineering teams orchestrating content discovery across large domain sets.

## Application Structure

- Top-level entrypoint: `crawler/run_crawl.py`
- Core modules in `crawler/`:
  - `canonical.py`: canonical URL resolution and robots preflight
  - `checkpoint.py`: file-based idempotent progress tracking
  - `extraction.py`: markdown normalization, headings/keywords, evidence
  - `link_selection.py`: internal link discovery + scoring/bucket selection
  - `logging.py`: structured JSON-line logging helpers
  - `output_writer.py`: atomic JSONL writer utilities
  - `politeness.py`: delays, jitter, and backoff sequences
  - `reachability.py`: CSV domain loading and normalization
  - `report_md.py`: Markdown report generator for run outputs
  - `session.py`: stable session IDs and browser headers
  - `config.json`: runtime config for selection, limits, and behavior
- Tests: `crawler/tests/` covering selection, extraction, IO, reachability

Component hierarchy (orchestration-centric):

- CLI → load config/CSV → for each domain: canonicalize → robots preflight → crawl homepage (Crawl4AI) → select links → crawl subpages → extract records → write JSONL → generate Markdown report.

## Functionalities Overview

- Domain intake: `reachability.load_domains_from_csv` normalizes apex domains, preserving input order and uniqueness.
- Canonical URL probing: `canonical.canonicalize_domain` tries https/www/http fallbacks; `canonical.is_robot_disallowed` provides a conservative preflight check.
- Crawl execution: `run_crawl.main` drives `AsyncWebCrawler` with Playwright-backed rendering, content filtering, and optional link preview scoring.
- Link selection:
  - Pure-HTML anchors via `link_selection.extract_anchors_from_html` with internal-only filtering and disallowed path drops.
  - Deterministic bucket-based ranking via `rank_links_by_priority` + `select_top_links`.
  - Scoring-aware selection via `select_links_with_scoring` using intrinsic/contextual scores, whitelist tiers, and services-intent boosts with deterministic tie-breakers.
- Page extraction: `extraction.make_page_record` standardizes title, language, text length, headings, detected keywords, evidence snippets, markdown, and links.
- Output: `output_writer.open_jsonl` and `write_record` emit atomic JSONL; `report_md.generate_markdown_report` creates a human-readable `output.md` with overview and per-domain details.
- Politeness: `politeness.jitter_delay_seconds` and `backoff_sequence` provide conservative pacing between domains.
- Logging: JSON-structured progress, events, and summaries in `logging.py`.

Data flow highlights:

- CSV domains → canonical URL → homepage crawl result → internal link candidates → selection → subpage crawls → normalization → JSONL + Markdown report.

## Technical Implementation

- Language/runtime: Python 3.12+
- Core libraries:
  - Crawl4AI (AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, LinkPreviewConfig)
  - Playwright (via Crawl4AI)
  - httpx (canonical/robots preflight)
  - BeautifulSoup4 (anchor extraction)
  - python-dotenv (optional env)
- Config: `crawler/config.json`
  - `keywords`: detection terms for evidence
  - `disallowed_paths`: path prefixes to skip (privacy/terms/legal)
  - `link_priority_buckets`: ordered pattern buckets (services/industries/about)
  - `page_cap`: max selected pages per domain
  - `per_domain_delay_seconds`: min/max/jitter politeness settings
  - `global_concurrency`: overall task concurrency (used by caller or flags)
  - `retries`, `page_timeout_ms`, `allow_blog_if_keywords`, `exclude_external_links`, `excluded_tags`, `respect_robots`, `robots_overrides`, `content_filter_threshold`, `sampling_ignore_robots`
- Environment variables (optional):
  - `PROXY_URL`: proxy endpoint for crawler runtime (if used)
  - `LOCALE`: default Accept-Language
  - `INPUT_CSV`, `OUTPUT_JSONL`, `CHECKPOINT`, `FROM_INDEX`, `LIMIT`, `CONCURRENCY`, `DOMAIN_COLUMN`
- Build/deploy: No build step; run directly via Python with Playwright browser installed. See Usage Examples.

## Integration Points

- External: Crawl4AI/Playwright for rendering and link scoring; httpx for reachability; BeautifulSoup for anchor parsing.
- Internal contracts:
  - JSONL schema: one record per domain containing summary fields and a `pages` array of normalized page records.
  - Markdown report: `crawl-runs/<run>/output.md`-style overview and details.
  - Deterministic selection: stable ordering given identical inputs for reproducibility.

## Development Status

- Current: End-to-end orchestration implemented with link preview scoring, deterministic selection, Markdown reporting, and resumable checkpoints.
- Known limitations:
  - Conservative robots preflight; final robots handling delegated to Crawl4AI.
  - Link scoring availability may vary by Crawl4AI build; code falls back to bucket-based selection.
- Planned improvements:
  - Expand selection heuristics for more service taxonomies.
  - Add richer evidence extraction and structured service taxonomy mapping.

## Usage Examples

- Setup (once):

```bash
python -m venv venv && source venv/bin/activate
pip3 install -U crawl4ai httpx beautifulsoup4 python-dotenv
python -m playwright install chromium
```

- Run a batch crawl:

```bash
python crawler/run_crawl.py \
  --input-csv /absolute/path/to/uptick-csvs/final_merged_hubspot_tam_data_resolved.csv \
  --output-jsonl /absolute/path/to/crawl-runs/sample/output.jsonl \
  --checkpoint /absolute/path/to/.crawl-checkpoint.json \
  --from-index 0 --limit 100 --concurrency 4
```

- Dry run to validate input and config:

```bash
python crawler/run_crawl.py --dry-run
```

## Troubleshooting Guide

- DNS_FAIL: Canonical probing could not reach any fallback URL.
  - Check domain validity in CSV and public DNS; verify network/proxy.
- ROBOT_DISALLOW: Preflight indicated robots disallow; domain was skipped.
  - Consider `robots_overrides` in config for approved exceptions.
- TIMEOUT: Homepage crawl did not complete in time.
  - Increase `page_timeout_ms`; verify site availability; reduce concurrency.
- EMPTY_CONTENT: No usable markdown extracted across selected pages.
  - Loosen `content_filter_threshold`; adjust selection thresholds and buckets.
- Poor link selection:
  - Inspect log events `link_selection` and `link_selection_ranked` and adjust `link_priority_buckets`, `selection_score_threshold`, and whitelist terms in `link_selection.py`.

---

### Module-to-Function Map (Quick Reference)

- `run_crawl.py`: CLI orchestration, Crawl4AI configs, selection pipeline, outputs
- `canonical.py`: `canonicalize_domain`, `is_robot_disallowed`
- `checkpoint.py`: `load_checkpoint`, `save_checkpoint`, `mark_attempt`, `mark_success`
- `extraction.py`: `extract_headings_simple`, `detect_keywords`, `build_evidence_snippets`, `make_page_record`
- `link_selection.py`: `filter_internal_links`, `rank_links_by_priority`, `select_top_links`, `extract_anchors_from_html`, `select_links_with_scoring`, `apply_blog_news_rule`
- `logging.py`: `get_logger`, `log_progress`, `log_event`, `log_summary`
- `output_writer.py`: `open_jsonl`, `write_record`
- `politeness.py`: `jitter_delay_seconds`, `backoff_sequence`, `human_like_pause`
- `reachability.py`: `normalize_domain`, `list_unique_preserve_order`, `load_domains_from_csv`
- `report_md.py`: `generate_markdown_report`
- `session.py`: `stable_session_id`, `build_headers`

<!-- AIDEV-NOTE: Update this document alongside non-trivial code changes. -->
