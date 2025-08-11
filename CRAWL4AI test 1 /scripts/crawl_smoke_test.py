"""
Purpose: Minimal Crawl4AI smoke test script.

Description: Uses `AsyncWebCrawler` to crawl a single URL and prints the first
few characters of extracted markdown to verify local installation.

Key Functions/Classes:
- main: Async entrypoint that performs a single crawl.
"""

from __future__ import annotations

import asyncio
from typing import Any

from crawl4ai import AsyncWebCrawler


# AIDEV-NOTE: Keep this script lightweight for fast validation


async def main() -> None:
    url = "https://example.com"
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url)
        snippet: str = ""
        # result.markdown can be a string or a MarkdownGenerationResult-like object
        md = getattr(result, "markdown", None)
        if isinstance(md, str):
            snippet = md[:300]
        elif md is not None and hasattr(md, "raw_markdown"):
            snippet = (md.raw_markdown or "")[:300]
        print(snippet)


if __name__ == "__main__":
    asyncio.run(main())


