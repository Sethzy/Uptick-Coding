"""
Purpose: Link discovery, filtering, ranking, and selection logic for the crawler.
Description: Provides helpers to identify internal links, extract anchors from
             HTML, and apply deterministic rule-first ranking and selection.
Key Functions: is_internal_link,
               extract_anchors_from_html,
               select_links_with_scoring,
               apply_blog_news_rule,
               select_links_simple

AIDEV-NOTE: Deterministic sorting is critical. Tie-breakers are bucket order
            (as provided by config), then path length, then URL lexicographic.
"""

from __future__ import annotations
from typing import Any, Dict, Iterable, List, Sequence, Tuple, Optional
from urllib.parse import urljoin, urlparse
import re

try:
    from bs4 import BeautifulSoup  # type: ignore
except Exception:  # pragma: no cover
    BeautifulSoup = None  # type: ignore


# -------------------- Core helpers --------------------

def is_internal_link(base: str, href: str) -> bool:
    """
    Return True if href resolves to the same origin as base (http/https only).

    Args:
        base: Absolute base URL (e.g., "https://acme.com").
        href: Possibly relative or absolute link to test.

    Returns:
        True when the resolved URL has the same netloc and an http/https scheme.

    Example:
        >>> is_internal_link("https://acme.com", "/services")
        True
        >>> is_internal_link("https://acme.com", "https://example.org/about")
        False
    """
    try:
        b = urlparse(base)
        u = urlparse(urljoin(base, href))
        return (u.netloc == b.netloc) and (u.scheme in {"http", "https"})
    except Exception:
        return False


def _normalize_url_for_match(url: str) -> str:
    """Lowercase, strip trailing slash for stable substring checks."""
    try:
        u = urlparse(url)
        path = (u.path or "/").lower().rstrip("/")
        q = (u.query or "").lower()
        return path + (f"?{q}" if q else "")
    except Exception:
        s = (url or "").lower().rstrip("/")
        return s


def _text_fields_lower(link: Dict[str, Any]) -> Tuple[str, str]:
    title = (((link.get("head_data") or {}).get("title")) or "").strip().lower()
    text = (link.get("text") or "").strip().lower()
    return title, text


def _path_length(url: str) -> int:
    try:
        p = urlparse(url).path or "/"
        return len([seg for seg in p.split("/") if seg])
    except Exception:
        return 0


def _is_service_area(link: Dict[str, Any]) -> bool:
    """Heuristics to drop city/region service-area pages from targeted crawl.

    Rules tightened to avoid conflict with `/services` and false positives like
    `/areas-of-expertise`:
    - Only match when the FIRST path segment is one of the known area prefixes
      (e.g., `service-areas`, `locations`, `regions`, etc.)
    - Remove generic `/areas` token to avoid substring collisions
    - Keep text-based hints as a fallback
    
    Args:
        link: Dict with at least `href` and optional `text`.

    Returns:
        True if the URL/text indicates a service-area landing.
    """
    href = (link.get("href") or link.get("url") or "").lower()
    text = (link.get("text") or "").lower()
    try:
        u = urlparse(href)
        segs = [s for s in (u.path or "/").lower().strip("/").split("/") if s]
        first = segs[0] if segs else ""
    except Exception:
        first = ""
    area_prefixes = {
        "service-area",
        "service-areas",
        "servicearea",
        "areas-we-serve",
        "locations",
        "location",
        "territories",
        "coverage",
        "where-we-work",
        "region",
        "regions",
    }
    if first in area_prefixes:
        return True
    if "service area" in text or "areas we serve" in text:
        return True
    return False


# Whitelists for strong service intent
_WHITELIST_TIER1: Sequence[str] = (
    # A/B absolute terms (exact per spec)
    "installation",
    "install",
    "maintenance",
    "inspection",
    "protection",
)

_WHITELIST_TIER2: Sequence[str] = (
    # U URL service terms (exact per spec)
    "fire",
    "alarm",
    "testing",
    "extinguishers",
    "repair",
    "system",
    "design",
    "monitoring",
    "commissioning",
    "commission",
)


