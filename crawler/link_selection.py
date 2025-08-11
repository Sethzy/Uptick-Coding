"""
Purpose: Link discovery and priority-based selection for targeted crawling.
Description: Extracts internal links from homepage response and selects up to a
             configured cap across priority buckets.
Key Functions: filter_internal_links, rank_links_by_priority, select_top_links

AIDEV-NOTE: Deterministic selection using stable sorting and bucket order.
"""

from __future__ import annotations
from typing import Dict, Iterable, List, Sequence, Tuple
from urllib.parse import urljoin, urlparse
import re


def is_internal_link(base: str, href: str) -> bool:
    try:
        b = urlparse(base)
        u = urlparse(urljoin(base, href))
        return (u.netloc == b.netloc) and (u.scheme in {"http", "https"})
    except Exception:
        return False


def filter_internal_links(base: str, hrefs: Iterable[str], disallowed_paths: Sequence[str]) -> List[str]:
    out: List[str] = []
    for h in hrefs:
        if not h:
            continue
        if not is_internal_link(base, h):
            continue
        u = urlparse(urljoin(base, h))
        path = u.path or "/"
        if any(path.startswith(p) for p in disallowed_paths):
            continue
        out.append(u.geturl())
    # Deduplicate preserving order
    seen = set()
    uniq: List[str] = []
    for u in out:
        if u not in seen:
            seen.add(u)
            uniq.append(u)
    return uniq


def rank_links_by_priority(links: Sequence[str], buckets: Sequence[Dict]) -> List[Tuple[int, str]]:
    ranked: List[Tuple[int, str]] = []
    for link in links:
        path = urlparse(link).path.lower()
        score = 10_000  # default low priority
        for idx, bucket in enumerate(buckets):
            pats = bucket.get("patterns", [])
            if any(re.search(p, path) for p in pats):
                score = idx
                break
        ranked.append((score, link))
    # Stable sort by score then link to ensure determinism
    return sorted(ranked, key=lambda x: (x[0], x[1]))


def select_top_links(ranked: Sequence[Tuple[int, str]], cap: int) -> List[str]:
    selected: List[str] = []
    for _, link in ranked:
        if len(selected) >= cap:
            break
        if link not in selected:
            selected.append(link)
    return selected
