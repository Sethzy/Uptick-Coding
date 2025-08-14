## Relevant Files

- `scoring/schema.py` - Core output schema; remove evidence fields and adjust validators/schema snippet.
- `scoring/api.py` - Classification orchestration and CSV flattening; drop evidence validation and evidence CSV fields; add status/error to CSV.
- `scoring/models.py` - Prompt builder and HTTP request; add DeepSeek `response_format: {"type":"json_object"}`, tighten prompt, set `max_tokens`, handle empty content.
- `scoring/io_csv.py` - CSV writer/flatten helpers; remove evidence columns.
- `scoring/io_jsonl.py` - JSONL writer (no functional change, verify fields written).
- `scoring/logging.py` - Ensure status/error logging remains intact; optionally add basic run metrics.
- `scoring/config.py` - Expose `max_tokens`, model name, and concurrency controls.
- `tests/test_io.py` - Update tests for new CSV headers without evidence columns.
- `tests/test_models.py` - Update/expand tests for JSON parsing with envelopes and JSON mode.
- `tests/test_cli.py` - Smoke tests for end-to-end run with new schema/CSV.
- `tests/test_evidence.py` - Remove or replace (no longer applicable after evidence removal).
- `scoring previewer/classifications-previewer.html` - If used, update to not assume evidence columns.

### Notes

- Keep retries/backoff and concurrency controls unchanged functionally; tune only if needed.
- Cite DeepSeek JSON Output guidance when documenting changes: `https://api-docs.deepseek.com/guides/json_mode`.

## Tasks

- [ ] 1.0 Remove evidence fields from schema and outputs

  - [ ] 1.1 Update `scoring/schema.py` to remove `EvidenceItem` and the `evidence` field; retain `classification_category`, `confidence`, `rationale`, and optional “Other” fields with existing validators.
  - [ ] 1.2 Update `get_model_classification_json_schema()` to only include the kept fields (no evidence entries).
  - [ ] 1.3 In `scoring/api.py`, remove calls to evidence validation and related error statuses; adjust result building to never expect `evidence`.
  - [ ] 1.4 Update CSV shaping: modify `_flatten_for_csv` in `scoring/api.py` and any helpers in `scoring/io_csv.py` to drop `evidence_url_*` and `evidence_snippet_*`; add `status` and `error` columns if missing.
  - [ ] 1.5 Search/remove any remaining imports/usages of `scoring/evidence.py`; deprecate file or leave with an `AIDEV-NOTE` stating it’s unused.
  - [ ] 1.6 Update previewers (if used) to not rely on evidence columns: `scoring previewer/classifications-previewer.html`.
  - [ ] 1.7 Adjust tests: delete or rewrite `tests/test_evidence.py`; update `tests/test_io.py`, `tests/test_models.py`, and `tests/test_cli.py` to reflect the new schema/CSV headers.
  - [ ] 1.8 Update any docs mentioning evidence output to reflect removal.

- [ ] 2.0 Enable strict JSON output mode and tighten prompt (DeepSeek JSON Output)
  - [ ] 2.1 In `scoring/models.py`, pass `response_format: {"type":"json_object"}` to the chat completion request.
  - [ ] 2.2 Update `_build_prompt` to: (a) state “Output only a JSON object (json)” and (b) require exactly `classification_category`, `confidence`, `rationale` (and the two “Other” fields when applicable). Include a minimal JSON example.
  - [ ] 2.3 Ensure `max_tokens` is configurable and sufficiently high via `scoring/config.py`.
  - [ ] 2.4 Handle empty content responses in JSON mode by retrying once or twice with short backoff.
  - [ ] 2.5 Keep and verify envelope unwrapping and markdown-fence stripping in the parser as a fallback.
  - [ ] 2.6 Add light observability: compute/log invalid_json rate, avg latency, and token counts post-run (can be printed or appended to a summary log).
  - [ ] 2.7 Update CLI help text and any README/notes to mention strict JSON mode and removed evidence outputs.
  - [ ] 2.8 Add/adjust a minimal e2e smoke test that asserts: valid JSON is produced, CSV contains `status` and `error`, and no evidence columns exist.
