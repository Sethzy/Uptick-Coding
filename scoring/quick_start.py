#!/usr/bin/env python3
"""
Purpose: Quick start script for the scoring module with common commands.
Description: Provides simplified commands for scoring operations with sensible defaults.
Key Functions/Classes: `quick_score`, `score_sample`, `check_setup`.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

import click

from .api import score_enriched_hubspot_file
from .config import get_openrouter_api_key
from .logging import log_info


@click.group()
def quick_start() -> None:
    """🚀 Quick start commands for scoring module."""
    pass


@quick_start.command()
@click.argument("input_file", type=click.Path(exists=True, dir_okay=False))
@click.option("--output", "-o", help="Output file path (auto-generated if not specified)")
@click.option("--model", "-m", default="qwen/qwen3-30b-a3b", help="LLM model to use")
@click.option("--hubspot-csv", "-h", help="HubSpot CSV file to enrich with (optional)")
def score(input_file: str, output: Optional[str], model: str, hubspot_csv: Optional[str]) -> None:
    """Quick score a JSONL file with sensible defaults."""
    if not get_openrouter_api_key():
        click.echo("❌ Error: OpenRouter API key not found!")
        click.echo("   Set OPENROUTER_API_KEY environment variable or create a .env file")
        sys.exit(1)
    
    # Check if we need to enrich the data first
    if hubspot_csv:
        click.echo(f"🔄 Enriching crawler data with HubSpot CSV...")
        click.echo(f"📊 HubSpot CSV: {hubspot_csv}")
        
        # Import enrichment function
        from .enrich_crawler_with_hubspot import enrich_crawler_data
        
        # Create enriched file path
        input_path = Path(input_file)
        enriched_file = str(input_path.parent / f"{input_path.stem}_enriched{input_path.suffix}")
        
        try:
            enrich_crawler_data(
                crawler_jsonl=input_file,
                hubspot_csv=hubspot_csv,
                output_jsonl=enriched_file
            )
            input_file = enriched_file  # Use enriched file for scoring
            click.echo(f"✅ Enrichment complete! Using: {enriched_file}")
        except Exception as e:
            click.echo(f"❌ Error during enrichment: {e}")
            sys.exit(1)
    
    # Auto-generate output filename if not provided
    if not output:
        input_path = Path(input_file)
        output = str(input_path.parent / f"{input_path.stem}_scored{input_path.suffix}")
    
    click.echo(f"🚀 Starting quick score...")
    click.echo(f"📁 Input: {input_file}")
    click.echo(f"📤 Output: {output}")
    click.echo(f"🤖 Model: {model}")
    
    try:
        results = score_enriched_hubspot_file(
            input_jsonl=input_file,
            output_jsonl=output,
            model=model,
            timeout_seconds=90
        )
        click.echo(f"✅ Success! Processed {len(results)} domains")
        click.echo(f"📊 Results saved to: {output}")
    except Exception as e:
        click.echo(f"❌ Error during scoring: {e}")
        sys.exit(1)


@quick_start.command()
@click.argument("input_file", type=click.Path(exists=True, dir_okay=False))
@click.argument("hubspot_csv", type=click.Path(exists=True, dir_okay=False))
@click.option("--output", "-o", help="Output file path (auto-generated if not specified)")
def enrich(input_file: str, hubspot_csv: str, output: Optional[str]) -> None:
    """Enrich crawler data with HubSpot CSV data."""
    click.echo(f"🔄 Starting data enrichment...")
    click.echo(f"📁 Crawler data: {input_file}")
    click.echo(f"📊 HubSpot CSV: {hubspot_csv}")
    
    # Import enrichment function
    from .enrich_crawler_with_hubspot import enrich_crawler_data
    
    # Auto-generate output filename if not provided
    if not output:
        input_path = Path(input_file)
        output = str(input_path.parent / f"{input_path.stem}_enriched{input_path.suffix}")
    
    try:
        enrich_crawler_data(
            crawler_jsonl=input_file,
            hubspot_csv=hubspot_csv,
            output_jsonl=output
        )
        click.echo(f"✅ Enrichment complete! Output: {output}")
    except Exception as e:
        click.echo(f"❌ Error during enrichment: {e}")
        sys.exit(1)


@quick_start.command()
def check_setup() -> None:
    """Check if the scoring module is properly configured."""
    click.echo("🔍 Checking scoring module setup...")
    
    # Check API key
    api_key = get_openrouter_api_key()
    if api_key:
        click.echo("✅ OpenRouter API key: Found")
        click.echo(f"   Key: {api_key[:8]}...{api_key[-4:]}")
    else:
        click.echo("❌ OpenRouter API key: Missing")
        click.echo("   Set OPENROUTER_API_KEY environment variable")
    
    # Check dependencies
    try:
        import httpx
        click.echo("✅ httpx: Available")
    except ImportError:
        click.echo("❌ httpx: Missing")
    
    try:
        import click as click_lib
        click.echo("✅ click: Available")
    except ImportError:
        click.echo("❌ click: Missing")
    
    try:
        import pydantic
        click.echo("✅ pydantic: Available")
    except ImportError:
        click.echo("❌ pydantic: Missing")
    
    # Check if we can import the main modules
    try:
        from . import api, models
        click.echo("✅ Scoring modules: Available")
    except ImportError as e:
        click.echo(f"❌ Scoring modules: Error - {e}")


@quick_start.command()
@click.option("--sample-size", "-n", default=5, help="Number of sample records to process")
def score_sample(sample_size: int) -> None:
    """Score a small sample for testing purposes."""
    # Look for common input files
    possible_inputs = [
        "crawl_*.jsonl",
        "scoring-runs/*.jsonl", 
        "*.jsonl"
    ]
    
    input_file = None
    for pattern in possible_inputs:
        matches = list(Path(".").glob(pattern))
        if matches:
            input_file = str(matches[0])
            break
    
    if not input_file:
        click.echo("❌ No JSONL files found in current directory")
        click.echo("   Please run this command from a directory with JSONL files")
        sys.exit(1)
    
    click.echo(f"🎯 Found input file: {input_file}")
    click.echo(f"🧪 Running sample scoring with {sample_size} records...")
    
    # For now, just run the full scoring (you could modify the API to limit records)
    score.callback(input_file, None, "qwen/qwen3-30b-a3b")


if __name__ == "__main__":
    quick_start()
