## 1) Introduction/Overview

Some sites return only the homepage even though they have service pages. Likely causes:

- Internal link checks are too strict (e.g., `www` vs apex host) and re-filter links that Crawl4AI already marked internal.
- Services detection relies only on path prefixes and misses CMS/query URLs (e.g., `/index.cfm?Page=Services`, `?page_id=...`) and anchor/title cues.
- Thresholding leaves selections below cap without deterministic backfill.

This PRD specifies fixes to improve internal detection and services discovery while keeping hard excludes (service-area), determinism, and auditability.

## 2) Goals

- Treat `www` and apex hosts as same-site for internal checks; trust Crawl4AI internal classification.
- Detect services via path, query params, anchor text, and head title.
- When < cap, backfill deterministically from priority buckets.

## 3) User Stories

- As a user, I want service pages selected even if URLs use query params or CMS routes.
- As a developer, I want resilient internal detection across `www`/apex.
- As a PM, I want up to 4 useful pages when services exist, excluding service-area.

## 4) Functional Requirements

1. Internal Link Acceptance

   - Trust `result.links.internal` as internal; avoid re-dropping them as external.
   - For self-validation, fold `www.` and compare registrable domain; normalize scheme.
   - Strip fragments for dedupe; keep query for routing.

2. Services Detection (Multi-signal)

   - Path: continue prioritizing `/services` hubs and children.
   - Query: treat URLs like `/index.cfm?Page=Services` or `?page_id=...` as service pages when:
     - query contains `services` (key or value), or
     - head title contains `Services`, or
     - anchor text contains `Services` or whitelisted terms.
   - WordPress/ID routes: if `?page_id=...` and title/anchor imply services, treat as service page.
   - Expand whitelist Tier 2 with `design`, `monitoring`.
   - Allow services hub recognition via title/anchor/query even if path doesn’t start with `/services`.

3. Scoring/Thresholding

   - Base: `total = 0.6*contextual + 0.4*(intrinsic/10)`; boosts: hub +0.30 (or +0.25 if inferred), Tier1 +0.20, Tier2 +0.10.
   - Threshold bypass for confirmed services hub or Tier1 in title/anchor/query.
   - Continue hard-excluding `service-area`/`service area`.

4. Deterministic Backfill (if selected < cap)

   - Backfill in order: remaining services-intent → About → Certifications → Projects → Contact.
   - Respect hard excludes and dedupe; label `selection_reason=backfill:<bucket>`.

5. Logging/Observability
   - Log drop reasons per candidate.
   - Persist per-link: `bucket`, scores, `selection_reason`, `matched_slugs`.
   - Counters: candidates, accepted internal, excluded service-area, below-threshold, selected, backfilled.

## 5) Non-Goals

- No deep crawl; homepage-based only. No LLM reranking. No external selection.

## 6) Success Metrics

- Reduce `internal_links_found > 0` but `selected_links_count == 0` by ≥ 80%.
- Select known services for:
  - `veteran-fire.com` (e.g., Fire Extinguishers, Fire Sprinkler Systems)
  - `shieldfireprotection.com` (`/services`)
  - `colonialfire.com` (`/index.cfm?Page=Services`)
  - `capitolfire.com` (`/services/installation`)
- Maintain 0 service-area selections.

## 7) Open Questions

- Use ETLD+1 lib or simple `www` folding for internal equivalence?
- Hub boost when inferred via title/anchor/query: keep +0.30 or use +0.25?
- Backfill ordering: include Industries before About?
- Threshold default: 0.25 vs 0.20?
