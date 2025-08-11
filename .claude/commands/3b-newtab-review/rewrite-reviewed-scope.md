You are revising the original PRD file to reorgnise to do's so it's clear what we're shipping for MVP scope and what we'll do later. Keep the PRD file structure, but reorgniase the content.

Inputs:

- The original PRD
- The MVP revision plan.

Rules (must follow):

- Keep the exact existing section headings and order. Do not add or remove sections.
- Inside each existing section, reorganize content into two clearly labeled blocks:
  - MVP (Do Now): smallest coherent scope to deliver value in 2 weeks
  - Later (Defer): valuable but non-essential for MVP
- Keep original wording where possible; trim or move rather than rewrite.
- In Functional Requirements, prefix each item with [MVP] or [Later].
- In Technical/Design Considerations, keep only MVP-critical details in the main text; move the rest to a short “Deferred Notes” paragraph at the end of that same section.
- Do not introduce new features or change API names; only label which are MVP vs Later.
- Add a one-line “Scope Note” at the very top stating the constraints and scoping intent.
- Preserve any removed details at the bottom as an “Appendix — Deferred/Reference (verbatim excerpts)”.

Output:

- Return the revised PRD text only, preserving the original headings, with MVP/Later labeling applied as described.