def _category_for_link(href: str, link: Dict[str, Any]) -> Tuple[str, int, bool, str]:
    """
    Determine rule-first category and base score:
    A: /services (base 80; +20 boost if absolute term also in URL)
    B: absolute TIER1 terms in URL (base 85)
    C: /about (base 75)
    U: TIER2 terms in URL (base 60)
    T: 'services' in text or absolute term in text (base 50)
    D: other (base 0)
    Returns (category, base_score, a_only_boost_applies, matched_term)
    
    Args:
        href: Absolute URL for the link being classified.
        link: Original link dict with optional `text` and `head_data.title`.

    Returns:
        Tuple of (category, base score, A-only boost flag, matched term for audit).
    """
    low = _normalize_url_for_match(href)
    title, text = _text_fields_lower(link)
    absolute_terms = set(_WHITELIST_TIER1)
    url_service_terms = set(_WHITELIST_TIER2)
    if low.startswith("/services"):
        matched = next((t for t in absolute_terms if t in low), None)
        return "A", 80, bool(matched), matched or ""
    matched = next((t for t in absolute_terms if t in low), None)
    if matched:
        return "B", 85, False, matched
    if low.startswith("/about"):
        return "C", 75, False, ""
    matched = next((t for t in url_service_terms if t in low), None)
    if matched:
        return "U", 60, False, matched
    if ("services" in title) or ("services" in text):
        return "T", 50, False, "services"
    matched = next((t for t in absolute_terms if t in title or t in text), None)
    if matched:
        return "T", 50, False, matched
    return "D", 0, False, ""


# -------------------- Simple selection (rule-first; no contextual weight) --------------------

def select_links_simple(
    internal_links: Sequence[Dict[str, Any]],
    *,
    base_url: str,
    cap: int,
    disallowed_paths: Sequence[str] | None = None,
) -> Tuple[List[str], Dict[str, Dict[str, Any]]]:
    """
    Deterministic selector using rule-first categories only (no contextual score).
    Sort by final_score desc, path_len asc, href asc.

    Args:
        internal_links: Links from Crawl4AI (list of dicts with `href`/`url`, `text`).
        base_url: Canonical homepage used for internal filtering and normalization.
        cap: Maximum number of links to return.
        disallowed_paths: Paths to be excluded (prefix match), e.g. ["/privacy"].

    Returns:
        (selected_hrefs, selection_info_map). The map includes category, base,
        a_boost, final_score, path_len, matched_slugs, selection_reason.

    Example:
        >>> select_links_simple([{"href": "/services"}], base_url="https://acme.com", cap=3)
        (['https://acme.com/services'], {...})
    """
    disallowed_paths = tuple(disallowed_paths or ())

    def _norm_href(x: Any) -> str:
        if isinstance(x, str):
            return x
        if isinstance(x, dict):
            return x.get("url") or x.get("href") or ""
        h = getattr(x, "url", None) or getattr(x, "href", None)
        return h if isinstance(h, str) else ""

    def _norm(u: str) -> str:
        return (u or "").rstrip("/")

    homepage = _norm(base_url)
    seen: set[str] = set()
    candidates: List[Dict[str, Any]] = []
    for link in internal_links:
        href = _norm_href(link)
        if not href:
            continue
        try:
            if not is_internal_link(base_url, href):
                continue
            u = urlparse(urljoin(base_url, href))
            path = u.path or "/"
            if any(path.startswith(p) for p in disallowed_paths):
                continue
        except Exception:
            continue
        abs_href = u.geturl()
        if _norm(abs_href) == homepage:
            continue
        if abs_href in seen:
            continue
        seen.add(abs_href)
        if _is_service_area({"href": abs_href, "text": link.get("text", "")} if isinstance(link, dict) else {"href": abs_href, "text": ""}):
            continue
        category, base_score, a_boost_flag, matched_term = _category_for_link(abs_href, link if isinstance(link, dict) else {})
        a_boost = 20 if (category == "A" and a_boost_flag) else 0
        final_score = base_score + a_boost
        candidates.append({
            "href": abs_href,
            "category": category,
            "base": base_score,
            "a_boost": a_boost,
            "final_score": final_score,
            "path_len": _path_length(abs_href),
            "matched_slugs": [matched_term] if matched_term else [],
            "selection_reason": f"category={category};base={base_score};a_boost={('+' if a_boost>0 else '')}{a_boost};path_len={_path_length(abs_href)}",
        })

    candidates.sort(key=lambda x: (-x["final_score"], x["path_len"], x["href"]))
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


# -------------------- HTML anchor extraction helpers --------------------

def filter_internal_links(base: str, hrefs: Iterable[str], disallowed_paths: Sequence[str]) -> List[str]:
    """
    Normalize and return unique absolute internal URLs from raw href strings.

    Args:
        base: Base URL to resolve against.
        hrefs: Raw href strings extracted from HTML.
        disallowed_paths: Paths to exclude (prefix match).

    Returns:
        Deduplicated list of absolute internal URLs.
    """
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
    seen = set()
    uniq: List[str] = []
    for u in out:
        if u not in seen:
            seen.add(u)
            uniq.append(u)
    return uniq

def extract_anchors_from_html(base_url: str, html: str, disallowed_paths: Sequence[str]) -> List[str]:
    """
    Extract internal anchor hrefs from HTML, normalize to absolute, filter and dedupe.

    Args:
        base_url: Base URL for resolving relative hrefs.
        html: Rendered HTML string.
        disallowed_paths: Paths to exclude (prefix match).

    Returns:
        Deduplicated list of absolute internal URLs discovered via <a href>.
    """
    if not html or BeautifulSoup is None:
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


