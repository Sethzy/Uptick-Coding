"""
Purpose: JSONL read/write helpers for the scoring pipeline.
Description: Small utilities to load LLM inputs and persist results.
Key Functions/Classes: `iter_llm_inputs_from_jsonl`, `write_results_jsonl`.
"""

from __future__ import annotations

import json
from typing import Iterable

from .models import ClassificationResult, LlmInput


def iter_llm_inputs_from_jsonl(path: str) -> Iterable[LlmInput]:
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            yield LlmInput.model_validate(obj)


def write_results_jsonl(path: str, results: Iterable[ClassificationResult]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for r in results:
            f.write(r.model_dump_json())
            f.write("\n")


