from crawler.link_selection import (
    select_links_simple,
    select_links_with_scoring,
    apply_blog_news_rule,
)
from urllib.parse import urlparse

def test_simple_selection_orders_services_over_about_and_drops_disallowed():
    base = "https://acme.com"
    links = [
        {"href": "https://acme.com/privacy"},  # disallowed
        {"href": "https://acme.com/about"},    # C (75)
        {"href": "https://acme.com/services"}, # A (80)
    ]
    selected, _ = select_links_simple(links, base_url=base, cap=2, disallowed_paths=["/privacy"])
    assert selected[0].endswith('/services')
    assert selected[1].endswith('/about')


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
    links = [
        _mk_link("https://acme.com/service-area/phoenix", "Phoenix"),  # hard exclude
        _mk_link("https://acme.com/services/inspections", "Inspections", intrinsic=8.0, contextual=0.5),  # hub child
        _mk_link("https://acme.com/inspections", "Inspections", intrinsic=6.0, contextual=0.6),  # top-level whitelisted
        _mk_link("https://acme.com/solutions", "Solutions", intrinsic=7.0, contextual=0.1),  # top-level non-whitelisted
    ]
    selected, info = select_links_with_scoring(links, base_url=base, cap=4)
    hrefs = set(selected)
    assert "https://acme.com/service-area/phoenix" not in hrefs
    assert "https://acme.com/solutions" not in hrefs  # not whitelisted
    assert "https://acme.com/services/inspections" in hrefs
    assert "https://acme.com/inspections" in hrefs


def test_scoring_selection_deterministic_tie_breakers():
    base = "https://acme.com"
    # Stability regardless of input order
    a = _mk_link("https://acme.com/about", "About")  # C (75)
    b = _mk_link("https://acme.com/services/install", "Install")  # A (80) +20 boost -> 100
    c = _mk_link("https://acme.com/industries", "Industries")  # D (0)
    sel1, _ = select_links_with_scoring([a, b, c], base_url=base, cap=3)
    sel2, _ = select_links_with_scoring([c, a, b], base_url=base, cap=3)
    assert sel1 == sel2  # stable outcome regardless of input order


def test_blog_news_rule():
    pages = [
        {"url": "https://acme.com/services/inspections", "detected_keywords": ["inspection"]},
        {"url": "https://acme.com/blog/new-inspection-standard", "detected_keywords": []},
        {"url": "https://acme.com/news/award", "detected_keywords": []},
    ]
    # Map slugs to only allow one blog/news
    info = {
        "https://acme.com/blog/new-inspection-standard": {"matched_slugs": ["inspection"]},
        "https://acme.com/news/award": {"matched_slugs": []},
    }
    kept = apply_blog_news_rule(pages, info)
    urls = [p["url"] for p in kept]
    assert "https://acme.com/blog/new-inspection-standard" in urls
    assert "https://acme.com/news/award" not in urls
