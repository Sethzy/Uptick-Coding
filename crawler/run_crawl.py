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

from crawler_logging import get_logger, log_event, log_progress, log_summary
from reachability import load_domains_from_csv, load_domain_id_pairs_from_csv
from session import stable_session_id
from canonical import canonicalize_domain, is_robot_disallowed
from politeness import jitter_delay_seconds
from output_writer import open_jsonl, write_record
from report_md import generate_markdown_report
from extraction import make_page_record
from link_selection import (
    extract_anchors_from_html,
    select_links_simple,
)
from checkpoint import load_checkpoint, save_checkpoint, mark_attempt, mark_success

import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, List, Any
import time
import os
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
try:  # Prefer top-level import; fallback to adaptive module if needed
    from crawl4ai import LinkPreviewConfig  # type: ignore
except Exception:  # pragma: no cover
    try:
        from crawl4ai.adaptive_crawler import LinkPreviewConfig  # type: ignore
    except Exception:  # pragma: no cover
        LinkPreviewConfig = None  # type: ignore
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
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
    parser.add_argument("--output-jsonl", default=os.getenv("OUTPUT_JSONL", os.path.join(os.getcwd(), "llm-input.jsonl")))
    parser.add_argument("--checkpoint", default=os.getenv("CHECKPOINT", os.path.join(os.getcwd(), ".crawl-checkpoint.json")))
    parser.add_argument("--from-index", type=int, default=int(os.getenv("FROM_INDEX", "0")))
    parser.add_argument("--limit", type=int, default=int(os.getenv("LIMIT", "0")))
    parser.add_argument("--concurrency", type=int, default=int(os.getenv("CONCURRENCY", "2")))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--column", default=os.getenv("DOMAIN_COLUMN", "tam_site"), help="CSV column to read domains from (default: tam_site)")
    parser.add_argument("--id-column", default=os.getenv("ID_COLUMN", "Record ID"), help="CSV column name for stable record ID to carry through outputs")
    parser.add_argument("--robots", choices=["respect", "ignore", "auto"], default=os.getenv("ROBOTS_MODE", "auto"), help="Robots handling: respect, ignore, or auto (use config)")
    args = parser.parse_args()

    # Runtime config
    cfg_path = os.path.join(os.getcwd(), "config.json")
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    # Load domains and optional record IDs
    try:
        # Prefer domain+id pairs to preserve 1:1 mapping to input rows
        domain_id_pairs = load_domain_id_pairs_from_csv(
            args.input_csv, domain_column=args.column, id_column=args.id_column
        )
        all_domains = [d for d, _rid in domain_id_pairs]
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

        # AIDEV-NOTE: Use the default Markdown generator with no additional filtering.
        # This aligns "fit" output with Crawl4AI's standard HTML→Markdown conversion.
        md = DefaultMarkdownGenerator()

        cp = load_checkpoint(args.checkpoint) if args.resume else {}

        # AIDEV-NOTE: As per Aggregated Context PRD, emit a single JSONL with aggregated_context per domain
        # The output shape replaces the previous llm-input.jsonl and raw records for downstream LLM use.
        run_dir = os.path.dirname(os.path.abspath(args.output_jsonl))

        def _approx_tokens(chars: int) -> int:
            try:
                return max(0, int(round(chars / 4)))
            except Exception:
                return 0

        def _normalize_page_text(text: str) -> str:
            """
            Normalization per PRD (subset):
            - collapse repeated whitespace
            - strip markdown link targets, keep anchor text [text](url) -> text
            - normalize newlines to \n
            Note: We intentionally avoid heavy transformations to preserve headings for citations.
            """
            import re
            if not isinstance(text, str):
                return ""
            s = text.replace("\r\n", "\n").replace("\r", "\n")
            # strip markdown link targets: [text](url) -> text
            s = re.sub(r"\[([^\]]+)\]\((?:[^)]+)\)", r"\1", s)
            # collapse whitespace (but keep single newlines)
            s = re.sub(r"[\t\f\v ]+", " ", s)
            s = re.sub(r"\n{3,}", "\n\n", s)
            return s.strip()

        def _build_aggregated_record(domain: str, pages: List[Dict[str, Any]], *, max_tokens: int | None, max_chars: int | None) -> Dict[str, Any]:
            # Deterministic ordering: homepage first, others by (path length asc, URL asc)
            ordered: List[Dict[str, Any]] = []
            if pages:
                homepage = pages[0]
                others = pages[1:]
                def _path_key(u: str) -> tuple[int, str]:
                    from urllib.parse import urlparse
                    try:
                        path = urlparse(u).path or "/"
                    except Exception:
                        path = u or ""
                    return (len(path), u)
                others_sorted = sorted(others, key=lambda p: _path_key(p.get("url") or ""))
                ordered = [homepage] + others_sorted

            sections: List[str] = []
            included_urls: List[str] = []
            seen_normalized_texts: set[str] = set()
            total_chars = 0
            overflow = False

            def _would_exceed(next_text: str) -> bool:
                nonlocal total_chars
                if max_chars is not None and max_chars > 0:
                    return (total_chars + len(next_text)) > max_chars
                if max_tokens is not None and max_tokens > 0:
                    return (_approx_tokens(total_chars + len(next_text)) > max_tokens)
                return False

            # AIDEV-NOTE: Aggregation order policy
            # - Homepage: use markdown_fit (default generator output; links stripped)
            # - Subpages: use markdown_scoped (DOM-scoped, links/images stripped)
            for idx, p in enumerate(ordered):
                url_val = p.get("url") or ""
                if idx == 0:
                    raw_text = p.get("markdown_fit") or ""
                else:
                    raw_text = p.get("markdown_scoped") or ""
                norm = _normalize_page_text(raw_text)
                if not norm:
                    continue
                # deduplicate by normalized text
                if norm in seen_normalized_texts:
                    continue
                header = f"### [PAGE] {url_val}\n"
                section_text = header + norm
                # add separation (two blank lines) when there are existing sections
                if sections:
                    section_text = "\n\n" + section_text
                # budget check
                if _would_exceed(section_text):
                    overflow = True
                    break
                sections.append(section_text)
                included_urls.append(url_val)
                seen_normalized_texts.add(norm)
                total_chars += len(section_text)

            aggregated_context = "".join(sections)
            
            # Aggregate HTML keywords from all pages
            all_html_keywords = set()
            for p in pages:
                page_html_keywords = p.get("html_keywords_found", [])
                if isinstance(page_html_keywords, list):
                    all_html_keywords.update(page_html_keywords)
            
            rec = {
                "domain": domain,
                "aggregated_context": aggregated_context,
                "included_urls": included_urls,
                "overflow": overflow,
                "length": {"chars": len(aggregated_context), "approx_tokens": _approx_tokens(len(aggregated_context))},
                "html_keywords_found": sorted(list(all_html_keywords)),
            }
            return rec

        with open_jsonl(args.output_jsonl) as agg_fh:
            async with AsyncWebCrawler(config=browser) as crawler:
                sem = asyncio.Semaphore(max(1, args.concurrency))

                async def crawl_one(domain: str) -> None:
                    nonlocal ok, fail, retry, failure_reasons
                    # Lookup the first matching record_id for this domain from the input pairs
                    record_id = next((rid for d, rid in domain_id_pairs if d == domain), "")
                    if args.resume and cp.get(domain) == -1:
                        return
                    start_ms = time.time()
                    mark_attempt(cp, domain)
                    save_checkpoint(args.checkpoint, cp)

                    # canonicalization
                    # Allow config overrides for timeouts/retries if present
                    canon_timeout = float(cfg.get("canonicalization_timeout_sec", 12.0))
                    canon_retries = int(cfg.get("canonicalization_retries", 2))
                    canonical_url = await canonicalize_domain(
                        domain,
                        timeout=canon_timeout,
                        max_retries=canon_retries,
                    )
                    if not canonical_url:
                        reason = "DNS_FAIL"
                        # Emit aggregated record with empty context for failed domain
                        # Prepare aggregated record (failure)

                        agg_rec = {
                            "domain": domain,
                            "record_id": record_id,
                            "aggregated_context": "",
                            "included_urls": [],
                            "overflow": False,
                            "length": {"chars": 0, "approx_tokens": 0},
                        }
                        write_record(agg_fh, agg_rec)
                        fail += 1
                        failure_reasons[reason] = failure_reasons.get(reason, 0) + 1
                        log_progress(logger, domain, "FAIL", reason=reason, elapsed_ms=int((time.time()-start_ms)*1000), pages_visited=0)
                        mark_success(cp, domain)  # finalize state as processed
                        save_checkpoint(args.checkpoint, cp)
                        return

                    # robots preflight with CLI override
                    respect_robots_cfg = bool(cfg.get("respect_robots", True))
                    sampling_ignore_cfg = bool(cfg.get("sampling_ignore_robots", False))
                    robots_mode = getattr(args, "robots", "auto")
                    if robots_mode == "respect":
                        respect_robots = True
                        sampling_ignore_robots = False
                    elif robots_mode == "ignore":
                        respect_robots = False
                        sampling_ignore_robots = True
                    else:
                        respect_robots = respect_robots_cfg
                        sampling_ignore_robots = sampling_ignore_cfg
                    overrides = set(cfg.get("robots_overrides", []))
                    if (respect_robots and not sampling_ignore_robots) and (domain not in overrides) and await is_robot_disallowed(canonical_url):
                        reason = "ROBOT_DISALLOW"

                        agg_rec = {
                            "domain": domain,
                            "record_id": record_id,
                            "aggregated_context": "",
                            "included_urls": [],
                            "overflow": False,
                            "length": {"chars": 0, "approx_tokens": 0},
                        }
                        write_record(agg_fh, agg_rec)
                        retry += 1
                        failure_reasons[reason] = failure_reasons.get(reason, 0) + 1
                        log_progress(logger, domain, "SKIPPED", reason=reason, elapsed_ms=int((time.time()-start_ms)*1000), pages_visited=0)
                        mark_success(cp, domain)
                        save_checkpoint(args.checkpoint, cp)
                        return

                    # Link preview + scoring defaults (can be overridden via cfg)
                    link_query = cfg.get("link_query", "fire protection sprinkler inspection testing alarm suppression")
                    link_max = int(cfg.get("link_max_links", 30))
                    link_ccy = int(cfg.get("link_concurrency", 5))
                    link_timeout = int(cfg.get("link_timeout_seconds", 5))
                    link_score_thresh = float(cfg.get("link_score_threshold", 0.0))

                    lp = None
                    if LinkPreviewConfig is not None:
                        try:
                            lp = LinkPreviewConfig(
                                include_internal=True,
                                include_external=False,
                                max_links=link_max,
                                concurrency=link_ccy,
                                timeout=link_timeout,
                                query=link_query,
                                score_threshold=link_score_thresh,
                                verbose=False,
                            )
                        except Exception:
                            lp = None

                    check_robots_txt = bool(respect_robots and not sampling_ignore_robots)

                    # Honor excluded_tags from config (fix key)
                    run = CrawlerRunConfig(
                        markdown_generator=md,
                        cache_mode=CacheMode.BYPASS,
                        check_robots_txt=check_robots_txt,
                        session_id=stable_session_id(domain),
                        simulate_user=True,
                        magic=True,
                         excluded_tags=cfg.get("excluded_tags", ["nav", "footer", "script", "style"]),
                         # Allow external links at crawl time to capture cross-subdomain (apex/www) as internal later
                         exclude_external_links=cfg.get("exclude_external_links", False),
                        process_iframes=True,
                        remove_overlay_elements=True,
                        word_count_threshold=10,
                        page_timeout=cfg.get("page_timeout_ms", 30000),
                         # Short wait can be emulated by page_timeout and simulate_user; omit unsupported param
                        stream=False,
                        verbose=False,
                        score_links=True,
                        link_preview_config=lp,
                    )

                    try:
                        result = await crawler.arun(url=canonical_url, config=run)
                    except Exception:
                        reason = "TIMEOUT"

                        agg_rec = {
                            "domain": domain,
                            "record_id": record_id,
                            "aggregated_context": "",
                            "included_urls": [],
                            "overflow": False,
                            "length": {"chars": 0, "approx_tokens": 0},
                        }
                        write_record(agg_fh, agg_rec)
                        fail += 1
                        failure_reasons[reason] = failure_reasons.get(reason, 0) + 1
                        log_progress(logger, domain, "FAIL", reason=reason, elapsed_ms=int((time.time()-start_ms)*1000), pages_visited=0)
                        return

                    pages: List[Dict[str, Any]] = []
                    emit_links_flag = bool(cfg.get("emit_links", False))
                    # Compute DOM-scoped markdown for homepage
                    content_selectors = cfg.get("content_selectors", [
                        "main", "article", "#content", ".content", ".main", ".main-content", ".container .content", "#primary"
                    ])
                    cleaned_html = getattr(result, "cleaned_html", "") or ""
                    scoped_md = ""
                    try:
                        from extraction import scoped_markdown_from_html  # local import to avoid circulars
                        scoped_md = scoped_markdown_from_html(cleaned_html, content_selectors, base_url=canonical_url)
                    except Exception:
                        scoped_md = ""
                    homepage = make_page_record(
                        canonical_url,
                        result,
                        html_keywords=cfg.get("html_keywords", []),
                        scoped_markdown=scoped_md,
                        emit_links=emit_links_flag,
                    )
                    pages.append(homepage)

                    # Link discovery and selection from homepage
                    links_obj = getattr(result, "links", None) or {}
                    internal_links: List[str] = []
                    internal_links_raw: List[Dict[str, Any]] = []
                    # Normalize links: handle strings, dicts, or objects with .url/.href
                    def _norm_link(x: Any) -> str:
                        if isinstance(x, str):
                            return x
                        if isinstance(x, dict):
                            return x.get("url") or x.get("href") or ""
                        # object with attributes
                        href = getattr(x, "url", None) or getattr(x, "href", None)
                        if isinstance(href, str):
                            return href
                        return ""
                    # Support dict style with 'internal'
                    if isinstance(links_obj, dict):
                        raw_internal = links_obj.get("internal", [])
                        # Preserve raw dicts for scoring-aware selection
                        if raw_internal and isinstance(raw_internal[0], dict):
                            internal_links_raw = raw_internal  # type: ignore[assignment]
                        internal_links = [l for l in (_norm_link(x) for x in raw_internal) if l]
                    else:
                        # object style with attribute 'internal'
                        raw_internal = getattr(links_obj, "internal", None)
                        if isinstance(raw_internal, list):
                            internal_links = [l for l in (_norm_link(x) for x in raw_internal) if l]
                        elif isinstance(links_obj, list):
                            internal_links = [l for l in (_norm_link(x) for x in links_obj) if l]

                    # Fallback: if no internal links, try extracting anchors from HTML
                    # Use the DOM-rendered HTML from Crawl4AI (nav/footer kept for discovery)
                    html = getattr(result, "cleaned_html", None) or ""
                    anchors = extract_anchors_from_html(canonical_url, html, cfg.get("disallowed_paths", []))
                    # Merge while preserving existing
                    merged = list(internal_links)
                    for a in anchors:
                        if a not in merged:
                            merged.append(a)
                    internal_links = merged

                    # Also merge anchors into raw dicts so scoring-aware selector sees them
                    if internal_links_raw is None or not isinstance(internal_links_raw, list):
                        internal_links_raw = []
                    hrefs_in_raw = set()
                    for x in internal_links_raw:
                        if isinstance(x, dict):
                            h = x.get("href") or x.get("url")
                            if isinstance(h, str) and h:
                                hrefs_in_raw.add(h)
                    for a in anchors:
                        if a not in hrefs_in_raw:
                            internal_links_raw.append({"href": a, "text": ""})

                    # No targeted probing here; rely on DOM discovery only

                    # Log counts for debugging
                    log_event(logger, "link_selection", details={
                        "domain": domain,
                        "internal_links_found": len(internal_links),
                        "internal_links_raw": len(internal_links_raw),
                    })
                    # Always use simple selector per spec (ctx_weight=0)
                    cap = int(cfg.get("page_cap", 4))
                    disallowed_paths = cfg.get("disallowed_paths", [])

                    selection_info_map: Dict[str, Any] = {}
                    selected_links: List[str] = []
                    selected_links, selection_info_map = select_links_simple(
                        internal_links_raw,
                        base_url=canonical_url,
                        cap=cap,
                        disallowed_paths=disallowed_paths,
                    )
                    # Exclude homepage from selection and enforce cap again
                    def _norm(u: str) -> str:
                        return (u or "").rstrip('/')
                    selected_links = [u for u in selected_links if _norm(u) != _norm(canonical_url)]
                    if len(selected_links) > cap:
                        selected_links = selected_links[:cap]

                    log_event(logger, "link_selection_ranked", details={
                        "domain": domain,
                        "selected_links_count": len(selected_links),
                        "selected_links": selected_links,
                    })

                    # Crawl selected pages
                    for link in selected_links:
                        try:
                            log_event(logger, "subpage_attempt", details={"domain": domain, "url": link})
                            r2 = await crawler.arun(url=link, config=run)
                            cleaned_html2 = getattr(r2, "cleaned_html", "") or ""
                            try:
                                scoped_md2 = scoped_markdown_from_html(cleaned_html2, content_selectors, base_url=link)
                            except Exception:
                                scoped_md2 = ""
                            page_rec = make_page_record(
                                link,
                                r2,
                                html_keywords=cfg.get("html_keywords", []),
                                scoped_markdown=scoped_md2,
                                emit_links=emit_links_flag,
                            )
                            # Attach only selection_reason for transparency; omit other scoring details
                            if link in selection_info_map:
                                info = selection_info_map.get(link, {})
                                sel_reason = info.get("selection_reason")
                                if isinstance(sel_reason, str) and sel_reason:
                                    page_rec["selection_reason"] = sel_reason
                            pages.append(page_rec)
                            log_event(logger, "subpage_ok", details={
                                "domain": domain,
                                "url": link,
                                "text_length": page_rec.get("text_length", 0),
                            })
                        except Exception as e:
                            log_event(logger, "subpage_error", details={
                                "domain": domain,
                                "url": link,
                                "error": str(e),
                            })
                            continue

                    # Blog/news rule: at most one if strong signals (contextual ≥ threshold and/or whitelisted slug)
                    if cfg.get("allow_blog_if_signals", True):
                        kept: List[Dict[str, Any]] = []
                        blog_kept = False
                        for p in pages:
                            path = (p.get("url") or "").lower()
                            is_blog = "/blog" in path or "/news" in path
                            if not is_blog:
                                kept.append(p)
                                continue
                            # strong signals: contextual score or matched slugs
                            info = selection_info_map.get(p.get("url", ""), {})
                            contextual_ok = isinstance(info.get("contextual_score"), (int, float)) and float(info.get("contextual_score")) >= float(cfg.get("selection_score_threshold", 0.3))
                            has_slug = bool(info.get("matched_slugs"))
                            if not blog_kept and (contextual_ok or has_slug):
                                kept.append(p)
                                blog_kept = True
                        pages = kept

                    # De-duplicate by URL + normalized text to preserve distinct routes even if content overlaps
                    seen_hashes = set()
                    deduped: List[Dict[str, Any]] = []
                    import hashlib
                    for p in pages:
                        url_key = p.get("url") or ""
                        text = (p.get("markdown_fit") or "")
                        h = hashlib.md5(f"{url_key}|{text}".encode("utf-8")).hexdigest()
                        if h in seen_hashes:
                            continue
                        seen_hashes.add(h)
                        deduped.append(p)
                    pages = deduped

                    # Content guard: accept if either scoped or raw markdown exists
                    has_any_content = any(((p.get("markdown_scoped") or p.get("markdown_raw") or p.get("markdown_fit"))) for p in pages)
                    if not has_any_content:
                        reason = "EMPTY_CONTENT"

                        agg_rec = {
                            "domain": domain,
                            "record_id": record_id,
                            "aggregated_context": "",
                            "included_urls": [],
                            "overflow": False,
                            "length": {"chars": 0, "approx_tokens": 0},
                        }
                        write_record(agg_fh, agg_rec)
                        fail += 1
                        failure_reasons[reason] = failure_reasons.get(reason, 0) + 1
                        log_progress(logger, domain, "FAIL", reason=reason, elapsed_ms=int((time.time()-start_ms)*1000), pages_visited=len(pages))
                        mark_success(cp, domain)
                        save_checkpoint(args.checkpoint, cp)
                        dcfg = cfg.get("per_domain_delay_seconds", {"min": 1.5, "max": 2.0, "jitter": 0.4})
                        await asyncio.sleep(jitter_delay_seconds(dcfg.get("min", 1.5), dcfg.get("max", 2.0), dcfg.get("jitter", 0.4)))
                        return

                    # Build aggregated context per PRD
                    max_tokens_cfg = None
                    max_chars_cfg = None
                    # Read budgeting config if present
                    if "max_tokens" in cfg:
                        try:
                            max_tokens_cfg = int(cfg.get("max_tokens"))
                        except Exception:
                            max_tokens_cfg = None
                    if "max_chars" in cfg:
                        try:
                            max_chars_cfg = int(cfg.get("max_chars"))
                        except Exception:
                            max_chars_cfg = None

                    # Write aggregated record
                    agg_rec = _build_aggregated_record(domain, pages, max_tokens=max_tokens_cfg, max_chars=max_chars_cfg)
                    # Attach record_id to aggregated output
                    agg_rec["record_id"] = record_id
                    write_record(agg_fh, agg_rec)
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
        try:
            # AIDEV-NOTE: Emit human-friendly Markdown next to output.jsonl
            generate_markdown_report(args.output_jsonl, args.input_csv)
        except Exception as e:
            logger.info(f"Failed to generate markdown report: {e}")
        return 0 if fail == 0 else 1

    return asyncio.run(crawl_all())


if __name__ == "__main__":
    raise SystemExit(main())
