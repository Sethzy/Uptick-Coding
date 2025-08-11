<!-- AIDEV-NOTE: PRD generated to guide targeted crawling & scoring over ~10k domains using crawl4ai -->

### Product Requirements Document (PRD) — Targeted Domain Crawler for Fire Industry Content

#### Introduction/Overview

The goal is to extract clean, structured website content for companies listed in `final_merged_hubspot_tam_data_resolved.csv` using targeted website crawling with `crawl4ai` to support downstream analysis. This PRD focuses on content acquisition only. A separate PRD will cover classification and scoring.

- Homepage and top high-signal pages content
- Page-level metadata and normalized text
- Evidence snippets around detected keywords

Size is explicitly out of scope for this phase. The output must be a content bundle per domain (JSONL by default; optional per-page Markdown can be enabled in a later slice) with evidence snippets, source URLs, and metadata. The crawl must be intentionally constrained and page-budgeted to remain targeted, resilient, and reproducible over ~10,000 domains with no hard time limit.

<!-- AIDEV-TODO: Future phase can add size and external enrichments (LinkedIn, etc.) if needed. -->

### Goals

- Produce high-quality content bundles per domain suitable for downstream scoring.
- Preserve evidence snippets and URLs for auditability.
- Keep crawl targeted: homepage plus up to four high-signal pages per domain (MLS).
- Operate politely and reliably at large scale (~10k domains) using headless rendering to handle JS-heavy sites.

### User Stories

- As an analyst, I want each domain scored for fire-company status, multi-vertical classification, and core services focus so I can prioritize outreach.
- As a reviewer, I want evidence snippets and source URLs for every score so I can audit decisions quickly.
- As an operator, I want the crawl to resume safely, avoid duplicates, and clearly surface failures and retry states.

### Functional Requirements

1. Input handling

   - Read domains from `tam_site` in `final_merged_hubspot_tam_data_resolved.csv`.
   - Canonicalize domains (handle `http/https`, `www`, trailing slashes). Skip empty or malformed entries.

   Scheme/host fallbacks: reuse the https/www fallback order concept to establish a single canonical start URL per domain.

   Domain canonicalization:

   - Normalize to lower-case; strip schemes, paths, and fragments when present.
   - Attempt reachability with fallback order: `https://{root}` → `https://www.{root}` → `http://{root}` → `http://www.{root}`.
   - Preserve successful canonical URL per domain for downstream crawling.

   - Resolve reachability with fallbacks (HTTP→HTTPS, `www`↔root) before scoring.

   <!-- AIDEV-NOTE: WAF-aware reachability and session persistence added; see bullets below -->

   WAF-aware reachability policy (Cloudflare/anti-bot):

   - Stable randomized user-agent with coherent headers per domain/session.
     - Choose a recent Chrome/Edge UA; keep it stable within a session; rotate only between sessions.
     - Keep headers coherent: `sec-ch-ua*`, `Accept`, `Accept-Language`, `Accept-Encoding`, `Connection`, `Upgrade-Insecure-Requests`, and realistic `Referer` when applicable. Match platform (Windows/macOS) and locale consistently.
   - TLS/HTTP impersonation and rendering alignment:
     - Ensure the HTTP/TLS fingerprint matches modern Chrome. Use the crawler's headless rendering stack per requirements and align headers/UA accordingly.

   Status and bookkeeping:

   - For each row: `canonical_url`, `crawler_status` (OK|FAIL|RETRY|SKIPPED), `crawler_reason`.
   - Reasons include: `MALFORMED_DOMAIN`, `DNS_FAIL`, `TLS_FAIL`, `TIMEOUT`, `BLOCKED` (incl. WAF), `ROBOT_DISALLOW`, `SOCIAL_PROFILE`.

2. Targeted crawl policy (Depth A: homepage + up to 4 pages)

   - Always use headless browser rendering (Playwright via `crawl4ai`) to capture JS content.
   - Page selection priority (H): Services/Capabilities → Industries/Markets → About/Company → Certifications/Associations → Projects/Case Studies → Careers/Team/Numbers → Contact/Locations.
   - Link discovery restricted to on-domain links; exclude subdomains unless explicitly matched by priority rules (e.g., `careers.*` when relevant) to remain targeted.
   - Disallow low-signal paths by default: `/privacy`, `/terms`, `/cookie`, `/legal`, `/sso`, query-heavy tracking URLs. Allow a single “blog”/“news” page only if it contains strong keywords (see Extraction rules).

#### Link Discovery & Selection Strategies

