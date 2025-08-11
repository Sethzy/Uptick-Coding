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

import asyncio
import json
from datetime import datetime, timezone
from typing import Dict
import time
import os
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import PruningContentFilter


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

    # Runtime config
    cfg_path = os.path.join(os.getcwd(), "crawler", "config.json")
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    input_csv = os.getenv("INPUT_CSV", os.path.join(os.getcwd(), "uptick-csvs", "final_merged_hubspot_tam_data_resolved.csv"))
    output_jsonl = os.getenv("OUTPUT_JSONL", os.path.join(os.getcwd(), "crawl-output.jsonl"))

    # Load domains
    try:
        domains = load_domains_from_csv(input_csv)
    except Exception as e:
        logger.info(f"Failed to load CSV: {e}")
        return 1

    async def crawl_all() -> int:
        total = len(domains)
        ok = fail = retry = 0
        failure_reasons: Dict[str, int] = {}

        headers = build_headers(locale)
        browser = BrowserConfig(headless=True, verbose=False, extra_http_headers=headers)

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

        with open_jsonl(output_jsonl) as fh:
            async with AsyncWebCrawler(config=browser) as crawler:
                for domain in domains:
                    start_ms = time.time()

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
                        continue

                    # robots preflight
                    if await is_robot_disallowed(canonical_url):
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
                        continue

                    run = CrawlerRunConfig(
                        markdown_generator=md,
                        cache_mode=CacheMode.BYPASS,
                        check_robots_txt=True,
                        session_id=stable_session_id(domain),
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
                        continue

                    page_record = make_page_record(canonical_url, result.__dict__, keywords=cfg.get("keywords", []))
                    rec = {
                        "domain": domain,
                        "canonical_url": canonical_url,
                        "crawler_status": "OK" if getattr(result, "success", True) else "FAIL",
                        "crawler_reason": "" if getattr(result, "success", True) else (getattr(result, "error_message", None) or "UNKNOWN"),
                        "crawl_pages_visited": 1,
                        "crawl_ts": datetime.now(timezone.utc).isoformat(),
                        "pages": [page_record],
                    }
                    write_record(fh, rec)
                    ok += 1
                    elapsed_ms = int((time.time() - start_ms) * 1000)
                    log_progress(logger, domain, "OK", elapsed_ms=elapsed_ms, pages_visited=1)

                    # delay
                    dcfg = cfg.get("per_domain_delay_seconds", {"min": 1.5, "max": 2.0, "jitter": 0.4})
                    await asyncio.sleep(jitter_delay_seconds(dcfg.get("min", 1.5), dcfg.get("max", 2.0), dcfg.get("jitter", 0.4)))

        log_summary(logger, total=total, ok=ok, fail=fail, retry=retry, reasons=failure_reasons)
        return 0 if fail == 0 else 1

    return asyncio.run(crawl_all())


if __name__ == "__main__":
    raise SystemExit(main())
