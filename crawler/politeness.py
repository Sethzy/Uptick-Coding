"""
Purpose: Politeness controls.
Description: Implements jittered per-domain delays and small human-like pauses.
Key Functions: jitter_delay_seconds, human_like_pause

AIDEV-NOTE: Keep conservative defaults to avoid hammering sites.
"""

from __future__ import annotations
import random
import time


def jitter_delay_seconds(base_min: float, base_max: float, jitter: float) -> float:
    base = random.uniform(base_min, base_max)
    j = random.uniform(-jitter, jitter)
    return max(0.0, base + j)


def human_like_pause(base_ms: int = 2000, jitter_ratio: float = 0.2) -> float:
    """Return seconds to sleep with small jitter (simulate human wait)."""
    jitter = base_ms * jitter_ratio
    import random
    ms = base_ms + random.uniform(-jitter, jitter)
    return max(0.0, ms / 1000.0)
