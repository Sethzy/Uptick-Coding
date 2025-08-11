"""
Purpose: Page extraction helpers using Crawl4AI outputs.
Description: Normalizes Crawl4AI results into page records with headings,
             keyword detection, and evidence snippets.
Key Functions: extract_headings_simple, detect_keywords, build_evidence_snippets,
               make_page_record

AIDEV-NOTE: Keep logic deterministic and lightweight for MLS.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Sequence
import re


_HEADING_RE = re.compile(r"^\s{0,3}(?:#{1,6}|\*\s|\d+\.)\s*(.+)$")


def extract_headings_simple(markdown: str) -> List[str]:
    headings: List[str] = []
    for line in markdown.splitlines():
        m = _HEADING_RE.match(line)
        if m:
            h = m.group(1).strip()
            if h:
                headings.append(h)
    return headings[:12]


def detect_keywords(text: str, keywords: Sequence[str]) -> List[str]:
    found: List[str] = []
    low = text.lower()
    for kw in keywords:
        if kw.lower() in low:
            found.append(kw)
    return found


def build_evidence_snippets(text: str, keywords: Sequence[str], *, window: int = 240, max_snippets: int = 2) -> List[str]:
    low = text.lower()
    out: List[str] = []
    for kw in keywords:
        k = kw.lower()
        idx = low.find(k)
        if idx == -1:
            continue
        start = max(0, idx - window // 2)
        end = min(len(text), start + window)
        snippet = text[start:end].strip()
        if snippet and snippet not in out:
            out.append(snippet)
        if len(out) >= max_snippets:
            break
    return out


def make_page_record(url: str, result: Dict, *, keywords: Sequence[str]) -> Dict:
    md_raw = (result.get("markdown") or {}).get("raw_markdown") or ""
    md_fit = (result.get("markdown") or {}).get("fit_markdown") or ""
    cleaned_html = result.get("cleaned_html") or ""
    links = result.get("links") or {}
    metadata = result.get("metadata") or {}

    md_text = md_fit or md_raw or ""
    headings = extract_headings_simple(md_text)
    detected = detect_keywords(md_text, keywords)
    evidence = build_evidence_snippets(md_text, detected)

    return {
        "url": url,
        "title": metadata.get("title"),
        "language": metadata.get("language"),
        "render_mode": "browser",
        "text_length": len(md_text),
        "headings": headings,
        "detected_keywords": detected,
        "evidence_snippets": evidence,
        "markdown_raw": md_raw,
        "markdown_fit": md_fit,
        "cleaned_html": cleaned_html,
        "links": links,
    }
