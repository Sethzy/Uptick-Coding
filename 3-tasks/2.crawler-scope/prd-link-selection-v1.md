# PRD: Link Scoring Upgrade (Pattern-Driven + Contextual Scoring)

## 1) Introduction / Overview

We will upgrade the current deterministic, bucket-only link selection to a scoring-driven system that blends:

- Intrinsic quality heuristics (URL/path structure, depth, anchor context)
- Contextual relevance (BM25 vs. a domain-appropriate query)
- Explicit pattern/slug priorities from `link-patterns-and-slugs.md`
- Deterministic bucket tie-breakers and selection rules

This targets fire-protection company websites and prioritizes pages that explain “what they do,” especially services and top-level service pages, with About as a strong secondary. We will explicitly down-rank location SEO trees (e.g., `/service-area/*`). The crawler still runs a homepage pass and selects a small, high-signal subset of internal pages for extraction.

## 2) Goals

- Rank internal links by a combined score that reflects quality + relevance + domain-specific patterns.
- Select up to a small cap of unique pages (default: 4) with deterministic tie-breaking.
- Preserve existing business rules:
  - Bucket taxonomy intent (Services → Industries → About → Certifications → Projects → Careers → Contact) for tie-breaks
  - At most one blog/news page and only if strong signals are present
- Reduce low-value selections (e.g., `/service-area` trees) while improving coverage of services and About.

## 3) User Stories

- As a research analyst, I want the crawler to automatically pick the most important “services” and “about” pages so I quickly see what the company offers.
- As a developer, I want deterministic selection so repeated runs produce the same outputs for the same site.
- As a PM, I want fewer dead/low-value pages (service-area SEO trees) and more pages that indicate capabilities and credibility.

## 4) Functional Requirements

1. Scoring Pipeline

   1. Compute an Intrinsic Score per link (URL/path, anchor text quality, path depth penalty, basic domain/authority cues). No LLM.
   2. Compute a Contextual Score using BM25 between a provided query and link text fields (title, meta description, anchor text, URL tokens). Requires link head extraction.
   3. Compute a Total Score as a weighted combination of Intrinsic + Contextual. Normalize to 0–1 for sorting and thresholding.

2. Pattern/Slug Prioritization (from `link-patterns-and-slugs.md`)

   1. Strongly prioritize Services hub and its child service pages (e.g., `/services`, `/services/*`).

3. Strongly prioritize top-level service pages without a hub (e.g., `/fire-extinguisher-services`, `/firesprinkler`, `/backflows`).
   - Whitelist-only rule: accept only if the slug contains one of these terms (case-insensitive):
     `inspection`, `maintenance`, `protection`, `installation`, `install`, `commissioning`, `commission`, `fire`, `alarm`, `testing`, `extinguishers`, `repair`, `system`.
   - Tiered priority within the whitelist:
     - Tier 1 (strong boost): `inspection`, `maintenance`, `protection`, `installation`/`install`, `commissioning`/`commission`.
     - Tier 2 (standard boost): `fire`, `alarm`, `testing`, `extinguishers`, `repair`, `system`.
   - All other top-level service-like pages that do not contain the whitelisted slugs are considered irrelevant for selection.
   3. Prioritize About pages (e.g., `/about`, `/about-us`).
4. Hard-exclude service-area/coverage trees. If the path or anchor contains `service-area` or `service area` (case-insensitive), the link must be disregarded completely (not selected under any circumstances). 5. Recognize product catalogs but do not prioritize them over services unless scores are clearly higher.
5. Recognize and boost whitelisted core-service slugs (as above). Apply a larger boost for Tier 1 slugs than Tier 2. Non-whitelisted slugs do not receive boosts and should not be selected when representing top-level service pages without a hub.

6. Buckets and Deterministic Tie-Breakers

   1. Use existing bucket taxonomy for intent: Services/Capabilities → Industries/Markets → About/Company → Certifications/Associations → Projects/Case Studies → Careers/Team/Numbers → Contact/Locations.
   2. Selection order: sort primarily by Total Score (desc). For ties (within small epsilon), apply deterministic tie-breakers:
      - Bucket priority (asc)
      - Path length (asc)
      - URL (lexicographic asc)
   3. Selection must be stable and deterministic across runs for identical inputs.

7. Selection Cap and Uniqueness

   1. Select the top unique links up to a cap (default: 4). The homepage counts toward visited pages if included in results.
   2. Ensure no duplicates when normalized (e.g., canonical path, fragment-stripped).

8. Blog/News Constraint

   1. Allow at most one `/blog` or `/news` page only if strong signals are present (e.g., keyword hits or score ≥ threshold).
   2. Otherwise skip blog/news pages.

9. Filtering

10. Respect include/exclude patterns to remove low-value or irrelevant links pre-scoring (e.g., exclude `/login`, `/admin`, policy/legal).
11. Hard-exclude service-area patterns: any link whose path or anchor contains `service-area` or `service area` (case-insensitive) is excluded from scoring and selection entirely.
12. Exclude external links from final selection (can be scored for diagnostics but not selected).

