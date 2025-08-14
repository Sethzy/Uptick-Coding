"""
Purpose: Generate human-readable Markdown summaries for aggregated context runs.
Description: Reads aggregated per-domain JSONL records (domain, aggregated_context,
             included_urls, overflow, length) and renders a concise Markdown report
             with an overview table and per-domain details. This version assumes the
             new Aggregated Context Builder output shape (no backward compatibility).
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
    lines.append("| Domain | Included URLs | Overflow | Length (chars) | Approx tokens |")
    lines.append("| --- | ---: | --- | ---: | ---: |")
    for domain in ordered_domains:
        rec = records_by_domain.get(domain)
        if rec is None:
            continue
        included_urls = rec.get("included_urls") or []
        if not isinstance(included_urls, list):
            included_urls = []
        overflow = bool(rec.get("overflow", False))
        length = rec.get("length") or {}
        chars = int((length.get("chars") or 0) if isinstance(length, dict) else 0)
        toks = int((length.get("approx_tokens") or 0) if isinstance(length, dict) else 0)
        lines.append(f"| {domain} | {len(included_urls)} | {overflow} | {chars} | {toks} |")
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
        included_urls = rec.get("included_urls") or []
        if not isinstance(included_urls, list):
            included_urls = []
        overflow = bool(rec.get("overflow", False))
        length = rec.get("length") or {}
        chars = int((length.get("chars") or 0) if isinstance(length, dict) else 0)
        toks = int((length.get("approx_tokens") or 0) if isinstance(length, dict) else 0)
        out.append("")
        out.append(f"- **included_urls_count**: {len(included_urls)}")
        out.append(f"- **overflow**: {overflow}")
        out.append(f"- **length.chars**: {chars}")
        out.append(f"- **length.approx_tokens**: {toks}")

        if included_urls:
            out.append("  - included_urls:")
            for u in included_urls:
                out.append(f"    - {u}")

        agg = rec.get("aggregated_context") or ""
        sample = _content_sample(str(agg))
        if sample:
            out.append("  - aggregated_context_sample:")
            out.append(f"    {sample}")
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
    lines.append(" * Purpose: Human-readable summary of aggregated output.jsonl")
    lines.append(" * Description: Summarizes aggregated context shape for quick verification.")
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


