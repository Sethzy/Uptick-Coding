"""
Purpose: Domain input loading and normalization utilities for the crawler.
Description: Reads domains from the TAM CSV (`tam_site` column), normalizes raw
             values into apex domains suitable for canonical URL fallback logic,
             and filters out invalid/empty entries while preserving input order.
Key Functions: load_domains_from_csv, normalize_domain, list_unique_preserve_order

AIDEV-NOTE: normalize_domain returns an apex domain (drops scheme, path, port,
            leading 'www.'). Canonical URL probing will try https/root vs www.
"""

from __future__ import annotations
import csv
import re
from typing import Iterable, List, Optional
from urllib.parse import urlsplit

# AIDEV-NOTE: Conservative domain pattern; avoids schemes, ports, and paths.
_DOMAIN_RE = re.compile(
    r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)+$",
    re.IGNORECASE,
)


def normalize_domain(raw: Optional[str]) -> Optional[str]:
    """
    Normalize a raw domain/URL string into an apex domain.

    Rules:
    - Trim whitespace; lowercase
    - If URL-like, extract host via urlsplit; else take token before first '/'
    - Strip credentials, port, and leading 'www.'
    - Require at least one dot and match conservative domain regex
    - Return None if invalid
    """
    if not raw:
        return None
    s = raw.strip().lower()
    if not s:
        return None

    # Extract host
    host = s
    if "://" in s:
        parts = urlsplit(s)
        host = parts.netloc or parts.path
    else:
        if "/" in host:
            host = host.split("/", 1)[0]

    # Drop credentials and port
    host = host.split("@")[-1]
    if ":" in host:
        host = host.split(":", 1)[0]

    # Strip leading www. and surrounding dots
    host = host.strip(".")
    if host.startswith("www."):
        host = host[4:]

    # Validate
    if not host or "." not in host:
        return None
    if not _DOMAIN_RE.match(host):
        return None
    return host


def list_unique_preserve_order(items: Iterable[str]) -> List[str]:
    """Return unique items preserving first-seen order."""
    seen = set()
    out: List[str] = []
    for it in items:
        if it not in seen:
            seen.add(it)
            out.append(it)
    return out


def load_domains_from_csv(csv_path: str, column: str = "tam_site") -> List[str]:
    """
    Load domains from a CSV file, normalizing and filtering invalid entries.

    - Reads `column` (default: tam_site)
    - Applies normalize_domain
    - Preserves input order; removes duplicates
    """
    domains: List[str] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or column not in reader.fieldnames:
            raise ValueError(f"CSV missing required column: {column}")
        for row in reader:
            raw = (row.get(column) or "").strip()
            norm = normalize_domain(raw)
            if norm:
                domains.append(norm)
    return list_unique_preserve_order(domains)
