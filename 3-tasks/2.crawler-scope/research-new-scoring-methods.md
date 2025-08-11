<!--
Purpose: Research PRD to design enhanced scoring methods using labeled exemplars and founder heuristics.
Description: This document follows `.claude/commands/3a-backend-phase/create-research-doc.md` and explores new
scoring strategies leveraging a 100+ perfect-match dataset and CEO-provided handwritten heuristics. It aligns with
existing crawler and scoring PRDs and defines a plan for feature extraction, modeling, and evaluation.
Key Sections: Feature Overview; Internal Codebase Analysis; External Documentation & Examples; Implementation Plan;
Key Considerations & Gotchas.
-->

<!-- AIDEV-NOTE: Use alongside `3-tasks/2. scoring/prd-scoring-system.md` and crawler PRDs. -->
<!-- AIDEV-NOTE: Keep scoring weights configurable and make evidence URLs/snippets auditable. -->

### 1. Feature Overview

We will design and evaluate new scoring methods that go beyond the current rubric-driven approach by:

- Incorporating a labeled dataset of ~100+ “perfect match” companies to extract discriminative signals/features.
- Encoding CEO-provided handwritten criteria into explicit, testable heuristics that can be weighted and audited.
- Producing a composite score and labels that remain compatible with the existing output schema in `prd-scoring-system.md`.

Primary deliverable: an improved, auditable scoring pipeline that combines rules, exemplar-derived features, and optional LLM assistance, yielding higher precision against a golden set.

### 2. Research & Resources

#### 2.1. Internal Codebase Analysis

Summary Table of Relevant Code

| Area/Feature                   | File(s)                                                      | Description                                                         | Reuse/Extension Opportunity                                          |
| ------------------------------ | ------------------------------------------------------------ | ------------------------------------------------------------------- | -------------------------------------------------------------------- |
| Crawler PRD (scope, artifacts) | `3-tasks/1.project-scoping/prd-targeted-domain-crawler.md`   | Defines content bundle fields and evidence capture used downstream. | Reuse page-level artifacts and evidence snippets as features.        |
| Crawler PRD (alt copy)         | `3-tasks/2. scoring/prd-targeted-domain-crawler.md`          | Variant of crawler PRD with slightly different page cap.            | Same as above; ensure consistency on page budget.                    |
| Current Scoring PRD            | `3-tasks/2. scoring/prd-scoring-system.md`                   | LLM-first classification with guardrails; rubric-based 0–90.        | Maintain output compatibility; add new features/weights.             |
| Legacy Criteria (GMaps)        | `3-tasks/2. scoring/prd-fire-protection-scoring-criteria.md` | Prior criteria including size and keywords.                         | Mine keywords and patterns to seed features; deprecate size for now. |

Existing Patterns & Conventions

- Output schema requires: per-criterion scores, confidence, evidence URL/snippet, and classifier mode/model.
- Guardrail approach: LLM primary with fallback to hybrid or rules-only under budget/limits.
- Signals come from normalized text, headings, detected keywords, and evidence snippets captured by crawler.

Reusable Components/Modules

- Evidence snippet generation and detected keyword lists from crawler PRDs can be reused as input features.
- Voting/aggregation pattern in scoring PRD can be extended to include exemplar-based feature votes.

Integration Points

- Input: JSONL content bundles with page arrays and metadata.
- Output: CSV with appended scoring columns (unchanged schema for downstream consumers).

Potential Redundancies

- Multiple crawler PRD copies differ on page cap (3 vs 4). Standardize ingest assumptions during evaluation.

Backward Compatibility Considerations

- Preserve existing CSV columns; add new columns only as optional (e.g., `score_match_exemplar`, `heuristic_profile_id`).
- Keep classifier modes consistent: LLM | HYBRID | RULES, with new methods mapping into HYBRID/RULES.

Summary of Recommendations

- Derive a compact feature set from perfect-match exemplars and encode CEO heuristics as explicit rules; blend via a transparent, configurable weighting scheme. Maintain current outputs and auditability.

#### 2.2. External Documentation & Examples

Note: Will be completed after gathering your specific sources per process. Please share any URLs/files for:

