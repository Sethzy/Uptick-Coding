"""
Purpose: Session-related helpers (stable session IDs and browser-like headers).
Description: Provides deterministic per-domain session IDs and coherent headers
             to reduce WAF friction, aligning with PRD guidance.
Key Functions: stable_session_id, build_headers

AIDEV-NOTE: Keep UA stable per domain. Optionally rotate across domains.
"""

from __future__ import annotations
import hashlib
from typing import Dict

try:
    from fake_useragent import UserAgent  # type: ignore
except Exception:  # pragma: no cover
    UserAgent = None  # type: ignore


def stable_session_id(domain: str) -> str:
    digest = hashlib.md5(domain.encode("utf-8")).hexdigest()[:10]
    return f"sess_{digest}"


def _choose_user_agent() -> str:
    if UserAgent is not None:
        try:
            # AIDEV-NOTE: Cached random modern UA; avoid frequent network.
            ua = UserAgent().chrome
            if isinstance(ua, str) and ua:
                return ua
        except Exception:
            pass
    # Fallback UA (modern Chrome Windows)
    return (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    )


def build_headers(locale: str = "en-US") -> Dict[str, str]:
    ua = _choose_user_agent()
    return {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": f"{locale},{locale.split('-')[0]};q=0.9",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
