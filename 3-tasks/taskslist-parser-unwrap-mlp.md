## Relevant Files

- `scoring/models.py` - Content extraction, JSON parsing, status/error mapping; add recursive unwrap + provider error detection.
- `scoring/config.py` - Optional toggle to switch `endpoint_base_url` to DeepSeek direct.
- `scoring/api.py` - Ensure status from model layer is surfaced; no evidence logic remains.
- `tests/test_models.py` - Add tests for nested envelope and provider error content.
- `README`/CLI help - Note strict JSON mode and new statuses.

### Notes

- Keep `response_format: {"type":"json_object"}` and strict JSON-only prompt.
- Add max-depth guard (e.g., 3) to unwrap loop.
- Map provider error payloads to `provider_error` status, not schema errors.

## Tasks

- [ ] 1.0 Implement recursive unwrap with max-depth
- [ ] 2.0 Detect provider error payloads and map to `provider_error`
- [ ] 3.0 Add unit tests for nested envelope and provider error cases
- [ ] 4.0 Optional: Config flag to use DeepSeek direct endpoint
- [ ] 5.0 Light observability: log counts for `invalid_json`, `provider_error`, request latency
- [ ] 6.0 Update docs/CLI help to mention strict JSON mode and statuses
- [ ] 7.0 Run a 3-domain sample and review outputs