- The 100+ perfect-match dataset (CSV/JSON, with labels and any notes).
- CEO handwritten criteria (images, notes, or transcriptions).
- Any prior ICP definitions, sales qualification frameworks, or playbooks.

Placeholder resources to consider incorporating:

1. LLM prompt citation patterns for classification

- How to Use: Ensure each label decision includes a URL + snippet; design prompts to require cite-and-score.

2. Weak-supervision/heuristic labeling references (e.g., Snorkel blog)

- How to Use: Convert CEO heuristics to labeling functions; analyze coverage, conflicts, and accuracies.

3. Feature extraction from text (keyword and pattern mining)

- How to Use: Seed features from headings/services/industries pages; score presence, density, and proximity.

4. Calibration and thresholding best practices

- How to Use: Calibrate composite scores on golden set to maximize precision at target recall.

5. Auditability and model cards for decision systems

- How to Use: Maintain per-decision rationale with top features/heuristics and evidence URLs.

### 3. Implementation Plan

#### 3.1. Approach & Pseudocode

Top likely sources of improvement:

- Exemplar-derived features: Mine discriminative terms/phrases and structural cues from perfect matches.
- CEO heuristic encoding: Translate handwritten rules into deterministic checks with weights and evidence.
- Hybrid scoring blend: Combine heuristics, exemplar features, and optional LLM checks under budget.

Recommended approaches:

1. Heuristic-first with exemplar-informed weights (RULES/HYBRID)

- Build a feature lexicon from exemplars; weight via frequency and mutual information.
- Encode CEO heuristics; assign explicit weights and tie to evidence extraction.
- Optional LLM verification step when signals conflict.

2. Exemplar similarity with centroid/prototype matching (HYBRID)

- Create TF-IDF or embedding prototype from perfect matches; score cosine similarity per domain.
- Blend similarity with heuristics for final score; cite top supporting pages/snippets.

3. LLM rubric with learned priors (LLM/HYBRID)

- Prompt LLM with rubric plus exemplar-derived hints; require citations.
- Fall back to rules-only for budget/length limits.

Pseudocode (sketch):

```pseudocode
function score_domain(domainRecord):
  pages = domainRecord.pages
  features = extract_features(pages)        # keywords, headings, services, industries, associations
  evidence = collect_evidence(pages)        # best URL/snippet per signal

  heuristic_score, heur_rationale = apply_ceo_heuristics(features, evidence)
  exemplar_score, ex_rationale = score_against_exemplar_profile(features, pages)

  if budget_allows and conflict_detected(heuristic_score, exemplar_score):
    llm_label, llm_conf, llm_ev = llm_verify(features, top_pages(pages))
  else:
    llm_label, llm_conf, llm_ev = None, None, None

  final = blend_scores({
    "heuristics": heuristic_score,
    "exemplar": exemplar_score,
    "llm": normalize_llm(llm_label, llm_conf)
  }, weights=config.weights)

  return {
    scores: map_to_schema(final),
    confidence: compute_confidence(final),
    evidence: select_best_evidence(evidence, llm_ev),
    classifier_mode: choose_mode(llm_ev)
  }
```

Implementation notes:

- Feature extraction: prefer headings and services/industries pages; compute keyword density and proximity.
- Exemplar profile: train lightweight centroids (TF-IDF or small embeddings) from perfect matches; store top-n terms.
- Heuristics: implement as deterministic labeling functions with weights and human-readable rationale.
- Blending: simple weighted sum with calibration against the golden set; keep weights in config.

#### 3.2. Key Considerations & Gotchas

- Token/cost limits: Gate LLM use; default to RULES/HYBRID. Require citations in any LLM path.
- Data drift: Recompute exemplar profiles periodically; keep lexicons versioned.
- Ambiguous sites: Prefer conservative scoring and lower confidence; always include rationale and evidence.
- Duplicated crawler PRDs: Align on page cap during evaluation runs to keep comparability.
- Auditability: Store which heuristics fired, with their evidence URLs and snippets.

---

Action required before completing this doc

- Please provide: (a) the 100+ perfect-match dataset (CSV/JSON), and (b) the CEO handwritten notes (or transcriptions/URLs). Once received, I will finalize Section 2.2 with concrete resources, derive initial exemplar features, and propose default weightings.
