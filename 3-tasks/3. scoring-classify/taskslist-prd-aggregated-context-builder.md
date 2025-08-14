<!--
/**
 * Purpose: High-level implementation task list for the Aggregated Context Builder PRD.
 * Description: Parent tasks only (no sub-tasks yet) per `.claude/commands/3a-backend-phase/generate-tasks-from-prd.md`.
 * Key Tasks: Deterministic ordering; headers/separation; content selection; normalization; dedup; truncation/overflow; audit fields.
 */
-->

## Relevant Files

- `aggregator/__init__.py` - Package init for the aggregator module.
- `aggregator/config.py` - Config for max tokens/chars and route preferences.
- `aggregator/ordering.py` - Deterministic ordering rules and helpers.
- `aggregator/normalize.py` - Whitespace collapse, simple boilerplate stripping, newline normalization.
- `aggregator/build.py` - Main builder to emit `aggregated_context`, `included_urls`, `overflow`, and `length`.
- `aggregator/token_estimator.py` - Approximate token estimation utility.
- `aggregator/io.py` - Read crawl artifacts, write JSONL outputs for the scorer.
- `tests/test_build.py` - Unit tests for output format, determinism, and overflow behavior.
- `tests/test_normalize.py` - Unit tests for normalization/dedup behavior.

### Notes

- Keep output byte-identical for same input/config.
- No Top‑N heuristics; truncate at page boundaries and set `overflow=true`.
- Ensure exact header and separation rules for downstream citation validation.

## Tasks

- [ ] 1.0 Project scaffolding and configuration (max size, encoding, newline rules)

  - [ ] 1.1 Create `aggregator/` package skeleton and `__init__.py`
  - [ ] 1.2 Implement `aggregator/config.py` with dataclass: `max_tokens` (or `max_chars`), `newline` policy, `encoding`
  - [ ] 1.3 Provide defaults aligned with PRD (e.g., ~8k token equivalent)

- [ ] 2.0 Deterministic page ordering and section header/separation implementation

  - [ ] 2.1 Implement `ordering.by_priority_then_path()` per PRD; homepage first; then deterministic remainder (path length asc, URL asc)
  - [ ] 2.2 Implement header emission: exactly `### [PAGE] <url>` on its own line
  - [ ] 2.3 Ensure exactly two blank lines between page sections

- [ ] 3.0 Content selection per page (`markdown_scoped` for homepage; `markdown_fit` for subpages)

  - [ ] 3.1 Implement selection with strict preference rules and skip empty pages
  - [ ] 3.2 Add unit tests to verify selection across mixed availability

- [ ] 4.0 Normalization and deduplication pipeline

  - [ ] 4.1 Collapse repeated whitespace; normalize newlines to `\n`; enforce UTF-8
  - [ ] 4.2 Strip link targets and simple boilerplate (nav/footers, cookie banners) when easily identifiable
  - [ ] 4.3 Deduplicate pages post-normalization; keep first occurrence
  - [ ] 4.4 Unit tests for normalization and dedup edge cases

- [ ] 5.0 Token/size budgeting with truncation at page boundaries and `overflow` flag

  - [ ] 5.1 Implement `token_estimator.estimate()` (simple chars/4 approximation acceptable)
  - [ ] 5.2 Maintain cumulative count; before adding a page, check budget; if would exceed, stop and set `overflow=true`
  - [ ] 5.3 Ensure truncation never splits within a page; only at boundaries

- [ ] 6.0 Emit audit fields: `included_urls`, `length` (chars, approx_tokens)

  - [ ] 6.1 Collect URLs in final included order
  - [ ] 6.2 Compute `length` object with chars and approx tokens
  - [ ] 6.3 Deterministic serialization

- [ ] 7.0 JSONL output writer for scorer consumption

  - [ ] 7.1 Implement `aggregator/io.py` to read crawl artifacts and write scorer-ready JSONL
  - [ ] 7.2 Validate header/separation rules in output

- [ ] 8.0 Determinism tests and snapshot tests for sample domains
  - [ ] 8.1 Provide 3–5 sample crawl inputs; snapshot expected JSONL outputs
  - [ ] 8.2 Add test that same inputs/config produce byte-identical outputs

This includes parent tasks with detailed sub-tasks. If you want me to expand any section into implementation guidance or code stubs, say "Expand A.x" (or the section number).
