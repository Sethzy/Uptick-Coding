<!--
Purpose: Task list to modify crawler output to use only `markdown_fit` for LLM scoring.
Description: High-level parent tasks to trim page-level artifacts to `markdown_fit` (+fallback), update schema, tests, and docs.
Key Sections: Relevant Files, Notes, Tasks.
AIDEV-NOTE: Parent tasks only; reply "Go" to expand into detailed sub-tasks per generate-tasks-from-prd.md.
-->

## Relevant Files

- `crawler/run_crawl.py` - Orchestration; controls what page fields are written to JSONL.
- `crawler/extraction.py` - Builds page records; will enforce `markdown_fit` preference and fallback.
- `crawler/output_writer.py` - Writer stays the same; schema references updated.
- `crawler/config.json` - Optionally add a toggle to include/exclude raw artifacts.
- `crawler/tests/` - Update tests to reflect new page schema (no `markdown_raw` or `cleaned_html`).
- `3-tasks/2.crawler-scope/taskslist-prd-targeted-domain-crawler.md` - Link back to primary PRD task list (context).

### Notes

- Goal: Minimize payload for LLM scoring while retaining structure. Use `markdown_fit` only; fallback to `markdown_raw` if `markdown_fit` is empty.
- Consider keeping `links` for transparency/debugging, but remove `cleaned_html` by default.
- Provide a config flag to re-enable full artifacts for audits if needed.

## Tasks

- [ ] 1.0 Switch output to `markdown_fit` only (primary)
- [ ] 2.0 Remove `markdown_raw` and `cleaned_html` from page records by default
- [ ] 3.0 Add fallback: if `markdown_fit` empty, use `markdown_raw` (compat path)
- [ ] 4.0 Make inclusion of raw artifacts configurable (audit mode)
- [ ] 5.0 Update unit tests and fixtures to the trimmed schema
- [ ] 6.0 Update docs and usage notes to recommend `markdown_fit` for LLMs

<!-- AIDEV-NOTE: Say "Go" to expand each parent task into actionable sub-tasks. -->

- [ ] 6.7 Add “sampling mode” toggle to globally ignore robots for small internal runs; log `crawler_status=OK` with `crawler_reason=OVERRIDE_ROBOTS`, enforce stricter politeness (longer delays, lower concurrency), and capture an audit flag in output.

- [ ] 7.0 Minimal render robustness (no overengineering)
  - [ ] 7.1 Wait-for content selector before extraction: try `main`, `article`, `[role=main]` with max 2s wait and ±250ms jitter.
  - [ ] 7.2 Scroll-to-bottom in 2–4 steps with 150–600ms pauses and small randomness; then extract.
  - [ ] 7.3 Add micro-jitter (±10–20%) to existing per-page delays; keep per-domain concurrency = 1.
  - [ ] 7.4 Log simple flags per page: `waited_for_selector`, `scrolled`, `jitter_ms` to aid auditing.
