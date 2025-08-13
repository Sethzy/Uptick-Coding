"""
Purpose: Canonical URL fallback probing and robots preflight helpers.
Description: Builds canonical URL candidates from apex domain and determines the
             first reachable URL, with basic robots disallow signaling.
Key Functions: canonicalize_domain, is_robot_disallowed

AIDEV-NOTE: Network fetch logic will be handled by Crawl4AI during arun, but we
            pre-probe reachability using httpx for speed.
"""

from __future__ import annotations
import httpx
from typing import List, Optional, Dict
import asyncio
from .session import build_headers

FALLBACKS = (
    "https://{root}",
    "https://www.{root}",
    "http://{root}",
    "http://www.{root}",
)


async def canonicalize_domain(
    root: str,
    *,
    timeout: float = 12.0,
    max_retries: int = 2,
    initial_backoff_sec: float = 0.6,
    headers: Optional[Dict[str, str]] = None,
) -> Optional[str]:
    """
    Attempt to resolve a canonical base URL by probing a set of fallback templates.

    Resiliency improvements:
    - Slightly higher default timeout
    - Retry each candidate with exponential backoff
    """
    candidates: List[str] = [t.format(root=root) for t in FALLBACKS]

    req_headers = headers or build_headers()
    async with httpx.AsyncClient(follow_redirects=True, timeout=timeout, headers=req_headers) as client:
        for url in candidates:
            attempt = 0
            backoff = initial_backoff_sec
            while attempt <= max_retries:
                try:
                    r = await client.get(url)
                    if r.status_code < 400:
                        return str(r.url)
                    # Treat 4xx as definitive non-canonical for this candidate; break to next
                    if 400 <= r.status_code < 500:
                        break
                except Exception:
                    # retry on network exceptions
                    pass
                attempt += 1
                if attempt <= max_retries:
                    await asyncio.sleep(backoff)
                    backoff *= 2
            # next candidate
    return None


async def is_robot_disallowed(root_or_url: str, *, timeout: float = 6.0) -> bool:
    # Minimal robots preflight; Crawl4AI will honor robots during crawl
    base = root_or_url
    if "://" not in base:
        base = f"https://{base}"
    origin = base.split("//", 1)[-1].split("/", 1)[0]
    robots_url = f"https://{origin}/robots.txt"
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.get(robots_url)
            if r.status_code >= 400:
                return False
            # Cheap heuristic: if robots explicitly disallows '/', assume blocked
            text = r.text.lower()
            return "disallow: /\n" in text or "disallow: /\r\n" in text
    except Exception:
        return False
