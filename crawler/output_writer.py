"""
Purpose: JSONL output writer for domain records.
Description: Emits one record per domain with required schema and optional page
             artifacts (markdown/html/links). Supports atomic writes.
Key Functions: write_record, open_jsonl

AIDEV-NOTE: Keep writer simple and robust for long runs.
"""

from __future__ import annotations
import io
import json
import os
from contextlib import contextmanager
from typing import Dict, Iterator


@contextmanager
def open_jsonl(path: str) -> Iterator[io.TextIOWrapper]:
    tmp = f"{path}.tmp"
    f = open(tmp, "w", encoding="utf-8")
    try:
        yield f
    finally:
        f.flush()
        os.fsync(f.fileno())
        f.close()
        os.replace(tmp, path)


def write_record(fh: io.TextIOBase, record: Dict) -> None:
    fh.write(json.dumps(record, ensure_ascii=False) + "\n")