13. Observability
    1. Persist per-link diagnostic fields: `bucket`, `intrinsic_score`, `contextual_score`, `total_score`, and `selection_reason` (e.g., “services-slug+high-bm25”).
14. Log counts: candidates, filtered, above threshold, selected, skipped by rule (blog/news), and service-area hard-exclusions.

## 5) Non-Goals (Out of Scope)

- No deep BFS across multiple levels; this is a homepage-based selection pass.
- No LLM-based re-ranking in this iteration.
- No Common Crawl or sitemap seeding for additional discovery (can be future work).
- No selection of purely external pages.

## 6) Design Considerations (Optional)

- Default contextual query (single default, overridable per run):
  - "fire protection sprinkler inspection testing alarm suppression"
- Field weights for contextual scoring (simple defaults; sum=1.0):
  - Title: 0.50, Meta: 0.25, Anchor: 0.20, URL: 0.05
- Total score blend (simple defaults):
  - total_score = 0.6 × contextual_score + 0.4 × intrinsic_score
- Pattern vs. Score: pattern/slug boosts should be additive/multiplicative but capped so extremely irrelevant pages don’t win solely by pattern.
- Thresholding: apply a minimum `total_score` threshold to filter out weak links before final selection.
- Determinism: apply stable sorts and fixed epsilon for tie detection.

## 7) Technical Considerations (Optional)

- Use Crawl4AI link head extraction to populate `head_data` and enable contextual BM25 scoring.
- Intrinsic heuristics and BM25 are non-LLM and deterministic; results vary only by site content and configuration.
- Pattern/slug mapping originates from `3-tasks/2.crawler-scope/link-patterns-and-slugs.md` and should be easy to extend.
- Continue to respect robots.txt and apply conservative per-domain delays.

### 7.1) Crawl4AI references and code patterns (for implementation)

Enable link preview + scoring (intrinsic + contextual):

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai import LinkPreviewConfig

config = CrawlerRunConfig(
    link_preview_config=LinkPreviewConfig(
        include_internal=True,
        include_external=False,
        max_links=30,
        concurrency=5,
        timeout=5,
        query="fire protection sprinkler inspection testing alarm suppression",  # default query
        score_threshold=0.3,
        verbose=False
    ),
    score_links=True,   # REQUIRED for intrinsic scoring
    only_text=True,
    verbose=False
)

async with AsyncWebCrawler() as crawler:
    result = await crawler.arun(start_url, config=config)
    internal = result.links.get("internal", [])
```

Access per-link scores and head data:

```python
for link in result.links.get("internal", []):
    href = link.get("href")
    intrinsic = link.get("intrinsic_score")  # 0–10
    contextual = link.get("contextual_score") # 0–1
    total = link.get("total_score")           # 0–1 (combined)
    title = (link.get("head_data") or {}).get("title")
```

Troubleshooting None scores:

```python
config = CrawlerRunConfig(
    score_links=True,
    link_preview_config=LinkPreviewConfig(
        query="fire protection sprinkler inspection testing alarm suppression",
        verbose=True
    )
)
```

Optional custom scorer shape (Advanced / AdaptiveCrawler):

```python
class CustomLinkScorer:
    def score(self, link, query, state) -> float:
        url = getattr(link, 'href', '') or ''
        low = url.lower()
        if 'service-area' in low or 'service area' in low:
            return 0.0  # hard exclude
        if low.startswith('/services'):
            return 2.0  # services hub boost
        tier1 = ['inspection','maintenance','protection','installation','install','commissioning','commission']
        if any(s in low for s in tier1):
            return 1.5
        tier2 = ['fire','alarm','testing','extinguishers','repair','system']
        if any(s in low for s in tier2):
            return 1.2
        return 1.0
```

Link object shape:

```python
{
  "href": "https://example.com/services/inspections",
  "text": "Inspections",
  "title": "",
  "base_domain": "example.com",
  "head_data": {"title": "Inspections | Example", "meta": {"description": "..."}},
  "intrinsic_score": 7.4,
  "contextual_score": 0.63,
  "total_score": 0.71
}
```

## 8) Success Metrics

- Coverage: ≥ 3 of the 4 selected pages typically include Services/Capabilities and/or About.
- Quality: < 2% selected pages are “empty content” outcomes across the dataset.
- Efficiency: p90 per-domain run time ≤ 25 seconds at default concurrency.
- Reduction: service-area pages selected = 0 across the dataset (hard requirement).

## 9) Open Questions

1. Cap value: keep at 4, or adjust to 5?
2. Exact contextual query string: use a single default or derive from keyword set per domain?
3. Field weights for contextual scoring (Title vs. Meta vs. Anchor vs. URL): use recommended defaults or specify ratios?
4. Product pages: should any product catalogs be prioritized for certain sites, or always secondary to services?
5. Blog/news rule: is “strong signals” defined by keyword presence, score threshold, or both?
6. Do we want to record and expose per-link pattern matches (e.g., matched slug terms) alongside scores for debugging?
