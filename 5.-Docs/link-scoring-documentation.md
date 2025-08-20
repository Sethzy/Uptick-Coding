<!--
/**
 * Purpose: Definitive guide to how links are scored and selected in the crawler.
 * Description: Documents pre-filters, category rules, final scoring, sorting,
 *              and selection as implemented in `crawler/link_selection.py` and
 *              invoked from `crawler/run_crawl.py`.
 * Key Sections: Overview; Pre-filters; Categories & Scores; Final Score & Sort;
 *               Selection; Contextual Scoring Status; Config Knobs; Differences
 *               from previous spec; Examples.
 * AIDEV-NOTE: Keep in sync with `select_links_simple` and related helpers.
 */
-->

## Overview

The crawler uses a deterministic, rule-first scoring system to prioritize internal links that are most likely to represent core service pages. The active selector is `select_links_simple` (no contextual weights). Ordering is stable and reproducible.

## Pre-filters (applied before scoring)

- Internal-only: keep links that resolve to the same origin as the homepage
- Drop paths starting with any `disallowed_paths` (from `crawler/config.json`)
- Exclude homepage URL itself
- De-duplicate absolute URLs
- Drop service-area pages (e.g., top-level `service-areas`, `locations`, `regions`)

## Categories and Base Scores

Evaluated in order; first match wins (no stacking beyond the A-only boost).

- A Services hub: URL starts with `/services` → base 80; if URL also contains any absolute term add +20 A-only boost
  - Absolute terms: `installation`, `install`, `maintenance`, `inspection`, `protection`
- B Absolute services: URL contains any absolute term → base 85
- C About us: URL starts with `/about` → base 75
- U URL service terms: URL contains any of `fire`, `alarm`, `testing`, `extinguishers`, `repair`, `system`, `design`, `monitoring`, `commissioning`, `commission` → base 60
- T Text/title signal: anchor text or title contains "services" OR any absolute term → base 50
- D Default: other internal links → base 0

Notes:

- A-only boost: +20 applies only to category A when an absolute term is also present in the URL
- Evaluation order: A → B → C → U → T → D; stop on first hit

## Final Score and Sorting

- Final score: `final_score = base + A_only_boost`
- Sort order: `final_score` desc, then `path_len` asc, then `href` asc

## Selection

- After sorting, take the top N links where N = `page_cap` from `crawler/config.json`

## Contextual scoring status (disabled)

- Contextual weighting is disabled. We do not include any intrinsic/contextual scores from the crawler runtime.
- Effective formula removes contextual: `final_score = base (+A-only boost)` only
- This matches the runtime usage in `run_crawl.py`, which uses `select_links_simple` and sets contextual weighting to zero.

## Config knobs

- `disallowed_paths`: prefix list filtered before scoring
- `page_cap`: number of links selected per domain

## Differences from the previous spec

- B Absolute services: now base 85 (was 80)
- C About us: now base 75 (was 80)
- Contextual factor removed: no `contextual_score × 10` term; `ctx_weight = 0`
- First-match-wins order and sorting tie-breakers remain the same

## Examples

- Example 1: `https://acme.com/services/fire-alarm-installation`

  - Category A (starts with `/services`) → base 80
  - Absolute term present (`installation`) → +20 boost
  - Final score = 100

- Example 2: `https://acme.com/inspection`

  - Category B (absolute term in URL) → base 85
  - Final score = 85

- Example 3: `https://acme.com/about/team`
  - Category C → base 75
  - Final score = 75

---

### Quick reference (active implementation)

- Selector: `select_links_simple` (deterministic, no contextual)
- Pre-filters: internal-only, drop disallowed paths, drop service-area, de-dup, exclude homepage
- Scoring: A=80 (+20 A-only boost), B=85, C=75, U=60, T=50, D=0
- Sort: final_score desc → path_len asc → href asc
- Select: top `page_cap`

<!-- AIDEV-NOTE: If `select_links_with_scoring` becomes active, document its extra top-level-route drop rule. -->
