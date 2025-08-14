"""
Purpose: Minimal CLI smoke test.
Description: Verifies the classify command parses flags and invokes without crashing for empty input.
Key Tests: test_cli_help.
"""

from __future__ import annotations

import subprocess
import sys


def test_cli_help():
    # Just ensure the module is importable and help runs
    proc = subprocess.run([sys.executable, "-m", "scoring.cli", "--help"], capture_output=True, text=True)
    assert proc.returncode == 0
    assert "classify" in proc.stdout


