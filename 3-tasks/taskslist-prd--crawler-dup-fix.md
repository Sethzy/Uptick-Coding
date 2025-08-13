## Relevant Files

- `crawler/run_crawl.py` - Orchestrates crawling, config wiring, and page loop.
- `crawler/extraction.py` - Builds page records; will host DOM-scoped extraction hook.
- `crawler/link_selection.py` - Link discovery/selection rules and helpers.
- `crawler/config.json` - Externalized crawler settings; add `content_selectors`, fix `excluded_tags` usage.
- `crawler/report_md.py` - Generates human-friendly reports from JSONL output.
- `crawler/output_writer.py` - JSONL writer utilities.
- `crawler/checkpoint.py` - Resume/idempotency helpers for domain processing.
- `crawler/reachability.py` - Canonicalization and reachability.
- `crawler/session.py` - Stable session IDs.
- `crawler/tests/` - Unit tests for selection, extraction, and output.

### Notes

- Use DOM-scoped extraction (CSS selectors) instead of markdown pruning to preserve page-unique content.
- Ensure `excluded_tags` (e.g., `nav`, `footer`, `script`, `style`) are honored to reduce boilerplate.
- Keep outputs deterministic and small; cap pages per domain as per PRD.

## Tasks

- [ ] 1.0 Wire DOM‑scoped content extraction (no pruning)

  - [ ] 1.1 Remove `PruningContentFilter` from `DefaultMarkdownGenerator` in `crawler/run_crawl.py`
  - [ ] 1.2 Implement `scoped_markdown_from_html(html, selectors)` in `crawler/extraction.py`
  - [ ] 1.3 Emit both `markdown_scoped` (CSS‑selected) and `markdown_raw` (generator) in page records; no fallback logic
  - [ ] 1.4 Recompute `headings`, `text_length`, `detected_keywords`, `evidence_snippets` from `markdown_scoped`
  - [ ] 1.5 Update output schema docstrings/comments to reflect both fields and their intent (scoped vs raw)

- [ ] 2.0 Fix config handling and defaults (`excluded_tags`, add `content_selectors`)

  - [ ] 2.1 In `crawler/config.json`, add `content_selectors` default list: `["main","article","#content",".content",".main",".main-content",".container .content","#primary"]`
  - [ ] 2.2 In `crawler/run_crawl.py`, use `excluded_tags = cfg.get("excluded_tags", ["nav","footer","script","style"])`
  - [ ] 2.3 Thread `content_selectors` from config into the crawl loop for homepage and subpages

- [ ] 3.0 Update crawl loop to inject scoped markdown into page records

  - [ ] 3.1 After `crawler.arun(...)`, read `result.cleaned_html`; compute `scoped_md`
  - [ ] 3.2 Pass `scoped_md` into `make_page_record` and always include `raw_markdown` alongside `markdown_scoped`
  - [ ] 3.3 Apply same flow for each selected subpage
  - [ ] 3.4 Ensure `report_md.py` renders both versions (scoped and raw) for review

- [ ] 4.0 Ensure uniqueness policy and de‑duplication behavior align with PRD

  - [ ] 4.1 Option A: hash by normalized `markdown_scoped` only to drop same‑content duplicates across routes
  - [ ] 4.2 Option B: keep URL+content hash but log duplicates for analysis in report
  - [ ] 4.3 Add a minimum content gate (e.g., `text_length >= 300`) before accepting a page

- [ ] 5.0 Add minimal dependencies and guards (e.g., `bs4`, HTML→MD converter) with fallbacks

  - [ ] 5.1 Ensure `beautifulsoup4` installed; import guarded in `extraction.py`
  - [ ] 5.2 Prefer `markdownify` for HTML→MD; fallback to lightweight converter if unavailable
  - [ ] 5.3 Add try/except around conversion; fallback to generator `raw_markdown` on errors

- [ ] 6.0 Validate on a small golden set and generate the summary report

  - [ ] 6.1 Pick 5–10 domains (include `https://ablefirepro.com/services.html`) and re‑crawl
  - [ ] 6.2 Verify page markdown uniqueness, headings diversity, and reduced boilerplate
  - [ ] 6.3 Regenerate `output.md` via `crawler/report_md.py`; spot‑check diffs
