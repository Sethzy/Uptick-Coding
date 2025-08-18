from crawler.extraction import extract_headings_simple


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
