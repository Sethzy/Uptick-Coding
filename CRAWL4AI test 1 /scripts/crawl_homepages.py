"""
Purpose: Crawl first N website homepages from CSV using Crawl4AI and save output.

Description: Loads `uptick-csvs/testing-crawl4AI.csv`, normalizes website URLs,
then uses `AsyncWebCrawler` to fetch each homepage and save markdown to
`CRAWL4AI testing/outputs/<domain>/index.md`. Errors are logged and do not halt
the run.

Key Functions/Classes:
- crawl_one: Crawl a single URL and return markdown text or error.
- save_markdown: Persist markdown to per-domain folder.
- main: CLI that orchestrates CSV → URL list → crawl loop → saves.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple
from urllib.parse import urlparse

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

# Import helper with fallback to local path when run as a script
try:
    from .csv_utils import prepare_url_list  # type: ignore
except Exception:  # AIDEV-NOTE: allow running without package context
    import os
    import sys
    sys.path.append(os.path.dirname(__file__))
    from csv_utils import prepare_url_list  # type: ignore


# AIDEV-NOTE: Simple sequential crawl; consider concurrency later if needed


@dataclass
class CrawlOutcome:
    url: str
    success: bool
    error: Optional[str]
    markdown: str


def _markdown_from_result(result) -> str:
    md = getattr(result, "markdown", None)
    if isinstance(md, str):
        return md
    if md is not None and hasattr(md, "raw_markdown"):
        return md.raw_markdown or ""
    return ""


async def crawl_one(crawler: AsyncWebCrawler, url: str) -> CrawlOutcome:
    run_config = CrawlerRunConfig(
        verbose=False,
        cache_mode=CacheMode.ENABLED,
        check_robots_txt=True,
    )
    try:
        result = await crawler.arun(url=url, config=run_config)
        if not getattr(result, "success", True):
            return CrawlOutcome(url, False, getattr(result, "error_message", "Unknown error"), "")
        return CrawlOutcome(url, True, None, _markdown_from_result(result))
    except Exception as exc:  # AIDEV-NOTE: keep crawling on failures
        return CrawlOutcome(url, False, str(exc), "")


def save_markdown(base_out: Path, url: str, markdown_text: str) -> Path:
    parsed = urlparse(url)
    domain = parsed.netloc or "unknown-domain"
    domain_dir = base_out / domain
    domain_dir.mkdir(parents=True, exist_ok=True)
    out_path = domain_dir / "index.md"
    out_path.write_text(markdown_text, encoding="utf-8")
    return out_path


async def run(csv_path: Path, out_dir: Path, limit: int) -> Tuple[int, int]:
    urls: List[str] = prepare_url_list(csv_path, limit=limit)
    if not urls:
        print("No valid URLs found after normalization.")
        return 0, 0

    out_dir.mkdir(parents=True, exist_ok=True)
    success_count = 0
    fail_count = 0

    async with AsyncWebCrawler() as crawler:
        for idx, url in enumerate(urls, start=1):
            print(f"[{idx}/{len(urls)}] Crawling: {url}")
            outcome = await crawl_one(crawler, url)
            if outcome.success and outcome.markdown:
                save_path = save_markdown(out_dir, outcome.url, outcome.markdown)
                print(f"  ✓ Saved: {save_path}")
                success_count += 1
            else:
                print(f"  ✗ Failed: {outcome.error}")
                fail_count += 1

    return success_count, fail_count


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Crawl first N homepages from CSV using Crawl4AI")
    parser.add_argument(
        "--csv",
        default=str(Path("uptick-csvs") / "testing-crawl4AI.csv"),
        help="Path to input CSV file with a `website` column",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Limit number of sites to crawl",
    )
    parser.add_argument(
        "--out",
        default=str(Path("CRAWL4AI testing") / "outputs"),
        help="Output directory for markdown files",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    csv_path = Path(args.csv)
    out_dir = Path(args.out)
    limit = args.limit

    try:
        success_count, fail_count = asyncio.run(run(csv_path, out_dir, limit))
        print(f"Done. Success: {success_count}, Failures: {fail_count}")
        return 0
    except KeyboardInterrupt:
        print("Interrupted.")
        return 130


if __name__ == "__main__":
    sys.exit(main())


