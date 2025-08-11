"""
Purpose: CSV helpers for preparing website inputs for Crawl4AI test runs.

Description: This module provides utilities to parse the `website` column from
the input CSV, normalize each website into a valid URL (defaulting to
`https://` when no scheme is present), and deduplicate/validate entries.

Key Functions/Classes:
- read_websites_from_csv: Reads the `website` column.
- normalize_url: Ensures scheme and basic URL hygiene.
- prepare_url_list: Full pipeline: parse → normalize → filter → dedupe.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable, List, Optional, Set
from urllib.parse import urlparse


# AIDEV-NOTE: CSV helper functions for Crawl4AI test flows


def read_websites_from_csv(csv_path: str | Path) -> List[str]:
    """Read the `website` column from a CSV with header.

    Ignores empty cells. Returns values as raw strings (no scheme added yet).
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path}")

    websites: List[str] = []
    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if "website" not in (reader.fieldnames or []):
            raise ValueError("CSV is missing a `website` column header")
        for row in reader:
            raw = (row.get("website") or "").strip()
            if raw:
                websites.append(raw)
    return websites


def normalize_url(raw: str) -> Optional[str]:
    """Normalize a website cell into a URL.

    - Adds https:// if the scheme is missing
    - Trims whitespace and lowercases the host only
    - Filters obvious invalids (no host after parsing)
    """
    candidate = raw.strip()
    if not candidate:
        return None

    # If scheme missing, default to https
    if "://" not in candidate and not candidate.startswith("raw:") and not candidate.startswith("file:"):
        candidate = f"https://{candidate}"

    parsed = urlparse(candidate)
    if not parsed.netloc:
        return None

    netloc_lower = parsed.netloc.lower()
    # Rebuild with lowercased host
    normalized = parsed._replace(netloc=netloc_lower).geturl()
    return normalized


def _dedupe_preserving_order(items: Iterable[str]) -> List[str]:
    seen: Set[str] = set()
    result: List[str] = []
    for item in items:
        if item not in seen:
            result.append(item)
            seen.add(item)
    return result


def prepare_url_list(csv_path: str | Path, limit: Optional[int] = None) -> List[str]:
    """Pipeline: CSV → raw websites → normalized URLs → deduped → limited.

    Returns at most `limit` URLs if provided.
    """
    raw_websites = read_websites_from_csv(csv_path)
    normalized = [u for u in (normalize_url(x) for x in raw_websites) if u]
    deduped = _dedupe_preserving_order(normalized)
    if limit is not None:
        return deduped[: max(0, limit)]
    return deduped


