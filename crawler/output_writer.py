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


def write_record_with_status(fh: io.TextIOBase, record: Dict, 
                           status: str, failure_reason: str = None, 
                           pages_visited: int = 0) -> None:
    """
    Write a record with enhanced status fields for crawl tracking.
    
    Args:
        fh: File handle to write to
        record: Base record dictionary
        status: Crawl status - "SUCCESS", "FAIL", or "SKIPPED"
        failure_reason: Specific failure reason (e.g., "DNS_FAIL", "TIMEOUT") or None
        pages_visited: Number of pages successfully crawled
    """
    enhanced_record = record.copy()
    enhanced_record.update({
        "crawl_status": status,
        "failure_reason": failure_reason,
        "pages_visited": pages_visited
    })
    write_record(fh, enhanced_record)
