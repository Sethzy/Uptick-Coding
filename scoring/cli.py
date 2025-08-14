"""
Purpose: CLI for the lightweight LLM scoring pipeline.
Description: Provides a `scorer classify` command to read aggregated-context
JSONL, call the LLM, and write JSONL/CSV outputs.
Key Functions/Classes: Click entrypoints `scorer` and `classify`.
"""

from __future__ import annotations

import os
from typing import Optional

import click

from .api import score_file
from .config import get_openrouter_api_key
from .logging import log_info


# AIDEV-NOTE: We use env var OPENROUTER_API_KEY for authentication.


@click.group()
def scorer() -> None:
    """Lead scoring utilities."""


@scorer.command()
@click.option("--input-jsonl", required=True, type=click.Path(exists=True, dir_okay=False))
@click.option("--output-jsonl", required=False, type=click.Path(dir_okay=False))
@click.option("--output-csv", required=False, type=click.Path(dir_okay=False))
@click.option("--model", default="qwen/qwen3-30b-a3b", show_default=True)
@click.option("--timeout-seconds", default=90, type=int, show_default=True)
def classify(
    input_jsonl: str,
    output_jsonl: Optional[str],
    output_csv: Optional[str],
    model: str,
    timeout_seconds: int,
) -> None:
    """Classify domains using aggregated context JSONL input and write outputs."""
    if not get_openrouter_api_key():
        raise click.ClickException("OpenRouter key not found (set OPENROUTER_API_KEY or OPENROUTER_KEY, or .env)")

    log_info("🚀 Starting domain classification pipeline")
    log_info(f"📁 Input: {input_jsonl}")
    log_info(f"🤖 Model: {model}")
    log_info(f"⏱️  Timeout: {timeout_seconds}s")

    # Run classification
    results = score_file(
        input_jsonl=input_jsonl,
        output_jsonl=output_jsonl,
        output_csv=output_csv,
        model=model,
        timeout_seconds=timeout_seconds,
    )
    
    log_info(f"🎉 Pipeline completed! Processed {len(results)} domains")



if __name__ == "__main__":  # pragma: no cover
    scorer()


