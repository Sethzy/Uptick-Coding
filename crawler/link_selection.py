"""
Purpose: Link discovery and priority-based selection for targeted crawling.
Description: Extracts internal links, applies hard-excludes and whitelist rules,
             and supports two strategies:
             - Legacy deterministic bucket ranking for href strings
             - Scoring-aware selection for Crawl4AI link preview outputs
Key Functions: filter_internal_links, rank_links_by_priority, select_top_links,
               select_links_with_scoring

AIDEV-NOTE: Deterministic selection using stable sorting and bucket order. When
            scores are available, sort by total_score desc with deterministic
            tie-breakers.
"""

from __future__ import annotations
from typing import Any, Dict, Iterable, List, Sequence, Tuple, Optional
from urllib.parse import urljoin, urlparse
import re
from bs4 import BeautifulSoup


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


def extract_anchors_from_html(base_url: str, html: str, disallowed_paths: Sequence[str]) -> List[str]:
    """Extract internal anchor hrefs from HTML, resolve to absolute URLs, filter disallowed, dedupe."""
    if not html:
        return []
    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception:
        return []
    hrefs: List[str] = []
    for a in soup.find_all("a"):
        href = (a.get("href") or "").strip()
        if href:
            hrefs.append(href)
    return filter_internal_links(base_url, hrefs, disallowed_paths)


# -------------------- Scoring-aware selection helpers --------------------

_WHITELIST_TIER1 = [
    "inspection", "maintenance", "protection", "installation", "install",
    "commissioning", "commission",
]

_WHITELIST_TIER2 = [
    "fire", "alarm", "testing", "extinguishers", "repair", "system",
]


def _path_segments(url: str) -> List[str]:
    path = urlparse(url).path or "/"
    segs = [s for s in path.split("/") if s]
    return segs


def _bucket_priority_for_url(url: str, buckets: Sequence[Dict]) -> Tuple[int, str]:
    path = (urlparse(url).path or "/").lower()
    for idx, bucket in enumerate(buckets):
        pats = bucket.get("patterns", [])
        try:
            if any(re.search(p, path) for p in pats):
                return idx, str(bucket.get("name", f"bucket-{idx}"))
        except Exception:
            continue
    return 1_000_000, "unmatched"


def _is_service_area(link: Dict[str, Any]) -> bool:
    href = (link.get("href") or "").lower()
    text = (link.get("text") or "").lower()
    return ("service-area" in href) or ("service area" in href) or ("service area" in text)


def _is_services_hub_or_child(url: str) -> bool:
    path = (urlparse(url).path or "/").lower()
    return path.startswith("/services")


def _is_top_level_without_hub(url: str) -> bool:
    segs = _path_segments(url)
    if not segs:
        return False
    # exactly one segment and not under /services
    return len(segs) == 1 and segs[0] != "services"


def _match_whitelist_slug(url: str) -> Tuple[Optional[str], int]:
    low = (urlparse(url).path or "").lower()
    for s in _WHITELIST_TIER1:
        if s in low:
            return s, 1
    for s in _WHITELIST_TIER2:
        if s in low:
            return s, 2
    return None, 0


def _path_length(url: str) -> int:
    return len(_path_segments(url))


