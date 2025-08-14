"""
Purpose: Simple structured logging utilities for the scoring pipeline.
Description: Writes compact JSON lines either to stdout or to a .jsonl file for later analysis.
Key Functions/Classes: StructuredLogger, get_logger.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class StructuredLogger:
    path: Optional[Path] = None

    def log(self, event: str, **fields: Any) -> None:
        payload: Dict[str, Any] = {"ts": _iso_now(), "event": event, **fields}
        line = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        if self.path is None:
            sys.stdout.write(line + "\n")
            sys.stdout.flush()
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(line)
            f.write("\n")


def get_logger(path: Optional[str | Path] = None) -> StructuredLogger:
    return StructuredLogger(path=Path(path) if path else None)


