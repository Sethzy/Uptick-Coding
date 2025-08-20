"""
Purpose: CLI for the lightweight LLM scoring pipeline.
Description: Provides a `scorer classify` command to read labeled dataset
JSONL, call the LLM, and write JSONL outputs.
Key Functions/Classes: Click entrypoints `scorer` and `classify`.
"""

from __future__ import annotations

import os
from typing import Optional

import click

from .api import score_raw_crawler_file
from .config import get_openrouter_api_key, get_default_model
from .scoring_logging import log_info


# AIDEV-NOTE: We use env var OPENROUTER_API_KEY for authentication.


@click.group()
def scorer() -> None:
    """Lead scoring utilities."""


@scorer.command()
@click.option("--input-jsonl", required=True, type=click.Path(exists=True, dir_okay=False))
@click.option("--output-jsonl", required=False, type=click.Path(dir_okay=False))
@click.option("--model", default=None, show_default=True, help="LLM model to use")
@click.option("--timeout-seconds", default=90, type=int, show_default=True)
def classify(
    input_jsonl: str,
    output_jsonl: str | None,
    model: str | None,
    timeout_seconds: int,
) -> None:
    """Classify domains using LLM scoring. Automatically handles both raw and enriched data."""
    if not get_openrouter_api_key():
        click.echo("❌ Error: OpenRouter API key not found!")
        click.echo("   Set OPENROUTER_API_KEY environment variable")
        sys.exit(1)
    
    # Get default model from config if not specified
    if model is None:
        model = get_default_model()
    
    if not output_jsonl:
        input_path = Path(input_jsonl)
        output_jsonl = str(input_path.parent / f"{input_path.stem}_scored{input_path.suffix}")
    
    click.echo(f"🚀 Starting classification...")
    click.echo(f"📁 Input: {input_jsonl}")
    click.echo(f"📤 Output: {output_jsonl}")
    click.echo(f"🤖 Model: {model}")
    click.echo(f"⏱️  Timeout: {timeout_seconds}s")
    click.echo("🔍 Auto-detecting data type (raw crawler or enriched)...")
    
    try:
        # Use the flexible scoring function that handles both raw and enriched data
        results = score_raw_crawler_file(
            input_jsonl=input_jsonl,
            output_jsonl=output_jsonl,
            model=model,
            timeout_seconds=timeout_seconds,
        )
        click.echo(f"✅ Success! Processed {len(results)} domains")
        click.echo(f"📊 Results saved to: {output_jsonl}")
        click.echo("🎯 All fields preserved with classification results")
    except Exception as e:
        click.echo(f"❌ Error during classification: {e}")
        sys.exit(1)


@scorer.command()
@click.option("--input-jsonl", required=True, type=click.Path(exists=True, dir_okay=False))
@click.option("--output-jsonl", required=False, type=click.Path(dir_okay=False))
@click.option("--model", default=None, show_default=True, help="LLM model to use")
@click.option("--timeout-seconds", default=90, type=int, show_default=True)
def score_crawler(
    input_jsonl: str,
    output_jsonl: str | None,
    model: str | None,
    timeout_seconds: int,
) -> None:
    """Score raw crawler data, preserving all crawler fields."""
    if not get_openrouter_api_key():
        click.echo("❌ Error: OpenRouter API key not found!")
        click.echo("   Set OPENROUTER_API_KEY environment variable")
        sys.exit(1)
    
    # Get default model from config if not specified
    if model is None:
        model = get_default_model()
    
    if not output_jsonl:
        input_path = Path(input_jsonl)
        output_jsonl = str(input_path.parent / f"{input_path.stem}_scored{input_path.suffix}")
    
    click.echo(f"🚀 Starting raw crawler scoring...")
    click.echo(f"📁 Input: {input_jsonl}")
    click.echo(f"📤 Output: {output_jsonl}")
    click.echo(f"🤖 Model: {model}")
    click.echo(f"⏱️  Timeout: {timeout_seconds}s")
    click.echo("📊 All crawler fields (html_keywords_found, included_urls, length, etc.) will be preserved")
    
    try:
        results = score_raw_crawler_file(
            input_jsonl=input_jsonl,
            output_jsonl=output_jsonl,
            model=model,
            timeout_seconds=timeout_seconds,
        )
        click.echo(f"✅ Success! Processed {len(results)} domains")
        click.echo(f"📊 Results saved to: {output_jsonl}")
        click.echo("🎯 All crawler fields preserved with classification results")
    except Exception as e:
        click.echo(f"❌ Error during scoring: {e}")
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    scorer()


