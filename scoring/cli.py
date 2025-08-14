"""
Purpose: CLI entrypoint for scorer.
Description: Provides `scorer classify` command to process an input JSONL and emit JSONL/CSV outputs.
Key Functions/Classes: main.
"""

from __future__ import annotations

import sys
import click

from .api import score_file


@click.group()
def cli() -> None:
    pass


@cli.command("classify")
@click.option("--input", "input_jsonl", required=True, type=click.Path(exists=True, dir_okay=False), help="Aggregated input JSONL (one domain per line)")
@click.option("--output-jsonl", "output_jsonl", required=False, type=click.Path(dir_okay=False), help="Defaults to classifications.jsonl next to input")
@click.option("--output-csv", "output_csv", required=False, type=click.Path(dir_okay=False), help="Defaults to classifications-review.csv next to input")
@click.option("--prompt-version", "prompt_version", required=False, default="v1")
@click.option("--raw-jsonl", "raw_jsonl", required=False, type=click.Path(dir_okay=False), help="Defaults to raw-model-responses.jsonl next to input")
@click.option("--checkpoint", "checkpoint", required=False, type=click.Path(dir_okay=False), help="Path to checkpoint file; defaults to output_jsonl.ckpt")
@click.option("--workers", "workers", required=False, type=int, help="Worker count; defaults to config.worker_count")
def classify_cmd(input_jsonl: str, output_jsonl: str | None, output_csv: str | None, prompt_version: str, raw_jsonl: str | None, checkpoint: str | None, workers: int | None) -> None:
    try:
        score_file(
            input_jsonl=input_jsonl,
            output_jsonl=output_jsonl,
            output_csv=output_csv,
            prompt_version=prompt_version,
            raw_jsonl=raw_jsonl,
            checkpoint=checkpoint,
            workers=workers,
        )
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def main() -> None:
    cli(standalone_mode=True)


if __name__ == "__main__":
    main()


