"""
Purpose: CSV writer for the scoring pipeline.
Description: Writes flattened classification results to CSV with evidence columns.
Key Functions/Classes: `write_results_csv`.
"""

from __future__ import annotations

import csv
from typing import Iterable

from .models import ClassificationResult


def write_results_csv(path: str, results: Iterable[ClassificationResult]) -> None:
    fieldnames = [
        "domain",
        "classification_category",
        "rationale",
        "evidence_url_1",
        "evidence_snippet_1",
        "evidence_url_2",
        "evidence_snippet_2",
        "evidence_url_3",
        "evidence_snippet_3",
        "model_name",
        "model_version",
        "prompt_version",
        "classifier_mode",
        "run_id",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow(
                {
                    "domain": r.domain,
                    "classification_category": r.classification_category,
                    "rationale": r.rationale,
                    "evidence_url_1": "",
                    "evidence_snippet_1": "",
                    "evidence_url_2": "",
                    "evidence_snippet_2": "",
                    "evidence_url_3": "",
                    "evidence_snippet_3": "",
                    "model_name": "",
                    "model_version": "",
                    "prompt_version": "",
                    "classifier_mode": "LLM",
                    "run_id": "",
                }
            )


