## PRD: Robust Evidence Normalization and JSON Extraction for Scoring Pipeline

### 1. Introduction / Overview

The scoring pipeline sometimes flags results as invalid for two main reasons:

- Evidence validation rejects URLs that are trivially different (http vs https, with/without `www`, trailing slash) or snippets that are verbatim in meaning but differ in whitespace/quotes/entities.
- JSON parsing fails when providers wrap responses in envelopes or return content in alternate fields.

Goal: Make runs “just work” smoothly with minimal and safe changes, keeping the system strict but practical.

### 2. Goals

1. Reduce `invalid_evidence` rate to < 5% on the provided sample set without relaxing core rules.
2. Reduce `invalid_json` or `schema_validation_error` to < 2% via better JSON extraction.
3. Maintain current classification categories and overall scoring logic.
4. Avoid noticeable performance regressions.

### 3. User Stories

- As an operator, I want classification runs to complete with high validity so I don’t need to manually re-run or fix many failures.
- As a developer, I want clear, consistent validation rules so I can reason about why an evidence item is accepted or rejected.
- As a stakeholder, I want minimal scope changes that improve reliability without introducing new ambiguity.

### 4. Functional Requirements

1. Evidence URL normalization (membership check against headers)

   - Normalize before comparison:
     - Lowercase host.
     - Strip leading `www.` from host.
     - Treat `http://` and `https://` as equivalent for membership.
     - Normalize trailing slash so `/path` and `/path/` are equivalent.
   - Preserve path and query; do not drop query or fragment in v1 to avoid mismatches across different pages.
   - Apply the normalization to both header URLs and evidence URLs within the validator.

2. Evidence snippet normalization (verbatim check)

   - Keep the “must be verbatim substring” rule, but compare in a normalized space:
     - Collapse runs of whitespace to a single space.
     - Normalize quotes/dashes (smart ↔ straight) and common HTML entities (e.g., `&amp;` → `&`).
     - Case-insensitive match.
   - If the normalized match passes, store the original snippet in outputs but trim it to `<= 320` chars on a natural boundary as today.

3. Evidence deduplication and limits

   - Keep current cap of 3 items and dedup semantics unchanged.

4. JSON extraction hardening

   - When parsing provider responses, search for model content in this order:
     - OpenAI/OpenRouter envelope: `choices[0].message.content` (string) or list-of-parts with `text` fields.
     - Alternate common fields: `output_text`, `response`, `output`.
     - If none found, fall back to the raw text.
   - Retain one repair attempt if schema parsing fails, as currently implemented.

5. Retry/backoff
   - Keep current strategy; allow configuration to increase attempts to 3 via config without changing defaults in this PRD.

### 5. Non-Goals (Out of Scope)

- No fuzzy similarity scoring for snippets (e.g., no 85% similarity threshold) in this iteration.
- No changes to classification categories, confidence semantics, or prompt structure beyond updating the schema snippet text if needed for clarity.
- No provider/model switching or multi-model routing.

### 6. Design Considerations

- Location of changes:
  - `scoring/evidence.py`: implement URL and snippet normalization helpers and use them in `validate_and_normalize_evidence`.
  - `scoring/models.py`: extend `_extract_content_text` to probe additional envelope fields safely.
- Determinism: Normalization must be deterministic and easily testable.
- Safety: Do not broaden URL equivalence beyond scheme/`www`/trailing-slash to avoid cross-page mismatches.
- Performance: Normalized substring checks are O(n); acceptable on current aggregated context sizes.

### 7. Technical Details (Proposed Approach)

- URL normalization rules:
  - Parse via `urllib.parse.urlsplit`.
  - Transform host: lowercase; strip leading `www.`
  - Normalize scheme to `https` for comparison; ignore scheme differences.
  - Normalize path: remove a single trailing slash unless path is just `/`.
  - Include query and fragment as-is in comparison (no changes).
- Snippet normalization rules:
  - For both aggregated context and candidate snippet: HTML-unescape, normalize unicode punctuation to ASCII equivalents, collapse whitespace to single spaces, lowercase.
  - Perform `in` check on normalized strings; if true, accept the original snippet (trimmed) for output.
- JSON extraction:
  - Extend `_extract_content_text` with additional checks for `output_text`, `response`, and `output` if `choices` path is absent/empty.
  - Keep existing markdown fence stripping and single repair pass.

### 8. Acceptance Criteria

- On the 10-sample confirmation data:
  - `invalid_evidence` < 5%.
  - `invalid_json` < 2%.
  - No new categories or confidence computation behavior introduced.
- Unit tests cover:
  - URL normalization cases (scheme, `www`, trailing slash, path equality, query retained).
  - Snippet normalization (whitespace, quotes/dashes, HTML entities, case-insensitive).
  - JSON envelope extraction paths including list-of-parts content.

### 9. Rollout Plan

1. Implement helpers and replace checks in-place.
2. Add unit tests for normalization and JSON extraction edge cases.
3. Run on the `cts-single` data and 10-sample confirmation set; validate acceptance criteria.
4. If metrics pass, merge. If not, review logs and adjust normalization selectively (without introducing fuzzy matching).

### 10. Alternatives and Trade-offs

- Option A (Chosen): Strict-but-normalized evidence + hardened JSON extraction

  - Pros: Minimal scope, predictable behavior, addresses majority of current failures.
  - Cons: Still rejects paraphrased snippets and URLs differing beyond simple variants.

- Option B: Add fuzzy snippet matching (e.g., RapidFuzz ≥ 85%)

  - Pros: Higher acceptance rate when minor edits or rendering changes occur.
  - Cons: Risk of false positives; harder to audit; increased CPU.

- Option C: Broaden URL equivalence (ignore query/fragment)
  - Pros: Accepts more citations for sites that use tracking params.
  - Cons: May accept evidence from different content than the aggregated header points to.

### 11. Open Questions

- Should we ever ignore query parameters for membership when the path matches exactly? (Default: No in this iteration.)
- Do we need a debug mode to emit the normalized forms for troubleshooting? (Default: Optional; off by default.)

### 12. Success Metrics & Monitoring

- Track counts by status (`ok`, `invalid_evidence`, `invalid_json`, `http_error`).
- Emit per-domain validation error details (already present) and sample a subset for manual spot checks.
