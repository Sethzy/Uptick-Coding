"""
Purpose: Generate human-readable Markdown summaries for crawl runs.
Description: Reads domain-level records from a JSONL output file and renders a
             Markdown report with an overview table and per-domain details that
             mirror the `crawl-runs/<run>/output.md` example structure.
Key Functions: generate_markdown_report

AIDEV-NOTE: Keep formatting stable for downstream diffing and human review.
"""

from __future__ import annotations
from typing import Any, Dict, List, Sequence
import json
import os

from .reachability import load_domains_from_csv


def _safe_title(s: Any) -> str:
    if not isinstance(s, str) or not s.strip():
        return "(no title)"
    return s


def _content_sample(text: str, *, max_chars: int = 360) -> str:
    if not text:
        return ""
    s = text.strip().replace("\n", "\n")
    if len(s) <= max_chars:
        return s
    return s[:max_chars].rstrip() + "…"


def _domain_heading(run_dir: str) -> str:
    run_name = os.path.basename(run_dir.rstrip("/")) if run_dir else ""
    if run_name:
        return f"## {run_name} Crawl Results"
    return "## Crawl Results"


def _overview_table(records_by_domain: Dict[str, Dict], ordered_domains: Sequence[str]) -> List[str]:
    lines: List[str] = []
    lines.append("### Overview")
    lines.append("")
    lines.append("| Domain | Status | Reason | Pages | Canonical URL |")
    lines.append("| --- | --- | --- | --- | --- |")
    for domain in ordered_domains:
        rec = records_by_domain.get(domain)
        if rec is None:
            continue
        status = rec.get("crawler_status", "")
        reason = rec.get("crawler_reason", "") or ""
        pages = int(rec.get("crawl_pages_visited", 0) or 0)
        can = rec.get("canonical_url", "") or ""
        lines.append(f"| {domain} | {status} | {reason} | {pages} | {can} |")
    lines.append("")
    return lines


def _per_domain_details(records_by_domain: Dict[str, Dict], ordered_domains: Sequence[str]) -> List[str]:
    out: List[str] = []
    for domain in ordered_domains:
        rec = records_by_domain.get(domain)
        if rec is None:
            continue
        out.append("")
        out.append(f"### {domain}")
        status = rec.get("crawler_status", "")
        reason = rec.get("crawler_reason", "")
        if not reason:
            reason_pretty = "-"
        else:
            reason_pretty = str(reason)
        pages_visited = int(rec.get("crawl_pages_visited", 0) or 0)
        canonical_url = rec.get("canonical_url", "") or ""
        crawl_ts = rec.get("crawl_ts", "") or ""
        out.append("")
        out.append(f"- **status**: {status}")
        out.append(f"- **reason**: {reason_pretty}")
        out.append(f"- **pages_visited**: {pages_visited}")
        out.append(f"- **canonical_url**: {canonical_url}")
        out.append(f"- **crawl_ts**: {crawl_ts}")

        pages = rec.get("pages", []) or []
        if not isinstance(pages, list) or len(pages) == 0:
            continue

        for idx, p in enumerate(pages, start=1):
            url = p.get("url", "") or ""
            title = _safe_title(p.get("title"))
            text_len = int(p.get("text_length", 0) or 0)
            headings = p.get("headings") or []
            md_scoped = p.get("markdown_scoped") or ""
            md_raw = p.get("markdown_raw") or ""
            out.append(f"  - Page {idx}: {url}")
            out.append(f"    - title: {title}")
            out.append(f"    - text_length: {text_len}")
            if isinstance(headings, list) and len(headings) > 0:
                joined = ", ".join(str(h) for h in headings if isinstance(h, str) and h.strip())
                if joined:
                    out.append(f"    - headings: {joined}")
            scoped_sample = _content_sample(md_scoped)
            raw_sample = _content_sample(md_raw)
            if scoped_sample:
                out.append(f"    - content_sample_scoped: {scoped_sample}")
            if raw_sample:
                out.append(f"    - content_sample_raw: {raw_sample}")
    return out


def generate_markdown_report(output_jsonl_path: str, input_csv_path: str) -> str:
    """
    Render a Markdown report from the JSONL domain records and write it next to
    the JSONL file as `raw-output.md`. Returns the path to the written Markdown.
    """
    run_dir = os.path.dirname(os.path.abspath(output_jsonl_path))
    md_path = os.path.join(run_dir, "raw-output.md")

    # Load all records keyed by domain
    records_by_domain: Dict[str, Dict] = {}
    try:
        with open(output_jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                domain = rec.get("domain")
                if isinstance(domain, str) and domain:
                    records_by_domain[domain] = rec
    except FileNotFoundError:
        # Nothing to do
        return md_path

    # Preserve input order; append any extra domains not present in input at the end
    ordered_domains: List[str] = []
    try:
        ordered_domains = load_domains_from_csv(input_csv_path)
    except Exception:
        # Fallback to encountered order
        ordered_domains = list(records_by_domain.keys())
    else:
        extras = [d for d in records_by_domain.keys() if d not in ordered_domains]
        ordered_domains = ordered_domains + extras

    # Build Markdown
    lines: List[str] = []
    lines.append("<!--")
    lines.append("/**")
    lines.append(" * Purpose: Human-readable summary of batch raw-output.jsonl")
    lines.append(" * Description: Summarizes domain crawl outcomes and key page data for quick verification.")
    lines.append(" * Key Sections: Overview table; Per-domain details")
    lines.append(" */")
    lines.append("-->")
    lines.append("")
    lines.append(_domain_heading(run_dir))
    lines.append("")
    lines.extend(_overview_table(records_by_domain, ordered_domains))
    lines.extend(_per_domain_details(records_by_domain, ordered_domains))
    content = "\n".join(lines).rstrip() + "\n"

    # Write file atomically
    tmp = f"{md_path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(content)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, md_path)
    return md_path


