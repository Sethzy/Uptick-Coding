"""
Purpose: Console script entrypoint shim for the scoring CLI.
Description: Allows `python -m scoring.run ...` to invoke the CLI commands.
Key Functions/Classes: `main`.
"""

from __future__ import annotations

from .cli import scorer


def main() -> None:  # pragma: no cover
    scorer()


if __name__ == "__main__":  # pragma: no cover
    main()


