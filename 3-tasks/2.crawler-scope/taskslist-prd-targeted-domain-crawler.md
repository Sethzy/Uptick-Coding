<!--
Purpose: Task list derived from PRD to implement a targeted domain crawler using Crawl4AI.
Description: High-level parent tasks with detailed sub-tasks, aligned with `prd-targeted-domain-crawler.md` and `generate-tasks-from-prd.md`.
Key Sections: Relevant Files, Notes, Tasks.
AIDEV-NOTE: Sub-tasks added after user confirmation per process.
-->

## Relevant Files

- `crawler/run_crawl.py` - Main entrypoint CLI to orchestrate crawling domains per PRD flow.
- `crawler/config.json` - Externalized configuration (keywords, disallowed paths, page caps, concurrency, politeness).
- `crawler/reachability.py` - Canonical URL resolution, scheme/host fallbacks, WAF-aware session setup.
- `crawler/link_selection.py` - Homepage link discovery and priority-first selection (services → industries → about...).
- `crawler/extraction.py` - Markdown generation, cleaned HTML capture, headings/keywords detection, evidence snippet builder.
- `crawler/output_writer.py` - JSONL writer implementing domain/page output schema and checkpoints.
- `crawler/politeness.py` - Robots handling, per-domain pacing, retries with backoff, timeouts.
- `crawler/checkpoint.py` - Idempotent resume and attempt bookkeeping.
- `crawler/logging.py` - Structured progress logs and end-of-run summary.
- `tests/golden_set/` - Golden set fixtures and validation scripts for acceptance criteria.
- `crawler/tests/test_reachability.py` - Unit tests for canonicalization and reachability.
- `crawler/tests/test_link_selection.py` - Unit tests for link discovery/priority selection.
- `crawler/tests/test_extraction.py` - Unit tests for headings/keywords/snippet extraction.
- `crawler/tests/test_output_writer.py` - Unit tests for JSONL schema serialization.

### Notes

- Unit tests should live alongside modules (e.g., `crawler/tests/test_link_selection.py`).
- Use `pip3` for Python dependencies and Playwright installation per Crawl4AI quickstart.
- Configure Playwright browsers once at setup to avoid repeated downloads.

## Tasks

- [ ] 1.0 Environment and configuration setup

  - [x] 1.1 Create Python virtual environment; install `crawl4ai`, `playwright`, and run `playwright install chromium` (via `pip3`).
  - [x] 1.2 Create `crawler/config.json` with: keywords, disallowed paths, link-priority buckets, page cap (4), per-domain delay (1.5–2.0s + jitter), global concurrency, retries (2), page timeout (20–30s).
  - [x] 1.3 Implement `crawler/logging.py` for structured logs (domain, status, reason, attempts, elapsed).
  - [x] 1.4 Add `.env` support for optional proxy and locale; read in `run_crawl.py`.
  - [x] 1.5 Document setup in README snippet inside this tasks file and `run_crawl.py` module docstring.

- [ ] 2.0 Input processing and canonicalization (reachability + WAF-aware session)
  - [x] 2.1 Implement CSV loader to read `tam_site` from `final_merged_hubspot_tam_data_resolved.csv`; normalize domains; filter empty/invalid.
  - [x] 2.2 Implement `canonicalize_domain(root)` producing `https://root → https://www.root → http://root → http://www.root` fallback order with reachability checks and timeouts.
  - [x] 2.3 Implement `stable_session_id(domain)` and per-domain UA + coherent headers; persist across that domain’s pages.
  - [x] 2.4 Preflight `robots.txt` via `check_robots_txt=True`; set `crawler_status` and `crawler_reason` if disallowed.
  - [x] 2.5 Persist domain-level bookkeeping: `canonical_url`, `crawler_status` (OK|FAIL|RETRY|SKIPPED), `crawler_reason`.
  - [ ] 2.6 Add unit tests in `crawler/tests/test_reachability.py` for fallback order and malformed domain handling.

