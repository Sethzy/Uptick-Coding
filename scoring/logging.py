"""
Purpose: Minimal logging helper for the scoring package.
Description: Provides `log_info` and `log_error` with consistent prefixing.
Key Functions/Classes: `log_info`, `log_error`.
"""

from __future__ import annotations

import sys
from typing import Any


def log_info(*args: Any) -> None:
    print("[scoring]", *args, file=sys.stderr)


def log_error(*args: Any) -> None:
    print("[scoring][error]", *args, file=sys.stderr)


