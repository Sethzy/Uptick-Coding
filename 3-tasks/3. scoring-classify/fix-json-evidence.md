## PRD: Remove Evidence Fields and Enforce Strict JSON Output

### 1) Introduction / Overview

This PRD proposes simplifying the scoring output by removing evidence URLs/snippets and making the model output strict, clean JSON. This reduces validation failures (invalid_json) and eases downstream review. We will enable DeepSeek’s JSON Output mode and keep resilient parsing (unwrap envelopes, strip markdown fences) as a fallback. Reference: [DeepSeek JSON Output docs](https://api-docs.deepseek.com/guides/json_mode).

### 2) Goals

- Reduce invalid_json failures by enforcing strict JSON output (DeepSeek JSON mode) and resilient parsing.
- Simplify schema and CSV by removing evidence fields entirely.
- Preserve core fields only: `classification_category`, `confidence`, `rationale` (+ optional “Other” sublabel fields).
- Maintain robust retries/backoff and sensible concurrency.
- Provide light observability: invalid_json rate, latency, tokens.

### 3) User Stories

- As an operator, I want runs to complete with few format errors so I can trust the outputs without manual fixing.
- As a developer, I want a smaller schema without evidence to reduce parsing/validation complexity.
- As an analyst, I want CSV rows to clearly show success/failure via `status` and `error` so triage is quick.

### 4) Functional Requirements

1. Evidence removal

   - Remove evidence URL and snippet requirements from the schema and outputs.
   - Stop writing evidence columns to CSV; keep only core fields plus `status` and `error`.

2. Strict JSON output with DeepSeek

   - Pass `response_format: { type: 'json_object' }` in requests to DeepSeek.
   - Ensure the prompt states: “Output only a JSON object with exactly: `classification_category`, `confidence`, `rationale`.”
   - If `classification_category == "Other"`, include `other_sublabel` (3–6 words) and `other_sublabel_definition` (2–3 sentences).
   - Provide a minimal example JSON in the prompt.
   - Set `max_tokens` high enough to avoid truncation.
   - Known caveat: JSON mode may return empty content; implement one or two quick retries with short backoff when content is empty. Source: [DeepSeek JSON Output docs](https://api-docs.deepseek.com/guides/json_mode).

3. Resilient parsing (fallbacks)

   - Keep envelope unwrapping (choices[0].message.content), markdown fence stripping, and first-object extraction as a fallback if JSON mode is ignored or a proxy wraps responses.

4. CSV output

   - Include `status` and `error` columns in CSV for diagnosability.
   - Remove evidence-related columns from CSV headers and rows.

5. Reliability controls

   - Preserve retry/backoff for timeouts/429/5xx with jittered delays.
   - Keep worker concurrency configurable to respect provider limits.

6. Observability
   - Report basic run metrics: invalid_json rate, average latency, and token usage.
   - Log model name, prompt version, and run_id for auditability.

### 5) Non-Goals (Out of Scope)

- Reintroducing or validating evidence URLs/snippets.
- Modifying the crawler or aggregated context generation.
- Changing business classification categories or core decision logic.

### 6) Design Considerations

- Enabling DeepSeek JSON mode should materially reduce format errors, but keep parser fallbacks because routers/providers may still envelope responses or ignore `response_format`.
- Keep schema minimal to reduce failure surface.
- Keep `status`/`error` visible to non-engineers via CSV.

### 7) Technical Considerations

- Request layer: add `response_format` and tune `max_tokens`; keep retries/backoff and concurrency controls.
- Prompt: update to emphasize “JSON only” with the exact fields required; include a minimal example object.
- Parsing: maintain envelope unwrap + fence stripping + object extraction as last resort.
- Outputs: update CSV flattening to drop evidence columns; ensure `status` and `error` are present.
- Configurability: keep model and concurrency as config-driven; allow toggling prompt version.

### 8) Success Metrics

- invalid_json rate ≤ 2% on the disco-won-lost sample run.
- Zero failures caused by missing evidence fields (since removed).
- CSV fully consumable without manual review for ≥ 98% rows.
- Median request latency unchanged (±10%) versus baseline.

### 9) Open Questions

- Do we keep the “Other” sublabel fields, or simplify to category+confidence+rationale only?
- Should we completely remove evidence columns from historical CSVs or keep them empty for schema continuity?
- Any provider-specific limits on `max_tokens` that we should guard against for larger rationales?

### Appendix: JSON Mode Example (DeepSeek)

Reference: [DeepSeek JSON Output docs](https://api-docs.deepseek.com/guides/json_mode)

Example input (Python):

```python
import json
from openai import OpenAI

client = OpenAI(
    api_key="<your api key>",
    base_url="https://api.deepseek.com",
)

system_prompt = """
The user will provide some exam text. Please parse the "question" and "answer" and output them in JSON format.

EXAMPLE INPUT:
Which is the highest mountain in the world? Mount Everest.

EXAMPLE JSON OUTPUT:
{
    "question": "Which is the highest mountain in the world?",
    "answer": "Mount Everest"
}
"""

user_prompt = "Which is the longest river in the world? The Nile River."

messages = [{"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}]

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=messages,
    response_format={
        'type': 'json_object'
    }
)

print(json.loads(response.choices[0].message.content))
```

Expected output:

```json
{
  "question": "Which is the longest river in the world?",
  "answer": "The Nile River"
}
```
