"""
Purpose: CLI entrypoint scaffold for the targeted domain crawler.
Description: Loads optional environment (.env) for proxy and locale, validates
            runtime prerequisites, and will later orchestrate crawling.
Key Functions: main

AIDEV-NOTE: This is a scaffold to satisfy Task 1 (env + docs). Core crawling
logic will be implemented in later tasks.

Quickstart (setup):
  1) source venv/bin/activate
  2) python -m playwright install chromium
  3) python crawler/run_crawl.py
"""

from __future__ import annotations
import os
import sys

try:
    from dotenv import load_dotenv  # type: ignore
except Exception:  # pragma: no cover
    def load_dotenv(*_args, **_kwargs):  # fallback if not available
        return False

from .logging import get_logger, log_event, log_progress, log_summary
from .reachability import load_domains_from_csv
from .session import stable_session_id, build_headers
from .canonical import canonicalize_domain, is_robot_disallowed
from .politeness import jitter_delay_seconds, backoff_sequence
from .output_writer import open_jsonl, write_record
from .extraction import make_page_record
from .link_selection import rank_links_by_priority, select_top_links
from .checkpoint import load_checkpoint, save_checkpoint, mark_attempt, mark_success

import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, List, Any
import time
import os
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import PruningContentFilter
import argparse


