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

from .logging import get_logger, log_event


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

    # AIDEV-NOTE: Placeholder; real crawling orchestrated in Task 2+.
    logger.info("Crawler scaffold ready. Configure and run subsequent tasks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