- in the MVP, we will adopt Strategy 1 — Priority-first BFS (deterministic):

  - Extract internal links on homepage; rank by priority buckets using URL patterns and anchor text (e.g., `/services`, `/capabilities`, `/industries`, `/about`, `/certifications`, `/projects|/case`, `/careers`, `/contact`).
  - Select top unique pages across buckets until the 4-page cap is reached.
  - Pros: Fast, predictable; Cons: Might miss content labeled unconventionally.

if there is a problem we will troubelshoot.

3. Politeness and rate limits

   - Robots policy: Soft compliance — honor `Disallow/Allow` rules; ignore non-standard directives (e.g., `crawl-delay`). Use our own politeness: per-domain concurrency = 1 with jittered base delay of 1.5–2.0 seconds; global concurrency configurable.
   - Retries with exponential backoff on transient errors (DNS, 429/5xx) up to 2 retries.
   - Timeout per page: 20–30s including render; abort if content density below threshold twice.

4. Extraction rules (signals)

   - Normalize text (lowercase, collapse whitespace, strip menus/footers where feasible) while retaining page title and H1–H3 headings as strong signals.
   - Capture per-page metadata: title, URL, language, render mode, text length, detected keywords, and candidate evidence snippets.
   - Evidence snippets should be 200–300 chars centered around matched keywords.

   1. Reference: See "Reference crawler configuration (informative)" below for concrete crawler settings that support Section 4 extraction rules.

5. Output (content-only)

   - Produce a content bundle per domain with page-level artifacts only (no classification/scoring).
   - Format: newline-delimited JSON (JSONL) file per run: one record per domain with an array of page objects. Per-page Markdown export is deferred by default and can be enabled in a later slice.
   - Domain-level fields: `domain`, `canonical_url`, `crawler_status` (OK|FAIL|RETRY|SKIPPED), `crawler_reason`, `crawl_pages_visited`, `crawl_ts` (ISO8601).
   - Page-level fields (array under `pages`): `url`, `title`, `language`, `render_mode`, `text_length`, `headings` (H1–H3), `detected_keywords`, `evidence_snippets` (200–300 chars). A `markdown_path` field may be included only if per-page Markdown export is enabled in a later slice.
   - Keep original input row order in an accompanying index if needed for reconciliation.

6. Failure handling and retries

   - On failure, set `crawler_status` to `FAIL` with `crawler_reason` (`DNS_FAIL`, `TIMEOUT`, `BLOCKED`, `ROBOT_DISALLOW`, `EMPTY_CONTENT`, etc.).
   - Also enqueue a retry with backoff (up to 2 attempts). If final attempt fails, leave row as `FAIL`.

7. Idempotency and resume

   - Checkpoint processed domains and attempts. Skips already-successful domains on re-run.
   - Deterministic link selection and page-cap logic; store configuration version/hash for reproducibility.

8. Operations

- Executed locally with `crawl4ai` and Playwright browsers installed.
- Long-running, no global time limit. Provide periodic progress logs and a summary report (counts by status).

### Removed scope (moved to separate PRD)

- Classification approach, scoring model, rubric, and scoring output schema have been moved to `prd-scoring.md`.

### Technical Considerations

- Rendering: Use Playwright headless (Chromium) always to handle SPA/JS sites per requirement 5C.
- Page discovery: Extract and prioritize links using anchor text and URL patterns that match the priority list. Cap at 4 pages (excluding homepage) for MLS.
- Language detection: Deferred beyond MLS to reduce complexity.
- Duplicate detection: Hash normalized text to skip near-duplicates; prefer the first unique page per priority bucket.
- Evidence selection: Use simple keyword matching and extract a centered 200–300 char snippet around the first match.
- Cost/throughput guardrails: Batch domains; manage concurrency and per-domain politeness via `config.json`.
- Configuration: Externalize keywords/lexicons, disallowed paths, page cap, and concurrency in a `config.json`.

### Crawl4AI integration

<!-- AIDEV-NOTE: We implement this PRD with Crawl4AI AsyncWebCrawler and CrawlerRunConfig -->

#### Description

This crawler uses Crawl4AI’s `AsyncWebCrawler` with `CrawlerRunConfig` to render pages, generate markdown, and collect links/metadata. We rely on:

