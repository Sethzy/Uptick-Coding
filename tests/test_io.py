"""
Purpose: Tests for JSONL/CSV writing utilities.
Description: Ensures deterministic JSONL lines and CSV header/row behavior.
Key Tests: test_append_jsonl_sorted, test_csv_header_and_row.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from scoring.io_jsonl import append_jsonl
from scoring.io_csv import ensure_csv_header, append_row, COLUMNS


def test_append_jsonl_sorted():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "out.jsonl"
        obj = {"b": 2, "a": 1}
        append_jsonl(p, obj)
        text = p.read_text(encoding="utf-8").strip()
        assert text == json.dumps({"a": 1, "b": 2}, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def test_csv_header_and_row():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "out.csv"
        ensure_csv_header(p)
        append_row(p, {"domain": "acme.com", "classification_category": "Install Focus", "confidence": 80, "status": "ok", "error": ""})
        lines = p.read_text(encoding="utf-8").splitlines()
        assert lines[0].split(",")[:4] == COLUMNS[:4]
        assert "acme.com" in lines[1]


