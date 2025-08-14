"""
Purpose: Evidence validation and normalization utilities for scorer outputs.
Description: Extracts header URLs from aggregated context, validates evidence URL membership and verbatim snippets,
             trims snippets to a configured length at sentence/word boundary, and deduplicates evidence items.
Key Functions/Classes: extract_header_urls, is_verbatim_snippet, trim_snippet, validate_and_normalize_evidence.
"""

from __future__ import annotations

import re
from typing import Iterable, List, Set, Tuple, Dict, Any


HEADER_PATTERN = re.compile(r"^### \[PAGE\] (\S+)\s*$", re.MULTILINE)


def extract_header_urls(aggregated_context: str) -> List[str]:
    """Return URLs from lines like: '### [PAGE] <url>' preserving order and removing duplicates.

    - Matches only at line start; trims trailing spaces.
    """
    seen: Set[str] = set()
    ordered: List[str] = []
    for match in HEADER_PATTERN.finditer(aggregated_context):
        url = match.group(1)
        if url not in seen:
            seen.add(url)
            ordered.append(url)
    return ordered


def is_verbatim_snippet(aggregated_context: str, snippet: str) -> bool:
    """Check that snippet is a verbatim substring of aggregated_context."""
    if not snippet:
        return False
    return snippet in aggregated_context


def trim_snippet(snippet: str, max_len: int = 320) -> str:
    """Trim snippet to <= max_len at a natural boundary.

    Priority: last sentence end punctuation (., !, ?), else last whitespace, else hard cut.
    """
    if len(snippet) <= max_len:
        return snippet
    slice_text = snippet[: max_len + 1]
    # Try sentence-ending punctuation within the window
    sentence_match = re.search(r"[.!?](?=[^.!?]*$)", slice_text)
    if sentence_match and sentence_match.end() <= max_len:
        return slice_text[: sentence_match.end()].strip()
    # Fallback to last whitespace
    last_space = slice_text.rfind(" ")
    if last_space > 0:
        return slice_text[:last_space].strip()
    # Hard cut
    return snippet[:max_len].strip()


def _dedup_items(items: Iterable[Tuple[str, str]]) -> List[Tuple[str, str]]:
    seen: Set[Tuple[str, str]] = set()
    ordered: List[Tuple[str, str]] = []
    for url, snip in items:
        key = (url, snip)
        if key in seen:
            continue
        seen.add(key)
        ordered.append(key)
    return ordered


def validate_and_normalize_evidence(
    aggregated_context: str,
    evidence_items: List[Dict[str, Any]],
    max_items: int = 3,
    max_snippet_len: int = 320,
) -> Tuple[List[Dict[str, str]], List[str]]:
    """Validate and normalize evidence according to PRD.

    - URL must be present in the aggregated headers
    - snippet must be a verbatim substring of aggregated_context
    - trim snippets to ~max_snippet_len at boundaries
    - deduplicate and cap to max_items

    Returns: (valid_normalized_items, errors)
    """
    header_urls = set(extract_header_urls(aggregated_context))

    normalized_pairs: List[Tuple[str, str]] = []
    errors: List[str] = []
    for idx, item in enumerate(evidence_items or []):
        raw_url = item.get("url")
        url = str(raw_url).strip() if raw_url is not None else ""
        snippet = str(item.get("snippet") or "").strip()
        if not url or not snippet:
            errors.append(f"evidence[{idx}] missing url/snippet")
            continue
        if url not in header_urls:
            errors.append(f"evidence[{idx}] url_not_in_headers: {url}")
            continue
        if not is_verbatim_snippet(aggregated_context, snippet):
            errors.append(f"evidence[{idx}] snippet_not_verbatim")
            continue
        normalized_pairs.append((url, trim_snippet(snippet, max_snippet_len)))

    deduped = _dedup_items(normalized_pairs)
    limited = deduped[:max_items]
    valid = [{"url": u, "snippet": s} for u, s in limited]
    return valid, errors