- `DefaultMarkdownGenerator` + `PruningContentFilter` for clean markdown with headings/links preserved
  - Docs: [Markdown generation](https://github.com/unclecode/crawl4ai/blob/main/docs/md_v2/core/markdown-generation.md#_snippet_0), [CrawlResult fields](https://github.com/unclecode/crawl4ai/blob/main/docs/md_v2/assets/llm.txt/txt/llms-full.txt#_snippet_12)
- Targeted content selection via `css_selector`/`target_elements`, `excluded_tags`, and link filtering
  - Docs: [Content selection](https://github.com/unclecode/crawl4ai/blob/main/docs/md_v2/core/content-selection.md#_snippet_11), [Basic options](https://github.com/unclecode/crawl4ai/blob/main/docs/md_v2/assets/llm.txt/txt/config_objects.txt#_snippet_1)
- Robots/session/cache/anti-bot controls: `check_robots_txt`, `session_id`, `CacheMode`, `simulate_user`, `magic`
  - Docs: [Check robots + advanced run](https://github.com/unclecode/crawl4ai/blob/main/docs/md_v2/api/arun.md#_snippet_13), [Config options](https://github.com/unclecode/crawl4ai/blob/main/docs/md_v2/assets/llm.txt/txt/config_objects.txt#_snippet_1)

<!-- AIDEV-NOTE: Crawl4AI key objects — AsyncWebCrawler, CrawlerRunConfig, DefaultMarkdownGenerator, PruningContentFilter -->

#### How to Use

1. Install Crawl4AI and Playwright browsers per Crawl4AI quickstart.
2. Initialize a long-lived `AsyncWebCrawler` context.
3. For each canonical domain URL:
   - Build a `CrawlerRunConfig` with: `CacheMode.BYPASS`, `check_robots_txt=True`, `session_id` scoped per domain, `excluded_tags=["nav","footer","script","style"]`, `exclude_external_links=True`, `process_iframes=True`, `remove_overlay_elements=True`, `word_count_threshold=10`.
   - Attach a `DefaultMarkdownGenerator(PruningContentFilter(threshold≈0.25, threshold_type="dynamic", min_word_threshold=10), options={"body_width":0, "ignore_links":False, "ignore_images":False}).
   - Await `crawler.arun(url, config)`; collect `result.cleaned_html`, `result.markdown.raw_markdown`, `result.markdown.fit_markdown`, `result.links` and page metadata.
4. Emit one JSONL record per domain matching the Output (content-only) schema.

Docs:

- [CrawlerRunConfig basics](https://github.com/unclecode/crawl4ai/blob/main/docs/md_v2/assets/llm.txt/txt/config_objects.txt#_snippet_1)
- [Content selection](https://github.com/unclecode/crawl4ai/blob/main/docs/md_v2/core/content-selection.md#_snippet_11)
- [CrawlResult fields](https://github.com/unclecode/crawl4ai/blob/main/docs/md_v2/assets/llm.txt/txt/llms-full.txt#_snippet_12)
- [Respect robots + advanced run](https://github.com/unclecode/crawl4ai/blob/main/docs/md_v2/api/arun.md#_snippet_13)

<!-- AIDEV-NOTE: How-to aligns Output schema with CrawlResult props (cleaned_html, markdown, links) -->

#### Example Code Snippet

<!-- AIDEV-NOTE: Example uses BYPASS cache for freshness, preserves links, excludes boilerplate; per docs above -->

```python
import asyncio, json, hashlib
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import PruningContentFilter

def stable_session_id(domain: str) -> str:
    return f"sess_{hashlib.md5(domain.encode()).hexdigest()[:10]}"

async def crawl_domain(domain: str, canonical_url: str):
    browser = BrowserConfig(headless=True, verbose=False)
    md = DefaultMarkdownGenerator(
        content_filter=PruningContentFilter(threshold=0.25, threshold_type="dynamic", min_word_threshold=10),
        options={
            "body_width": 0,
            "ignore_emphasis": False,
            "ignore_links": False,
            "ignore_images": False,
            "protect_links": True,
            "single_line_break": True,
            "mark_code": True,
            "escape_snob": False,
        },
    )

    run = CrawlerRunConfig(
        markdown_generator=md,
        cache_mode=CacheMode.BYPASS,
        check_robots_txt=True,              # docs: api/arun.md#_snippet_13
        session_id=stable_session_id(domain),# docs: config_objects.txt#_snippet_1
        excluded_tags=["nav","footer","script","style"],
        exclude_external_links=True,
        process_iframes=True,
        remove_overlay_elements=True,
        word_count_threshold=10,
        page_timeout=30000,
        stream=True,
        verbose=False,
    )

    async with AsyncWebCrawler(config=browser) as crawler:
        result = await crawler.arun(url=canonical_url, config=run)
        record = {
            "domain": domain,
            "canonical_url": canonical_url,
            "crawler_status": "OK" if result.success else "FAIL",
            "crawler_reason": "" if result.success else (result.error_message or "UNKNOWN"),
            "crawl_pages_visited": 1,
            "crawl_ts": __import__("datetime").datetime.utcnow().isoformat(),
            "pages": [
                {
                    "url": canonical_url,
                    "title": (result.metadata or {}).get("title"),
                    "language": (result.metadata or {}).get("language"),
                    "render_mode": "browser",
                    "text_length": len((result.markdown.fit_markdown or result.markdown.raw_markdown or "")),
                    "headings": [],
                    "detected_keywords": [],
                    "evidence_snippets": [],
                    "markdown_raw": result.markdown.raw_markdown if result.markdown else "",
                    "markdown_fit": result.markdown.fit_markdown if result.markdown else "",
                    "cleaned_html": result.cleaned_html or "",
                    "links": result.links or {},
                }
            ],
        }
        print(json.dumps(record))

if __name__ == "__main__":
    asyncio.run(crawl_domain("example.com", "https://example.com"))
```

References:

- Markdown generation and content filter: [quickstart](https://github.com/unclecode/crawl4ai/blob/main/docs/md_v2/core/quickstart.md#_snippet_2)
- Content selection and link analysis: [content-selection](https://github.com/unclecode/crawl4ai/blob/main/docs/md_v2/core/content-selection.md#_snippet_11)
- CrawlResult fields: [crawler-result](https://github.com/unclecode/crawl4ai/blob/main/docs/md_v2/core/crawler-result.md#_snippet_2)

#### Reference crawler configuration (informative)

<!-- AIDEV-NOTE: Example configuration aligning with rendering and content filtering expectations. Non-binding guide. -->

```python
def get_optimized_crawler_config(self) -> CrawlerRunConfig:
    """
    Get optimized crawler configuration following PRD specifications

    PRD Requirements:
    - Use PruningContentFilter with relaxed threshold (0.2-0.3)
    - Configure DefaultMarkdownGenerator with ignore_links: false
    - Set word_count_threshold: 10 to keep shorter content blocks
    - Generate clean, formatted markdown output
    """
    # AIDEV-NOTE: Configure content filtering as per PRD specifications
    content_filter = PruningContentFilter(
        threshold=self.content_filter_threshold,  # 0.25 as specified in PRD
        threshold_type="dynamic",  # Adapts to page structure
        min_word_threshold=10  # Keep shorter content blocks per PRD
    )

    # AIDEV-NOTE: Configure markdown generation to preserve reference context
    markdown_generator = DefaultMarkdownGenerator(
        content_filter=content_filter,
        options={
            "body_width": 0,  # Prevent text wrapping per PRD
            "ignore_emphasis": False,
            "ignore_links": False,  # Preserve reference context per PRD
            "ignore_images": False,
            "protect_links": True,
            "single_line_break": True,
            "mark_code": True,
            "escape_snob": False,
        }
    )

    return CrawlerRunConfig(
        markdown_generator=markdown_generator,
        cache_mode=CacheMode.BYPASS,  # Fresh content retrieval per PRD
        excluded_tags=['script', 'style'],  # Only exclude obvious noise per PRD
        exclude_external_links=True,  # MLS: on-domain only for targeted crawl
        word_count_threshold=10,  # Per PRD specifications
        page_timeout=self.crawl_timeout,
        stream=False,  # MLS: basic logging without streaming
        verbose=False
    )
```

### Non-Goals (Out of Scope)

- Employee size estimation (explicitly excluded for this phase).
- Off-domain enrichment (LinkedIn, Google, third-party APIs).
- Deep crawling beyond 4 targeted pages per domain (MLS cap).
- Classification and scoring (moved to `prd-scoring.md`).
- Writing code for this PRD.

### Success Metrics

- Coverage: ≥ 90% of reachable domains produce a content bundle including homepage + up to 4 targeted pages.
- Content completeness: ≥ 95% of bundles include title, URL, language, and H1–H3 where present; at least one page per domain has ≥ 200 words.
- Auditability: 100% of pages include URL and page-level metadata; evidence snippets are present when keywords detected.
- Robustness: < 10% final `FAIL` after retries across the full dataset.

### Open Questions

1. Are there known subdomains that should be in-scope (e.g., `careers.domain.com`) or should we restrict to apex only?
2. Should we include PDFs if linked from Services/About pages (often contain certifications)? If yes, add 1 PDF per domain to the 3-page budget (would consume one page slot) in a later slice.
3. Confirm acceptance threshold for “operational website” (e.g., 200+ words on homepage OR presence of Services/About pages).

### Deliverables

- This PRD document.
- Content bundle specification (page/domain JSONL schema; per-page Markdown export deferred) suitable for downstream scoring.

### Acceptance Criteria

- An NDJSON file is produced containing one record per input domain with page arrays and required metadata fields; row/domain order is preserved or an index is provided.
- Per-page Markdown export is deferred by default; may be enabled in a later slice.
- The crawler respects robots, is rate-limited, retries transient failures, and logs a summary of statuses.

<!-- AIDEV-NOTE: Keep weights configurable to absorb rubric changes without code refactors. -->
<!-- AIDEV-TODO: After sign-off, create TASK.md with implementation milestones and test plan for the 30-site golden set. -->
