from crawler.extraction import extract_headings_simple, detect_keywords, build_evidence_snippets


def test_extract_headings_simple():
    md = """
# Title
Some text
## Section
- item
### Subsection
"""
    heads = extract_headings_simple(md)
    assert heads[:2] == ["Title", "Section"]


def test_detect_keywords_and_snippets():
    text = "Fire sprinkler systems are part of fire protection services including alarm monitoring."
    kws = ["fire sprinkler", "alarm monitoring", "suppression"]
    found = detect_keywords(text, kws)
    assert set(found) >= {"fire sprinkler", "alarm monitoring"}
    snippets = build_evidence_snippets(text, found, window=60)
    assert len(snippets) >= 1
