"""
Purpose: JSONL read/write helpers for the scoring pipeline.
Description: Small utilities to load labeled dataset records and persist classification results.
Key Functions/Classes: `iter_labeled_dataset_from_jsonl`, `write_labeled_results_jsonl`.
"""

from __future__ import annotations

import json
from typing import Iterable

from .models import LabeledDatasetRecord, LabeledDatasetResult, CrawlerRecord


def iter_labeled_dataset_from_jsonl(path: str) -> Iterable[LabeledDatasetRecord]:
    """Read labeled dataset records from JSONL file."""
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            yield LabeledDatasetRecord.model_validate(obj)


def iter_crawler_records_from_jsonl(path: str) -> Iterable[CrawlerRecord]:
    """Read raw crawler records from JSONL file."""
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            yield CrawlerRecord.model_validate(obj)


def write_labeled_results_jsonl(path: str, results: Iterable[LabeledDatasetResult]) -> None:
    """Write labeled dataset results with classification to JSONL file."""
    with open(path, "w", encoding="utf-8") as f:
        for r in results:
            # Use by_alias=True to maintain original field names with spaces
            f.write(r.model_dump_json(by_alias=True))
            f.write("\n")