- [ ] 3.0 Targeted crawl policy and link selection (homepage + up to 4 high-signal pages)
  - [x] 3.1 Use `AsyncWebCrawler` + `CrawlerRunConfig` as specified (BYPASS cache, robots on, exclude external links, process iframes, remove overlays).
  - [x] 3.2 Implement homepage internal link extraction; filter low-signal paths (`/privacy`, `/terms`, `/cookie`, `/legal`, `/sso`, heavy query trackers).
  - [x] 3.3 Rank links by priority buckets: Services/Capabilities → Industries/Markets → About/Company → Certifications/Associations → Projects/Case Studies → Careers/Team/Numbers → Contact/Locations.
  - [x] 3.4 Select top unique pages across buckets until cap=4; ensure deterministic ordering (stable sort + tiebreakers).
  - [ ] 3.5 Allow at most one blog/news page only if strong keywords detected; otherwise skip.
  - [ ] 3.6 Add unit tests in `crawler/tests/test_link_selection.py` with synthetic link sets covering ties, exclusions, and caps.

- [ ] 4.0 Content extraction and evidence generation (markdown, cleaned HTML, snippets)
  - [x] 4.1 Configure `DefaultMarkdownGenerator(PruningContentFilter(threshold≈0.25, threshold_type="dynamic", min_word_threshold=10))` with markdown options per PRD.
  - [x] 4.2 For each page, capture: `title`, `url`, `language`, `render_mode="browser"`, `cleaned_html`, `markdown.raw`, `markdown.fit`, `links`.
  - [x] 4.3 Extract H1–H3 headings; compute `text_length` from markdown; handle empty/low-density content per threshold.
  - [x] 4.4 Implement keyword detection; generate 200–300 char evidence snippets centered on first match(es); limit count per page.
  - [x] 4.5 De-duplicate near-identical pages using normalized text hash to avoid wasting page budget.
  - [ ] 4.6 Add unit tests in `crawler/tests/test_extraction.py` for headings parsing and snippet windowing.

- [ ] 5.0 Output serialization to JSONL (domain/page schema compliance)
  - [x] 5.1 Implement `crawler/output_writer.py` to emit one NDJSON record per domain with fields: `domain`, `canonical_url`, `crawler_status`, `crawler_reason`, `crawl_pages_visited`, `crawl_ts`, `pages` array.
  - [x] 5.2 Ensure page objects include: `url`, `title`, `language`, `render_mode`, `text_length`, `headings`, `detected_keywords`, `evidence_snippets`; include optional `markdown_raw`, `markdown_fit`, `cleaned_html`, `links`.
  - [x] 5.3 Write atomically (temp file → move) and support append mode; flush regularly for long runs.
  - [x] 5.4 Maintain optional input row index mapping for reconciliation.
  - [ ] 5.5 Add unit tests in `crawler/tests/test_output_writer.py` to validate schema and ordering.

- [ ] 6.0 Reliability controls (robots, politeness, retries, timeouts, idempotent resume)
  - [x] 6.1 Respect robots: `check_robots_txt=True`; set disallow reasons; skip pages when required.
  - [x] 6.2 Implement per-domain rate limiting with jittered 1.5–2.0s delay; enforce per-domain concurrency=1; expose global concurrency in config.
  - [x] 6.3 Implement retries (up to 2) on transient errors (DNS, 429/5xx) with exponential backoff; record attempts and final reason.
  - [x] 6.4 Enforce page timeout (20–30s) including render; abort page on repeated low-density content.
  - [x] 6.5 Implement checkpointing: persist processed domains and attempts; skip already-successful on rerun.
  - [ ] 6.6 Smoke test resume behavior by interrupting and rerunning on a small set.

- [ ] 7.0 Operations, logging, and QA (CLI runner, progress/summary, golden-set validation)
  - [x] 7.1 Implement CLI flags in `run_crawl.py`: `--input-csv`, `--output-jsonl`, `--concurrency`, `--from-index`, `--limit`, `--resume`, `--dry-run`.
  - [x] 7.2 Add progress logs every N domains; aggregate failure reasons; print end-of-run summary (OK/FAIL/RETRY counts).
  - [ ] 7.3 Create a ~30-domain golden set; validate success metrics and acceptance criteria from PRD.
  - [ ] 7.4 Provide a lightweight README section in this file with example command and expected NDJSON shape.
  - [ ] 7.5 Add an integration smoke test that crawls 3–5 known domains and validates core fields are populated.

<!-- AIDEV-NOTE: High-level tasks expanded with actionable sub-tasks per PRD. -->
