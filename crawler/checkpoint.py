"""
Purpose: Simple file-based checkpointing for idempotent resume.
Description: Tracks processed domains and attempts to enable safe restarts.
Key Functions: load_checkpoint, save_checkpoint, mark_success, mark_attempt

AIDEV-NOTE: Lightweight JSON-based store suitable for MLS scale.
"""

from __future__ import annotations
import json
import os
from typing import Dict, Set


def load_checkpoint(path: str) -> Dict[str, int]:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_checkpoint(path: str, data: Dict[str, int]) -> None:
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.replace(tmp, path)


def mark_attempt(state: Dict[str, int], domain: str) -> None:
    state[domain] = state.get(domain, 0) + 1


def mark_success(state: Dict[str, int], domain: str) -> None:
    state[domain] = -1  # -1 indicates success
