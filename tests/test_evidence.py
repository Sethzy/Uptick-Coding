"""
Purpose: Unit tests for evidence extraction and validation.
Description: Covers URL header extraction, verbatim checks, trimming behavior, deduplication, and error reporting.
Key Tests: test_extract_header_urls, test_validate_success, test_validate_errors, test_trim_boundaries.
"""

from __future__ import annotations

from scoring.evidence import (
    extract_header_urls,
    is_verbatim_snippet,
    trim_snippet,
    validate_and_normalize_evidence,
)


def _ctx() -> str:
    return (
        "### [PAGE] https://a.com\n"
        "A alpha.\n\n\n"
        "### [PAGE] https://a.com/services\n"
        "We provide fire sprinklers and alarms installation and inspections.\n"
    )


def test_extract_header_urls():
    urls = extract_header_urls(_ctx())
    assert urls == ["https://a.com", "https://a.com/services"]


def test_is_verbatim_snippet():
    assert is_verbatim_snippet(_ctx(), "A alpha.")
    assert not is_verbatim_snippet(_ctx(), "A alpha..")


def test_validate_success():
    ev = [
        {"url": "https://a.com/services", "snippet": "We provide fire sprinklers and alarms installation and inspections."}
    ]
    valid, errors = validate_and_normalize_evidence(_ctx(), ev, max_items=3, max_snippet_len=320)
    assert errors == []
    assert len(valid) == 1
    assert valid[0]["url"].endswith("/services")


def test_validate_errors():
    ev = [
        {"url": "https://b.com", "snippet": "We provide"},  # wrong domain
        {"url": "https://a.com/services", "snippet": "not present"},  # not verbatim
        {"url": "", "snippet": ""},  # missing
    ]
    valid, errors = validate_and_normalize_evidence(_ctx(), ev, max_items=3, max_snippet_len=50)
    assert len(valid) == 0
    assert len(errors) == 3


def test_trim_boundaries():
    long_snip = "This is a very long sentence that should be trimmed nicely at some point without breaking words. " * 10
    trimmed = trim_snippet(long_snip, max_len=80)
    assert len(trimmed) <= 80
    # Should end at whitespace or punctuation rather than in the middle of a word
    assert trimmed[-1] in ".!? "


