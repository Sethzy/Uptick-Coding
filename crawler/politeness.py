"""
Purpose: Politeness controls and retry helpers.
Description: Implements jittered per-domain delays, exponential backoff, and
             retry predicate for transient errors.
Key Functions: jitter_delay_seconds, backoff_sequence

AIDEV-NOTE: Keep conservative defaults to avoid hammering sites.
"""

from __future__ import annotations
import random
from typing import Iterator


def jitter_delay_seconds(base_min: float, base_max: float, jitter: float) -> float:
    base = random.uniform(base_min, base_max)
    j = random.uniform(-jitter, jitter)
    return max(0.0, base + j)


def backoff_sequence(retries: int, *, initial: float = 1.0, factor: float = 2.0) -> Iterator[float]:
    delay = initial
    for _ in range(retries):
        yield delay
        delay *= factor
