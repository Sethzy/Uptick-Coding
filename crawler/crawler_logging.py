"""
Purpose: Provide structured logging helpers for the targeted domain crawler.
Description: Defines JSON-style logging utilities for progress, events, and
            end-of-run summaries. Keeps logs consistent across modules.
Key Functions: get_logger, log_progress, log_event, log_summary

AIDEV-NOTE: Centralize logging; prefer structured fields for easy parsing.
"""

from __future__ import annotations
import json
import logging
import sys
from typing import Any, Dict, Optional

# AIDEV-NOTE: Avoid reconfiguring root logger elsewhere; use this factory.

def get_logger(name: str = "crawler") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


def _to_json(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False)


def log_progress(logger: logging.Logger, domain: str, status: str, *,
                 reason: str = "", attempt: int = 0, elapsed_ms: Optional[int] = None,
                 pages_visited: Optional[int] = None) -> None:
    logger.info(_to_json({
        "type": "progress",
        "domain": domain,
        "status": status,
        "reason": reason,
        "attempt": attempt,
        "elapsed_ms": elapsed_ms,
        "pages_visited": pages_visited,
    }))


def log_event(logger: logging.Logger, event: str, *, details: Optional[Dict[str, Any]] = None) -> None:
    logger.info(_to_json({
        "type": "event",
        "event": event,
        "details": details or {},
    }))


def log_summary(logger: logging.Logger, *, total: int, ok: int, fail: int, retry: int,
                reasons: Optional[Dict[str, int]] = None) -> None:
    logger.info(_to_json({
        "type": "summary",
        "total": total,
        "ok": ok,
        "fail": fail,
        "retry": retry,
        "reasons": reasons or {},
    }))
