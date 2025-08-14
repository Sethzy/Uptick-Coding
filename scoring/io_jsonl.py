"""
Purpose: JSONL writers for scorer outputs and raw model payloads.
Description: Provides simple append helpers that produce deterministic JSON lines with sorted keys and compact separators.
Key Functions/Classes: append_jsonl, append_raw_jsonl.
"""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any, Dict


# AIDEV-NOTE: Deterministic formatting eases diffs and audits across runs.


def _dumps_sorted(obj: Dict[str, Any]) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def append_jsonl(path: str | Path, obj: Dict[str, Any]) -> None:
    """Append a single JSON object as one line to a file (creating parent dirs if needed)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(_dumps_sorted(obj))
        f.write("\n")


def append_raw_jsonl(path: str | Path, text: str) -> None:
    """Append a raw text line to a JSONL file. Caller guarantees `text` is JSON string.

    Useful for persisting model raw responses for audit/debug.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(text.strip())
        f.write("\n")


