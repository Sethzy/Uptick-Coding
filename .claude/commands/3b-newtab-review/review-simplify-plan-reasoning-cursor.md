### Simplify & Scope-Down PRD / Implementation

My develper just finished this and i want to make sure they did a good job. can you review their work?

Ask yourself, is this implemenetation overly complex?

We are building the V1 of the feature. Given a PRD, your job is to simplify the scope, avoid overengineering, and select a Minimum Lovable Product (MLP) that maximizes business outcome per unit of complexity, with a strong preference for the smallest “Minimum Lovable Slice” that can be shipped fast by a solo founder to validate demand.

The end output is a a MARKDOWN summarising all the different points. ot code

#### Inputs

- PRD: {{paste PRD or link; include goals, features, constraints}}
- Constraints: team-size={{N}}, timeframe={{X weeks}}, budget={{$ or eng-weeks}}, tech-debt-constraints={{notes}}
  - Defaults if unspecified: team-size=1 (solo founder), time-box=1 week for first ML slice, reuse existing UI/system primitives, instrument adoption/time-to-value, reversible by toggle, avoid schema changes unless absolutely required.
- Business goals/OKRs: {{primary metrics}}, {{guardrail metrics}}
- Hard requirements: {{compliance, SLAs, contractual deadlines}}

#### Method

1. Extract candidate features/initiatives from the PRD. Group by user outcome.
2. For each feature, analyze: Problem, Hypothesis, User Value, Business Outcome, Success Metrics, Dependencies, Simpler Alternatives, Risks, Assumptions.
3. Define the Minimum Lovable Slice (MLS): the tiniest end-to-end path that delivers the core promise to one narrow use case in ≤ 1 week.
4. Score each feature with the rubric below. Compute Priority.
5. Classify into a 2x2: Complexity (Low/High) × Business Outcome (Low/High): Quick Wins, Big Bets, Fill-ins, Defer/Avoid.
6. Propose MLP scope: the smallest coherent set that proves core value fast. Identify deferrals/cuts.
7. Provide a crisp 1-week plan and critical path callouts.

#### Scoring Rubric (1–5)

- Complexity (Effort/Uncertainty)
  - 1: Very low effort; well-known pattern; no new infra; single-owner.
  - 3: Moderate effort; some unknowns; minor infra; small cross-team touch.
  - 5: High effort; many unknowns; new infra; multi-team coordination.
- Business Outcome (Impact)
  - 1: Minimal effect; nice-to-have; unclear tie to goals.
  - 3: Noticeable lift on a key metric; supports strategy.
  - 5: Direct, material lift on primary goals (revenue/activation/retention); strategic leverage.
- Confidence
  - 1: Speculative; weak evidence; novel space.
  - 3: Some evidence; analogous wins elsewhere.
  - 5: Strong evidence; prior data/tests; clear user pull.

Priority Formula

- Use RICE-like, tuned for solo-founder v1 with heavier complexity penalty:
  Priority = (BusinessOutcome × Confidence) ÷ (Complexity^2)
  - Tie-breakers (in order): fewer calendar days to ship; zero new infra/deps; lowest ongoing maintenance.
  - Default rules: Defer if Complexity ≥ 4 and Confidence ≤ 3; Cut if new infra/vendor or schema migration is required for v1; Prefer reuse/mocks over full integrations for v1.

2x2 prioritization bucket Quadrant:

Quick Wins (Low complexity, High outcome): Do first.
Big Bets (High complexity, High outcome): Plan, de-risk, maybe split into slices.
Fill-ins (Low complexity, Low outcome): Do when you have slack; don’t block on them.
Defer/Avoid (High complexity, Low outcome): Cut or postpone.

#### Output — Ranked Table (concise)

Provide a Markdown table sorted by Priority (desc).

| Rank | Feature | Simple Feature Explanation to a 10 year old | Complexity (1–5) | Outcome (1–5) | Confidence (1–5) | Priority | Quadrant | Rationale (1–2 lines) | Final decision (cut or keep) |
| ---- | ------- | ------------------------------------------- | ---------------- | ------------- | ---------------- | -------- | -------- | --------------------- | ---------------------------- |

#### MLP Scope Recommendation

- Describe the minimal coherent set (features + any must-have integrations) to deliver core value in {{X}} weeks.
- For each included feature: cite the smallest viable implementation and any “scaffolding now vs. later” decisions.
- Note any experiment/flagging plan to gather data early (gates, cohorts, staged rollout), and define clear kill metrics/triggers.
  - Reuse-first: Use existing UI components, existing auth, and existing data paths; no new services for v1.

#### Cut/Defer List (Not Doing Now)

- List all features to cut or defer with a 2-line reason each (e.g., high complexity, low outcome, dependency risk, unclear demand).

#### Risks & Mitigations

- Call out top 3 risks (delivery, adoption, dependencies) and mitigation steps, including a rollback plan (feature flag off; revert path ≤ 5 minutes).

#### One-Week Plan (Time-Boxed)

- Day 1: Define MLS scope, success metric, and kill metric; add feature flag + basic telemetry.
- Day 2–3: Build smallest end-to-end happy path (hardcode/mock where possible); no new infra.
- Day 4–5: Instrument adoption and timing; dogfood with 3–5 target users; fix P0 issues; decide iterate/pivot/stop.

#### Apply To PRD Now

Use the above on this PRD: {{paste PRD here}}. If constraints are missing, assume the solo-founder defaults above.

### IMPORTANT - Ouput format

Produce a markdown that summarises all the above. You must disply the information.

Return Output A (table), then MLP, Cut List, Risks, and One-Week Plan.
