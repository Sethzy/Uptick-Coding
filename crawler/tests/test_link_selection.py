from crawler.link_selection import rank_links_by_priority, select_top_links

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