def main() -> int:
    logger = get_logger("crawler")

    # AIDEV-NOTE: Load .env early to influence network/runtime options.
    load_dotenv()  # looks for .env in CWD by default

    proxy_url = os.getenv("PROXY_URL", "")
    locale = os.getenv("LOCALE", "en-US")

    runtime = {
        "python": sys.version.split()[0],
        "proxy_url": bool(proxy_url),
        "locale": locale,
    }

    log_event(logger, "startup", details=runtime)

    # CLI flags
    parser = argparse.ArgumentParser(description="Targeted domain crawler (PRD aligned)")
    parser.add_argument("--input-csv", default=os.getenv("INPUT_CSV", os.path.join(os.getcwd(), "uptick-csvs", "final_merged_hubspot_tam_data_resolved.csv")))
    parser.add_argument("--output-jsonl", default=os.getenv("OUTPUT_JSONL", os.path.join(os.getcwd(), "crawl-output.jsonl")))
    parser.add_argument("--checkpoint", default=os.getenv("CHECKPOINT", os.path.join(os.getcwd(), ".crawl-checkpoint.json")))
    parser.add_argument("--from-index", type=int, default=int(os.getenv("FROM_INDEX", "0")))
    parser.add_argument("--limit", type=int, default=int(os.getenv("LIMIT", "0")))
    parser.add_argument("--concurrency", type=int, default=int(os.getenv("CONCURRENCY", "1")))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    # Runtime config
    cfg_path = os.path.join(os.getcwd(), "crawler", "config.json")
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    # Load domains
    try:
        all_domains = load_domains_from_csv(args.input_csv)
    except Exception as e:
        logger.info(f"Failed to load CSV: {e}")
        return 1

    # Slice per flags
    domains = all_domains[args.from_index: (args.from_index + args.limit) if args.limit > 0 else None]

    async def crawl_all() -> int:
        total = len(domains)
        ok = fail = retry = 0
        failure_reasons: Dict[str, int] = {}

        # Note: headers are handled internally by Crawl4AI/Playwright. Keep BrowserConfig minimal.
        browser = BrowserConfig(headless=True, verbose=False)

        md = DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(threshold=cfg.get("content_filter_threshold", 0.25), threshold_type="dynamic", min_word_threshold=10),
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

        cp = load_checkpoint(args.checkpoint) if args.resume else {}

        with open_jsonl(args.output_jsonl) as fh:
            async with AsyncWebCrawler(config=browser) as crawler:
                sem = asyncio.Semaphore(max(1, args.concurrency))

                async def crawl_one(domain: str) -> None:
                    nonlocal ok, fail, retry, failure_reasons
                    if args.resume and cp.get(domain) == -1:
                        return
                    start_ms = time.time()
                    mark_attempt(cp, domain)
                    save_checkpoint(args.checkpoint, cp)

                    # canonicalization
                    canonical_url = await canonicalize_domain(domain)
                    if not canonical_url:
                        reason = "DNS_FAIL"
                        rec = {
                            "domain": domain,
                            "canonical_url": "",
                            "crawler_status": "FAIL",
                            "crawler_reason": reason,
                            "crawl_pages_visited": 0,
                            "crawl_ts": datetime.now(timezone.utc).isoformat(),
                            "pages": [],
                        }
                        write_record(fh, rec)
                        fail += 1
                        failure_reasons[reason] = failure_reasons.get(reason, 0) + 1
                        log_progress(logger, domain, "FAIL", reason=reason, elapsed_ms=int((time.time()-start_ms)*1000))
                        mark_success(cp, domain)  # finalize state as processed
                        save_checkpoint(args.checkpoint, cp)
                        return

                    # robots preflight (allow override per domain)
                    respect_robots = cfg.get("respect_robots", True)
                    overrides = set(cfg.get("robots_overrides", []))
                    if respect_robots and (domain not in overrides) and await is_robot_disallowed(canonical_url):
                        reason = "ROBOT_DISALLOW"
                        rec = {
                            "domain": domain,
                            "canonical_url": canonical_url,
                            "crawler_status": "SKIPPED",
                            "crawler_reason": reason,
                            "crawl_pages_visited": 0,
                            "crawl_ts": datetime.now(timezone.utc).isoformat(),
                            "pages": [],
                        }
                        write_record(fh, rec)
                        retry += 1
                        failure_reasons[reason] = failure_reasons.get(reason, 0) + 1
                        log_progress(logger, domain, "SKIPPED", reason=reason, elapsed_ms=int((time.time()-start_ms)*1000))
                        mark_success(cp, domain)
                        save_checkpoint(args.checkpoint, cp)
                        return

                    run = CrawlerRunConfig(
                        markdown_generator=md,
                        cache_mode=CacheMode.BYPASS,
                        check_robots_txt=True,
                        session_id=stable_session_id(domain),
                        simulate_user=True,
                        magic=True,
                        excluded_tags=cfg.get("excluded_tags", ["nav", "footer", "script", "style"]),
                        exclude_external_links=cfg.get("exclude_external_links", True),
                        process_iframes=True,
                        remove_overlay_elements=True,
                        word_count_threshold=10,
                        page_timeout=cfg.get("page_timeout_ms", 30000),
                        stream=False,
                        verbose=False,
                    )

                    try:
                        result = await crawler.arun(url=canonical_url, config=run)
                    except Exception:
                        reason = "TIMEOUT"
                        rec = {
                            "domain": domain,
                            "canonical_url": canonical_url,
                            "crawler_status": "FAIL",
                            "crawler_reason": reason,
                            "crawl_pages_visited": 0,
                            "crawl_ts": datetime.now(timezone.utc).isoformat(),
                            "pages": [],
                        }
                        write_record(fh, rec)
                        fail += 1
                        failure_reasons[reason] = failure_reasons.get(reason, 0) + 1
                        log_progress(logger, domain, "FAIL", reason=reason, elapsed_ms=int((time.time()-start_ms)*1000))
                        return

                    pages: List[Dict[str, Any]] = []
                    homepage = make_page_record(canonical_url, result, keywords=cfg.get("keywords", []))
                    pages.append(homepage)

                    # Link discovery and selection from homepage
                    links_obj = getattr(result, "links", None) or {}
                    internal_links: List[str] = []
                    # Normalize links: handle strings or dicts with href/url
                    def _norm_link(x: Any) -> str:
                        if isinstance(x, str):
                            return x
                        if isinstance(x, dict):
                            return x.get("url") or x.get("href") or ""
                        return ""
                    if isinstance(links_obj, dict):
                        raw_internal = links_obj.get("internal", [])
                        internal_links = [l for l in (_norm_link(x) for x in raw_internal) if l]
                    elif isinstance(links_obj, list):
                        internal_links = [l for l in (_norm_link(x) for x in links_obj) if l]
                    # Rank by priority buckets and select up to cap
                    buckets = cfg.get("link_priority_buckets", [])
                    ranked = rank_links_by_priority(internal_links, buckets)
                    cap = int(cfg.get("page_cap", 4))
                    selected_links = select_top_links(ranked, cap)

                    # Crawl selected pages
                    for link in selected_links:
                        try:
                            r2 = await crawler.arun(url=link, config=run)
                            page_rec = make_page_record(link, r2, keywords=cfg.get("keywords", []))
                            pages.append(page_rec)
                        except Exception:
                            continue

                    # Optional blog/news rule: keep at most one blog/news if it has keywords
                    if cfg.get("allow_blog_if_keywords", True):
                        kept: List[Dict[str, Any]] = []
                        blog_kept = False
                        for p in pages:
                            path = (p.get("url") or "").lower()
                            is_blog = "/blog" in path or "/news" in path
                            if not is_blog:
                                kept.append(p)
                                continue
                            if not blog_kept and p.get("detected_keywords"):
                                kept.append(p)
                                blog_kept = True
                        pages = kept

                    # De-duplicate by normalized text hash
                    seen_hashes = set()
                    deduped: List[Dict[str, Any]] = []
                    import hashlib
                    for p in pages:
                        text = (p.get("markdown_fit") or p.get("markdown_raw") or "")
                        h = hashlib.md5(text.encode("utf-8")).hexdigest()
                        if h in seen_hashes:
                            continue
                        seen_hashes.add(h)
                        deduped.append(p)
                    pages = deduped

                    # Content guard: if no content extracted at all, treat as EMPTY_CONTENT
                    has_any_content = any((p.get("markdown_fit") or p.get("markdown_raw") or p.get("cleaned_html")) for p in pages)
                    if not has_any_content:
                        reason = "EMPTY_CONTENT"
                        rec = {
                            "domain": domain,
                            "canonical_url": canonical_url,
                            "crawler_status": "FAIL",
                            "crawler_reason": reason,
                            "crawl_pages_visited": len(pages),
                            "crawl_ts": datetime.now(timezone.utc).isoformat(),
                            "pages": pages,
                        }
                        write_record(fh, rec)
                        fail += 1
                        failure_reasons[reason] = failure_reasons.get(reason, 0) + 1
                        log_progress(logger, domain, "FAIL", reason=reason, elapsed_ms=int((time.time()-start_ms)*1000))
                        mark_success(cp, domain)
                        save_checkpoint(args.checkpoint, cp)
                        dcfg = cfg.get("per_domain_delay_seconds", {"min": 1.5, "max": 2.0, "jitter": 0.4})
                        await asyncio.sleep(jitter_delay_seconds(dcfg.get("min", 1.5), dcfg.get("max", 2.0), dcfg.get("jitter", 0.4)))
                        return

                    rec = {
                        "domain": domain,
                        "canonical_url": canonical_url,
                        "crawler_status": "OK" if getattr(result, "success", True) else "FAIL",
                        "crawler_reason": "" if getattr(result, "success", True) else (getattr(result, "error_message", None) or "UNKNOWN"),
                        "crawl_pages_visited": len(pages),
                        "crawl_ts": datetime.now(timezone.utc).isoformat(),
                        "pages": pages,
                    }
                    write_record(fh, rec)
                    ok += 1
                    elapsed_ms = int((time.time() - start_ms) * 1000)
                    log_progress(logger, domain, "OK", elapsed_ms=elapsed_ms, pages_visited=len(pages))

                    mark_success(cp, domain)
                    save_checkpoint(args.checkpoint, cp)

                    # delay per domain
                    dcfg = cfg.get("per_domain_delay_seconds", {"min": 1.5, "max": 2.0, "jitter": 0.4})
                    await asyncio.sleep(jitter_delay_seconds(dcfg.get("min", 1.5), dcfg.get("max", 2.0), dcfg.get("jitter", 0.4)))

                async def worker(domain: str):
                    async with sem:
                        if args.dry_run:
                            log_progress(logger, domain, "DRY_RUN")
                            return
                        await crawl_one(domain)

                await asyncio.gather(*[worker(d) for d in domains])

        log_summary(logger, total=total, ok=ok, fail=fail, retry=retry, reasons=failure_reasons)
        return 0 if fail == 0 else 1

    return asyncio.run(crawl_all())


if __name__ == "__main__":
    raise SystemExit(main())