def select_links_with_scoring(
    internal_links: Sequence[Dict[str, Any]],
    *,
    base_url: str,
    buckets: Sequence[Dict],
    cap: int,
    score_threshold: float = 0.0,
    epsilon: float = 1e-6,
) -> Tuple[List[str], Dict[str, Dict[str, Any]]]:
    """
    Select links using Crawl4AI link preview outputs when available.

    - Hard-exclude `service-area` links pre-scoring.
    - For top-level service pages without hub, enforce whitelist-only rule.
    - Apply tiered boosts and services hub boost.
    - Primary sort by total_score (desc). Fallback to intrinsic/contextual if needed.
    - Deterministic tie-breakers: bucket priority asc → path length asc → URL asc.

    Returns (selected_hrefs, selection_info_map)
    """
    # AIDEV-NOTE: We accept dicts shaped like Crawl4AI link objects
    seen = set()
    candidates: List[Dict[str, Any]] = []

    for link in internal_links:
        href = link.get("href") or link.get("url") or ""
        if not href:
            continue
        # only internal
        if not is_internal_link(base_url, href):
            continue
        # dedupe by normalized href
        if href in seen:
            continue
        seen.add(href)

        # hard exclude service-area
        if _is_service_area(link):
            continue

        # whitelist for top-level pages without hub
        if _is_top_level_without_hub(href) and not _is_services_hub_or_child(href):
            slug, tier = _match_whitelist_slug(href)
            if tier == 0:
                # not whitelisted → drop
                continue
            link["_matched_slugs"] = [slug] if slug else []
            link["_whitelist_tier"] = tier
        else:
            # still record slug matches (for boosts/observability)
            slug, tier = _match_whitelist_slug(href)
            link["_matched_slugs"] = [slug] if slug else []
            link["_whitelist_tier"] = tier

        # base scores from Crawl4AI if present
        intrinsic = link.get("intrinsic_score")
        contextual = link.get("contextual_score")
        total = link.get("total_score")
        # Normalize fallback if needed
        base_total = None
        if isinstance(total, (int, float)):
            base_total = float(total)
        else:
            # approximate from intrinsic (0..10) and contextual (0..1)
            it = float(intrinsic) / 10.0 if isinstance(intrinsic, (int, float)) else 0.0
            ct = float(contextual) if isinstance(contextual, (int, float)) else 0.0
            base_total = 0.6 * ct + 0.4 * it

        # thresholding
        if base_total < score_threshold:
            # still allow if services hub or Tier1 — but only marginally below
            if not (_is_services_hub_or_child(href) or link.get("_whitelist_tier") == 1):
                continue

        # boosts
        boost = 0.0
        if _is_services_hub_or_child(href):
            boost += 0.30  # strong hub boost
        tier = link.get("_whitelist_tier") or 0
        if tier == 1:
            boost += 0.20
        elif tier == 2:
            boost += 0.10
        # slight negative boost for product catalogs when competing
        if "/products" in (urlparse(href).path or "").lower():
            boost -= 0.05

        final_score = max(0.0, min(1.0, base_total + boost))
        bucket_idx, bucket_name = _bucket_priority_for_url(href, buckets)

        candidates.append({
            "href": href,
            "final_score": final_score,
            "base_total": base_total,
            "intrinsic_score": intrinsic,
            "contextual_score": contextual,
            "bucket_idx": bucket_idx,
            "bucket": bucket_name,
            "path_len": _path_length(href),
            "matched_slugs": link.get("_matched_slugs", []),
            "selection_reason": _build_selection_reason(href, base_total, boost, bucket_name, link.get("_matched_slugs", [])),
        })

    # sort and select deterministically
    candidates.sort(key=lambda x: (
        -x["final_score"],
        x["bucket_idx"],
        x["path_len"],
        x["href"],
    ))

    selected: List[str] = []
    info_map: Dict[str, Dict[str, Any]] = {}
    for c in candidates:
        if len(selected) >= cap:
            break
        h = c["href"]
        if h in info_map:
            continue
        info_map[h] = c
        selected.append(h)

    return selected, info_map


def _build_selection_reason(href: str, base_total: float, boost: float, bucket: str, matched_slugs: List[str]) -> str:
    parts: List[str] = []
    parts.append(f"base={base_total:.3f}")
    if abs(boost) > 1e-6:
        parts.append(f"boost={boost:+.2f}")
    if bucket:
        parts.append(f"bucket={bucket}")
    if matched_slugs:
        parts.append(f"slugs={','.join(matched_slugs)}")
    return ";".join(parts)


def apply_blog_news_rule(
    pages: List[Dict[str, Any]],
    selection_info_map: Dict[str, Dict[str, Any]],
    *,
    contextual_threshold: float,
) -> List[Dict[str, Any]]:
    """Keep at most one blog/news page if strong signals; otherwise remove.

    Strong signals: contextual_score ≥ threshold and/or any matched_slugs.
    Non-blog/news pages are always kept.
    """
    kept: List[Dict[str, Any]] = []
    blog_kept = False
    for p in pages:
        url = (p.get("url") or "").lower()
        is_blog = "/blog" in url or "/news" in url
        if not is_blog:
            kept.append(p)
            continue
        if blog_kept:
            continue
        info = selection_info_map.get(p.get("url", ""), {})
        ctx = info.get("contextual_score")
        contextual_ok = isinstance(ctx, (int, float)) and float(ctx) >= contextual_threshold
        has_slug = bool(info.get("matched_slugs"))
        if contextual_ok or has_slug or p.get("detected_keywords"):
            kept.append(p)
            blog_kept = True
    return kept
