"""
Purpose: CSV writer for scorer outputs.
Description: Flattens model outputs and metadata into a stable set of columns.
Key Functions/Classes: ensure_csv_header, append_row.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List, Any


COLUMNS: List[str] = [
    "record_id",
    "domain",
    "classification_category",
    "confidence",
    "rationale",
    "other_sublabel",
    "other_sublabel_definition",
    "model_name",
    "prompt_version",
    "run_id",
    "status",
    "error",
]


def ensure_csv_header(path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists() or p.stat().st_size == 0:
        with p.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(COLUMNS)


def append_row(path: str | Path, row: Dict[str, Any]) -> None:
    ensure_csv_header(path)
    values = [row.get(col, "") for col in COLUMNS]
    with Path(path).open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(values)


