from crawler.link_selection import (
    rank_links_by_priority,
    select_top_links,
    select_links_with_scoring,
    apply_blog_news_rule,
)
from urllib.parse import urlparse

BUCKETS = [
    {"name": "services", "patterns": ["/services", "/capabilities"]},
    {"name": "industries", "patterns": ["/industries", "/markets"]},
    {"name": "about", "patterns": ["/about", "/company"]},
]


def test_rank_and_select_links():
    links = [
        "https://acme.com/industries",
        "https://acme.com/privacy",
        "https://acme.com/about",
        "https://acme.com/services",
        "https://acme.com/contact",
    ]
    ranked = rank_links_by_priority(links, BUCKETS)
    selected = select_top_links(ranked, 2)
    assert selected[0].endswith('/services')
    assert selected[1].endswith('/industries') or selected[1].endswith('/about')


def _mk_link(url: str, text: str = "", intrinsic: float | None = None, contextual: float | None = None, total: float | None = None):
    return {
        "href": url,
        "text": text,
        "intrinsic_score": intrinsic,
        "contextual_score": contextual,
        "total_score": total,
    }


def test_scoring_selection_hard_exclude_service_area_and_whitelist():
    base = "https://acme.com"
    buckets = BUCKETS
    links = [
        _mk_link("https://acme.com/service-area/phoenix", "Phoenix"),  # hard exclude
        _mk_link("https://acme.com/services/inspections", "Inspections", intrinsic=8.0, contextual=0.5),  # hub child
        _mk_link("https://acme.com/inspections", "Inspections", intrinsic=6.0, contextual=0.6),  # top-level whitelisted
        _mk_link("https://acme.com/solutions", "Solutions", intrinsic=7.0, contextual=0.1),  # top-level non-whitelisted
    ]
    selected, info = select_links_with_scoring(links, base_url=base, buckets=buckets, cap=4, score_threshold=0.2)
    hrefs = set(selected)
    assert "https://acme.com/service-area/phoenix" not in hrefs
    assert "https://acme.com/solutions" not in hrefs  # not whitelisted
    assert "https://acme.com/services/inspections" in hrefs
    assert "https://acme.com/inspections" in hrefs


def test_scoring_selection_deterministic_tie_breakers():
    base = "https://acme.com"
    buckets = BUCKETS
    # Two links with equal final score; tie-break by bucket, then path length, then URL
    a = _mk_link("https://acme.com/about", "About", intrinsic=7.0, contextual=0.5, total=0.6)
    b = _mk_link("https://acme.com/services/install", "Install", intrinsic=7.0, contextual=0.5, total=0.6)
    c = _mk_link("https://acme.com/industries", "Industries", intrinsic=7.0, contextual=0.5, total=0.6)
    sel1, _ = select_links_with_scoring([a, b, c], base_url=base, buckets=buckets, cap=3, score_threshold=0.0)
    sel2, _ = select_links_with_scoring([c, a, b], base_url=base, buckets=buckets, cap=3, score_threshold=0.0)
    assert sel1 == sel2  # stable outcome regardless of input order


def test_blog_news_rule():
    pages = [
        {"url": "https://acme.com/services/inspections", "detected_keywords": ["inspection"]},
        {"url": "https://acme.com/blog/new-inspection-standard", "detected_keywords": []},
        {"url": "https://acme.com/news/award", "detected_keywords": []},
    ]
    # Map contextual score and slugs to only allow one blog/news
    info = {
        "https://acme.com/blog/new-inspection-standard": {"contextual_score": 0.5, "matched_slugs": ["inspection"]},
        "https://acme.com/news/award": {"contextual_score": 0.1, "matched_slugs": []},
    }
    kept = apply_blog_news_rule(pages, info, contextual_threshold=0.3)
    urls = [p["url"] for p in kept]
    assert "https://acme.com/blog/new-inspection-standard" in urls
    assert "https://acme.com/news/award" not in urls
