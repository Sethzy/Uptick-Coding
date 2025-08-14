<!--
/**
 * Purpose: High-level implementation task list for the LLM Scoring Pipeline PRD.
 * Description: Parent tasks only (no sub-tasks yet) per `.claude/commands/3a-backend-phase/generate-tasks-from-prd.md`.
 * Key Tasks: Scaffolding; LLM classify w/ strict JSON; evidence validation; outputs (JSONL/CSV); CLI & Python API; retries/logging.
 */
-->

## Relevant Files

- `scoring/__init__.py` - Package init for the scoring module.
- `scoring/cli.py` - CLI entrypoint for `scorer classify` command.
- `scoring/config.py` - Load and validate YAML/JSON config (thresholds, evidence count, model, temperature).
- `scoring/models.py` - Model invocation wrapper (Qwen3 30B A3B via OpenRouter) with strict JSON enforcement and repair.
- `scoring/schema.py` - Typed schemas for request/response, JSONL/CSV output mapping, and validation helpers.
- `scoring/evidence.py` - Evidence validation (URL must exist in headers; snippet sourced from aggregated text; trimming/dedup).
- `scoring/io_jsonl.py` - JSONL writer (one object per domain) and raw payload persistence.
- `scoring/io_csv.py` - CSV writer (flat columns for category, confidence, evidence, metadata).
- `scoring/run.py` - Orchestration: read input JSONL, classify domains, handle retries/backoff, and logging.
- `scoring/logging.py` - Structured logging utilities (run_id, model, prompt_version, token counts, request_ms).
- `scoring/api.py` - Python API surface: `score_domain()`, `score_file()`.
- `tests/test_models.py` - Unit tests for strict JSON parsing and single repair flow.
- `tests/test_evidence.py` - Unit tests for evidence URL/snippet validation and trimming.
- `tests/test_io.py` - Unit tests for JSONL/CSV schemas and writers.
- `tests/test_cli.py` - CLI smoke tests for required flags and end-to-end output shape.

### Notes

- Unit tests live next to implementation where practical.
- Run tests with `pytest` or project default.
- Use deterministic logs and stable output schemas for easy diffing.
- Aggregated input is provided upstream by the Aggregated Context Builder PRD.

## Tasks

- [x] ~~_1.0 Project scaffolding and configuration_~~ [2025-08-14]

  - [x] ~~_1.1 Create `scoring/` package skeleton and `__init__.py`_~~ [2025-08-14]
  - [x] ~~_1.2 Implement `scoring/config.py` with dataclass: `model`, `temperature`, `thresholds` (A,B), `max_evidence`, `timeout_s`, `max_tokens`, `worker_count`, `retry` (max_attempts, backoff)_~~ [2025-08-14]
  - [x] ~~_1.3 Add config loader from YAML/JSON and environment overrides_~~ [2025-08-14]
  - [x] ~~_1.4 Define constants for default prompt version `v1`_~~ [2025-08-14]
  - [x] ~~_1.5 Add minimal `requirements.txt` if needed (http client, pydantic/dataclasses-json, click/argparse)_~~ [2025-08-14]

- [x] ~~_2.0 LLM classification with strict JSON schema and single repair attempt_~~ [2025-08-14]

  - [x] ~~_2.1 Define response schema in `scoring/schema.py` with types: `classification_category`, `confidence`, `rationale`, `evidence[]`_~~ [2025-08-14]
  - [x] ~~_2.2 Implement `scoring/models.py` for Qwen3 30B A3B calls via OpenRouter (temperature 0, bounded max_tokens)_~~ [2025-08-14]
  - [x] ~~_2.3 Enforce "JSON only" output; parse and validate strictly; capture raw text payload_~~ [2025-08-14]
  - [x] ~~_2.4 On parse/validation failure, perform exactly one repair re-prompt; if still invalid, return error record_~~ [2025-08-14]
  - [x] ~~_2.5 Unit tests in `tests/test_models.py` for valid JSON path and repair path_~~ [2025-08-14]

- [ ] 3.0 Evidence validation and discipline (URL membership, snippet sourcing, trimming, dedup)

  - [ ] 3.1 Implement header URL extraction from `aggregated_context` using regex for lines `^### \[PAGE\] (\S+)`
  - [ ] 3.2 Validate each evidence `url` exists in extracted header set
  - [ ] 3.3 Validate each `snippet` is a verbatim substring of `aggregated_context`
  - [ ] 3.4 Trim snippets to ~320 chars at sentence boundaries when possible
  - [ ] 3.5 Deduplicate evidence items and enforce 1–3 items; require at least 1 valid item
  - [ ] 3.6 On validation failure, trigger one repair prompt; otherwise emit explicit error in output
  - [ ] 3.7 Unit tests in `tests/test_evidence.py` for membership, substring, trimming, and failure cases

- [ ] 4.0 Output layers: JSONL object writer and CSV flattening with metadata

  - [ ] 4.1 Implement `scoring/io_jsonl.py` to append one JSON object per domain; deterministic field ordering
  - [ ] 4.2 Persist raw LLM payloads alongside parsed outputs for audit (e.g., `out_raw.jsonl`)
  - [ ] 4.3 Implement `scoring/io_csv.py` flattening: domain, category, confidence, rationale, evidence_url_1..3, evidence_snippet_1..3, model/prompt/run_id
  - [ ] 4.4 Unit tests in `tests/test_io.py` for schema mapping and quoting/escaping

- [ ] 5.0 CLI (`scorer classify`) and Python API (`score_domain`, `score_file`) interfaces

  - [ ] 5.1 Implement `scoring/cli.py` with flags: `--input`, `--output-jsonl`, `--output-csv`, `--model`, `--threshold-a`, `--threshold-b`, `--max-evidence`, `--prompt-version`, `--config`
  - [ ] 5.2 Wire CLI to orchestrator in `scoring/run.py`
  - [ ] 5.3 Implement `scoring/api.py` with `score_domain(...)` and `score_file(...)`
  - [ ] 5.4 Add `tests/test_cli.py` smoke test to run a tiny input and assert output headers

- [ ] 6.0 Error handling and retries with jittered backoff; per-request timeouts

  - [ ] 6.1 Implement retry policy: retry on 5xx/429/network/timeout; respect Retry-After; jittered exponential backoff
  - [ ] 6.2 Do not retry on 4xx auth/validation errors
  - [ ] 6.3 Add per-request timeout and per-domain attempt cap; emit categorized errors

- [ ] 7.0 Structured logging (run_id, model/prompt versions, token counts, request_ms, status)

  - [ ] 7.1 Implement `scoring/logging.py` utilities for structured log lines
  - [ ] 7.2 Log per-call metadata: model, prompt_version, run_id, request_ms, token_counts, status/error
  - [ ] 7.3 Ensure logs are deterministic and grep-friendly

- [ ] 8.0 Minimal concurrency controls and checkpointed resume (optional small worker pool)

  - [ ] 8.1 Add worker pool (3–5) with bounded concurrency and simple rate limiting
  - [ ] 8.2 Maintain processed set and skip completed domains on rerun
  - [ ] 8.3 Write periodic checkpoints to allow resume after interruption

- [ ] 9.0 Operational checks: JSON parse failure rate and evidence-present rate surfaced in logs
  - [ ] 9.1 Track counters for parse failures and valid-evidence presence
  - [ ] 9.2 Emit end-of-run summary log with rates and counts

This includes parent tasks with detailed sub-tasks. If you want me to expand any section into implementation guidance or code stubs, say "Expand 2.x" (or the section number).