# -------------------- Rule-first selection with diagnostics --------------------

def _matched_whitelist_slugs(url_or_text: str) -> List[str]:
    low = url_or_text.lower()
    found: List[str] = []
    for t in list(_WHITELIST_TIER1) + list(_WHITELIST_TIER2):
        if t in low and t not in found:
            found.append(t)
    return found

def select_links_with_scoring(
    internal_links: Sequence[Dict[str, Any]],
    *,
    base_url: str,
    cap: int,
    disallowed_paths: Optional[Sequence[str]] = None,
) -> Tuple[List[str], Dict[str, Dict[str, Any]]]:
    """
    Rule-first selector variant that also records selection diagnostics.

    Note: Contextual/intrinsic scores and bucket priorities are ignored.

    Args:
        internal_links: Link dicts (href/url, text, optional head_data).
        base_url: Canonical homepage used for internal filtering and normalization.
        cap: Maximum links to select.
        disallowed_paths: Paths to exclude.

    Returns:
        (selected_hrefs, info_map) with deterministic ordering and selection reasons.
    """
    disallowed_paths = tuple(disallowed_paths or ())

    def _norm_href(x: Any) -> str:
        if isinstance(x, str):
            return x
        if isinstance(x, dict):
            return x.get("url") or x.get("href") or ""
        h = getattr(x, "url", None) or getattr(x, "href", None)
        return h if isinstance(h, str) else ""

    def _norm(u: str) -> str:
        return (u or "").rstrip("/")

    homepage = _norm(base_url)
    seen: set[str] = set()
    candidates: List[Dict[str, Any]] = []

    for link in internal_links:
        href = _norm_href(link)
        if not href:
            continue
        try:
            if not is_internal_link(base_url, href):
                continue
            u = urlparse(urljoin(base_url, href))
            path = u.path or "/"
            if any(path.startswith(p) for p in disallowed_paths):
                continue
        except Exception:
            continue
        abs_href = u.geturl()
        if _norm(abs_href) == homepage:
            continue
        if abs_href in seen:
            continue
        seen.add(abs_href)
        if _is_service_area({"href": abs_href, "text": link.get("text", "")} if isinstance(link, dict) else {"href": abs_href, "text": ""}):
            continue

        # Rule-first scoring only: category base + A-only boost
        category, base_score, a_boost_flag, _cat_term = _category_for_link(abs_href, link if isinstance(link, dict) else {})
        a_boost = 20 if (category == "A" and a_boost_flag) else 0
        final_score = base_score + a_boost

        # Whitelist-driven allowlist for top-level non-hub routes
        path_len = _path_length(abs_href)
        matched_slugs = list({_s for _s in (
            *_matched_whitelist_slugs(abs_href), *_matched_whitelist_slugs((link.get("text") or "") if isinstance(link, dict) else "")
        ) if _s})
        is_top_level = path_len == 1
        is_services_hub = path.startswith("/services")
        if is_top_level and not is_services_hub and not matched_slugs:
            # AIDEV-NOTE: Drop generic top-level routes like /solutions unless whitelisted
            continue

        candidates.append({
            "href": abs_href,
            "final_score": float(final_score),
            "path_len": path_len,
            "matched_slugs": matched_slugs,
            "selection_reason": f"score={final_score:.3f};path_len={path_len};matched={','.join(matched_slugs)}",
        })

    candidates.sort(key=lambda x: (-x["final_score"], x["path_len"], x["href"]))
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


def apply_blog_news_rule(pages: Sequence[Dict[str, Any]], selection_info_map: Dict[str, Dict[str, Any]], *, contextual_threshold: float = 0.0) -> List[Dict[str, Any]]:
    """
    Keep at most one blog/news page, requiring matched whitelist slugs;
    ignore contextual scoring.

    Args:
        pages: Page records as produced by make_page_record.
        selection_info_map: Diagnostics produced during selection.
        contextual_threshold: Ignored (retained for signature stability).

    Returns:
        Filtered list of page records with at most one blog/news page.
    """
    kept: List[Dict[str, Any]] = []
    blog_kept = False
    for p in pages:
        url = p.get("url") or ""
        low = url.lower()
        is_blog = "/blog" in low or "/news" in low
        if not is_blog:
            kept.append(p)
            continue
        info = selection_info_map.get(url, {})
        # AIDEV-NOTE: Ignore contextual; rely on whitelist slugs only
        has_slug = bool(info.get("matched_slugs"))
        if not blog_kept and has_slug:
            kept.append(p)
            blog_kept = True
    return kept
