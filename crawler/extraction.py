"""
Purpose: Page extraction helpers using Crawl4AI outputs.
Description: Normalizes Crawl4AI results into page records with headings,
             keyword detection, and evidence snippets. Also supports
             DOM-scoped extraction using CSS selectors for unique page content.
Key Functions: extract_headings_simple, detect_keywords, build_evidence_snippets,
               scoped_markdown_from_html, make_page_record

AIDEV-NOTE: Keep logic deterministic and lightweight for MLS.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Sequence, Any
import re
import unicodedata
from urllib.parse import urlparse, urljoin
try:
    from bs4 import BeautifulSoup, Comment  # type: ignore
except Exception:  # pragma: no cover
    BeautifulSoup = None  # type: ignore
    Comment = None  # type: ignore


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


def clean_text(text: str) -> str:
    """Normalize control chars while preserving newlines/tabs/carriage returns."""
    if not text:
        return ""
    return "".join(
        ch for ch in unicodedata.normalize("NFKD", text)
        if unicodedata.category(ch)[0] != "C" or ch in ["\n", "\t", "\r"]
    )


def _emit_heading(tag_name: str, content: str) -> str:
    try:
        level = int(tag_name[1])
        level = max(1, min(level, 6))
    except Exception:
        level = 1
    text = re.sub(r"\s+", " ", content).strip()
    return ("#" * level) + " " + text + "\n"


def html2text(html: str, *, include_urls: bool = False, url: Optional[str] = None) -> str:
    """Convert HTML to readable markdown-like text with headings and links."""
    if not html or BeautifulSoup is None:
        return ""
    soup = BeautifulSoup(html, "html.parser")

    # Canonical override
    try:
        canonical_tag = soup.find("link", {"rel": "canonical"})
        if url and canonical_tag and canonical_tag.get("href"):
            url = canonical_tag["href"]
    except Exception:
        pass

    # Remove noise
    for s in soup(["code", "script", "style", "noscript"]):
        s.extract()
    if Comment is not None:
        try:
            comments = soup.find_all(string=lambda string: isinstance(string, Comment))
            for c in comments:
                c.extract()
        except Exception:
            pass

    # Normalize URL host
    if include_urls and url and not (url.startswith("http://") or url.startswith("https://")):
        url = "https://" + url

    def traverse(node) -> str:
        if node is None:
            return ""
        out = ""
        for child in getattr(node, "children", []):
            name = getattr(child, "name", None)
            if name is None:
                text = str(child).strip()
                if text:
                    text = re.sub(r"\s+", " ", text)
                    out += text
                continue
            name = name.lower()
            if name in {"h1", "h2", "h3", "h4", "h5", "h6"}:
                out += _emit_heading(name, child.get_text(" ").strip())
                continue
            if name == "button":
                btn_text = child.get_text().strip()
                href = child.get("href", "")
                onclick = child.get("onclick", "")
                if href or onclick:
                    out += f"[Button: {btn_text} href=\"{href}\" onclick=\"{onclick}\"]\n"
                else:
                    out += btn_text + "\n"
                continue
            if name == "a":
                href = child.get("href")
                label = child.get_text().strip()
                link_suffix = ""
                if include_urls and href:
                    try:
                        abs_href = href
                        if url:
                            abs_href = urljoin(url, href).split('#')[0].rstrip('/')
                        if not abs_href.startswith("javascript:void(0)"):
                            link_suffix = f"[{label}]({abs_href})"
                    except Exception:
                        link_suffix = label
                inner = traverse(child)
                out += (inner or label) + (link_suffix and (" " + link_suffix)) + "\n"
                continue
            if name == "img":
                alt_text = (child.get("alt") or "").strip()
                title_text = (child.get("title") or "").strip()
                src = (child.get("src") or "").strip()
                label = title_text or alt_text
                if src and not src.startswith("data:"):
                    try:
                        if url and (src.startswith('/') or not src.startswith(("http://", "https://"))):
                            src = urljoin(url, src)
                        src = urlparse(src)._replace(query="", fragment="").geturl()
                    except Exception:
                        pass
                    out += f"[Image: {label or src} ({src})]\n"
                elif label:
                    out += f"[Image: {label}]\n"
                continue
            child_text = traverse(child)
            if child_text:
                out += child_text + "\n"
        return out

    raw = traverse(soup)
    # Normalize indent by relative depth (approximation)
    lines = raw.split("\n")
    counts = set(len(line) - len(line.lstrip()) for line in lines)
    sorted_counts = sorted(counts)
    depth_map = {count: i for i, count in enumerate(sorted_counts)}
    norm = ""
    for line in lines:
        count = len(line) - len(line.lstrip())
        norm += (" " * depth_map.get(count, 0)) + line.lstrip() + "\n"
    cleaned = "\n".join(ln for ln in norm.split("\n") if ln.strip())
    return clean_text(cleaned)


def strip_links_from_markdown(text: str) -> str:
    """
    Remove links from markdown while preserving visible anchor text.

    AIDEV-NOTE: Applied only to `markdown_fit` to reduce noise for LLMs.
    - [text](url) -> text
    - ![alt](src) -> alt
    - <https://...> -> ''
    - bare https?://... -> ''
    - Drop trailing '## References' section if present
    """
    if not text:
        return ""
    # Inline images then links
    s = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r"\1", text)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", s)
    # Autolinks <http://...>
    s = re.sub(r"<https?://[^>]+>", "", s)
    # Bare URLs
    s = re.sub(r"https?://\S+", "", s)
    # Drop References section (if generator added citations-like block)
    s = re.sub(r"\n\n## References[\s\S]*$", "", s, flags=re.MULTILINE)
    return s


def strip_links_and_images_scoped(text: str) -> str:
    """
    Remove images and link remnants from scoped markdown.

    AIDEV-NOTE: Scoped content aims to be clean text-only for LLMs.
    - Drop custom image tokens like: [Image: label (src)]
    - Remove inline [Image: ...] occurrences
    - Remove markdown-style links and bare/angle URLs if present
    """
    if not text:
        return ""
    s = text
    # Remove whole lines that are only image tokens
    s = re.sub(r"^\s*\[Image:[^\]]*\]\s*$", "", s, flags=re.MULTILINE)
    # Remove inline image tokens
    s = re.sub(r"\[Image:[^\]]*\]", "", s)
    # Remove markdown images/links and bare URLs
    s = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r"\1", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", s)
    s = re.sub(r"<https?://[^>]+>", "", s)
    s = re.sub(r"https?://\S+", "", s)
    # Collapse any created multiple blank lines
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

def scoped_markdown_from_html(html: str, selectors: Sequence[str], base_url: Optional[str] = None) -> str:
    """
    Return markdown-like text extracted from the first DOM node matching any CSS selector.

    If BeautifulSoup is unavailable or no selector matches, returns an empty string.
    Fallback: convert <body>.
    """
    if not html or BeautifulSoup is None:
        return ""
    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception:
        return ""
    for sel in selectors or []:
        try:
            node = soup.select_one(sel)
        except Exception:
            node = None
        if node is not None:
            fragment_html = str(node)
            return html2text(fragment_html, include_urls=False, url=base_url)
    try:
        body = soup.body
        if body is not None:
            return html2text(str(body), include_urls=False, url=base_url)
    except Exception:
        pass
    return ""


def make_page_record(
    url: str,
    result: Any,
    *,
    keywords: Sequence[str],
    scoped_markdown: Optional[str] = None,
    emit_links: bool = False,
) -> Dict:
    """Normalize Crawl4AI result (object or dict) into a page record."""
    # Access helpers that work for both objects and dicts
    def _get(obj: Any, attr: str, default: Any = None) -> Any:
        if isinstance(obj, dict):
            return obj.get(attr, default)
        return getattr(obj, attr, default)

    md_obj = _get(result, "markdown") or {}
    md_raw = _get(md_obj, "raw_markdown", "") if md_obj else ""
    md_fit = _get(md_obj, "fit_markdown", "") if md_obj else ""
    if md_fit:
        # AIDEV-NOTE: Remove links from fit markdown only (keep raw for provenance)
        md_fit = strip_links_from_markdown(md_fit)
    # AIDEV-NOTE: Trimmed schema per decision — no cleaned_html or markdown_raw
    links = _get(result, "links", {}) or {}
    metadata = _get(result, "metadata", {}) or {}

    markdown_scoped = scoped_markdown or ""
    if markdown_scoped:
        # AIDEV-NOTE: Remove links and images from scoped markdown for minimal noise
        markdown_scoped = strip_links_and_images_scoped(markdown_scoped)
    markdown_raw = md_raw or ""
    # Derive signals from scoped content only
    signal_text = markdown_scoped
    headings = extract_headings_simple(signal_text)
    detected = detect_keywords(signal_text, keywords)
    evidence = build_evidence_snippets(signal_text, detected)

    # AIDEV-NOTE: Redact heavy `links` object from page records. If emit_links is
    # true, surface only minimal counts for internal/external links for debugging.
    internal_count = 0
    external_count = 0
    try:
        if isinstance(links, dict):
            li = links.get("internal") or []
            le = links.get("external") or []
            internal_count = len(li) if isinstance(li, list) else 0
            external_count = len(le) if isinstance(le, list) else 0
        elif hasattr(links, "internal") or hasattr(links, "external"):
            li = getattr(links, "internal", None)
            le = getattr(links, "external", None)
            internal_count = len(li) if isinstance(li, list) else 0
            external_count = len(le) if isinstance(le, list) else 0
        elif isinstance(links, list):
            # Treat plain list as internal-only when shape is ambiguous
            internal_count = len(links)
    except Exception:
        internal_count = internal_count or 0
        external_count = external_count or 0

    rec: Dict[str, Any] = {
        "url": url,
        "title": metadata.get("title"),
        "text_length": len(signal_text),
        "headings": headings,
        "detected_keywords": detected,
        "evidence_snippets": evidence,
        # New fields for side-by-side review
        "markdown_scoped": markdown_scoped,
        "markdown_raw": markdown_raw,
        # Backward-compat field retained for existing tooling
        "markdown_fit": md_fit,
    }
    if emit_links:
        rec["links_internal_count"] = int(internal_count)
        rec["links_external_count"] = int(external_count)
    return rec
