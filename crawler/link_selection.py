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


def _fold_www(host: str) -> str:
    h = (host or "").lower()
    return h[4:] if h.startswith("www.") else h


def _same_site(base_url: str, href: str) -> bool:
    try:
        b = urlparse(base_url)
        u = urlparse(urljoin(base_url, href))
        if u.scheme not in {"http", "https"}:
            return False
        return _fold_www(b.netloc) == _fold_www(u.netloc)
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
    "design", "monitoring",
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


def _query_contains_services(url: str) -> bool:
    try:
        q = urlparse(url).query.lower()
    except Exception:
        return False
    if not q:
        return False
    return ("service=" in q) or ("services=" in q) or ("=service" in q) or ("=services" in q) or ("services" in q and "page" in q)


def _title_or_anchor_services(link: Dict[str, Any]) -> bool:
    title = (((link.get("head_data") or {}).get("title")) or "").lower()
    text = (link.get("text") or "").lower()
    return ("services" in title) or ("services" in text)


def _match_whitelist_in_title_or_anchor(link: Dict[str, Any]) -> Tuple[Optional[str], int]:
    title = (((link.get("head_data") or {}).get("title")) or "").lower()
    text = (link.get("text") or "").lower()
    for s in _WHITELIST_TIER1:
        if s in title or s in text:
            return s, 1
    for s in _WHITELIST_TIER2:
        if s in title or s in text:
            return s, 2
    return None, 0


def _path_length(url: str) -> int:
    return len(_path_segments(url))


def _is_contact_page(link: Dict[str, Any]) -> bool:
    """Detect generic contact pages by URL path/query, title, or anchor text.

    AIDEV-NOTE: We avoid over-broad matches (e.g., plain 'quote'). Penalize
    classic contact endpoints like '/contact', 'contact_us', 'contact-us',
    and CTA equivalents like 'get-a-quote' or 'request-quote'.
    """
    href = (link.get("href") or link.get("url") or "").lower()
    try:
        u = urlparse(href)
        path_q = f"{u.path or ''}?{u.query or ''}"
    except Exception:
        path_q = href
    title = (((link.get("head_data") or {}).get("title")) or "").lower()
    text = (link.get("text") or "").lower()
    needles = ["/contact", "contact_us", "contact-us", "get-a-quote", "request-quote"]
    def contains_contact(s: str) -> bool:
        s = s or ""
        return any(n in s for n in needles)
    return contains_contact(path_q) or contains_contact(title) or contains_contact(text)


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
        # Trust Crawl4AI internal classification; do not re-drop here
        # dedupe by normalized href
        if href in seen:
            continue
        seen.add(href)

        # hard exclude service-area
        if _is_service_area(link):
            continue

        # detect whitelist slugs from URL, title, or anchor
        slug_url, tier_url = _match_whitelist_slug(href)
        slug_txt, tier_txt = _match_whitelist_in_title_or_anchor(link)
        tier = max(tier_url, tier_txt)
        slug = slug_url or slug_txt
        link["_matched_slugs"] = [slug] if slug else []
        link["_whitelist_tier"] = tier

        # services-intent detection
        services_hub_signal = _is_services_hub_or_child(href) or _query_contains_services(href) or _title_or_anchor_services(link)
        # Stronger signal: exact 'services' anchor or title
        title = (((link.get("head_data") or {}).get("title")) or "").strip().lower()
        text = (link.get("text") or "").strip().lower()
        if text == "services" or title == "services" or "\nservices\n" in text:
            services_hub_signal = True

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

        # thresholding (bypass for confirmed services hub or Tier1 via any channel)
        if base_total < score_threshold and not (services_hub_signal or link.get("_whitelist_tier") == 1):
            # Skip adding this candidate
            continue

        # boosts
        boost = 0.0
        if services_hub_signal:
            boost += 0.30  # strong hub boost, inferred by path/query/title/anchor
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
            "_services_intent": services_hub_signal or (tier > 0),
        })

    # sort and select deterministically (prefer services intent in tie situations)
    candidates.sort(key=lambda x: (
        -x["final_score"],
        0 if x.get("_services_intent") else 1,
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

    # Deterministic backfill if under cap
    if len(selected) < cap:
        remaining = [c for c in candidates if c["href"] not in info_map]
        # prefer remaining services-intent first
        remaining.sort(key=lambda x: (
            0 if x.get("_services_intent") else 1,
            x["bucket_idx"],
            x["path_len"],
            x["href"],
        ))
        for c in remaining:
            if len(selected) >= cap:
                break
            h = c["href"]
            info = info_map.get(h) or dict(c)
            info["selection_reason"] = (info.get("selection_reason") or "") + (";" if info.get("selection_reason") else "") + ("backfill:" + info.get("bucket", ""))
            info_map[h] = info
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
