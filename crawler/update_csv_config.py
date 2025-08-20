#!/usr/bin/env python3
"""
Purpose: Helper script to update CSV configuration in config.json
Description: Allows users to easily change the default CSV file and column names
Key Functions: update_csv_config, main
"""

import json
import os
import click
from pathlib import Path


def update_csv_config(
    config_file: str,
    csv_file: str = None,
    domain_column: str = None,
    id_column: str = None
) -> None:
    """Update CSV configuration in the crawler config file."""
    
    # Read existing config
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # Initialize csv_input section if it doesn't exist
    if "csv_input" not in config:
        config["csv_input"] = {}
    
    # Update only the specified values
    if csv_file is not None:
        config["csv_input"]["default_file"] = csv_file
        click.echo(f"📁 Updated default CSV file to: {csv_file}")
    
    if domain_column is not None:
        config["csv_input"]["domain_column"] = domain_column
        click.echo(f"🏷️  Updated domain column to: {domain_column}")
    
    if id_column is not None:
        config["csv_input"]["id_column"] = id_column
        click.echo(f"🆔 Updated ID column to: {id_column}")
    
    # Write updated config
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    click.echo(f"✅ Configuration updated in {config_file}")
    
    # Show current config
    click.echo(f"\n📋 Current CSV configuration:")
    click.echo(f"   File: {config['csv_input'].get('default_file', 'Not set')}")
    click.echo(f"   Domain Column: {config['csv_input'].get('domain_column', 'Not set')}")
    click.echo(f"   ID Column: {config['csv_input'].get('id_column', 'Not set')}")


@click.command()
@click.option("--config", "-c", default="config.json", help="Path to config.json file")
@click.option("--csv-file", "-f", help="New default CSV file path")
@click.option("--domain-column", "-d", help="New domain column name")
@click.option("--id-column", "-i", help="New ID column name")
@click.option("--show", "-s", is_flag=True, help="Show current configuration without making changes")
def main(config: str, csv_file: str, domain_column: str, id_column: str, show: bool) -> None:
    """Update CSV configuration in crawler config.json"""
    
    if not os.path.exists(config):
        click.echo(f"❌ Config file not found: {config}")
        return
    
    if show:
        # Just show current config
        with open(config, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        click.echo(f"📋 Current CSV configuration in {config}:")
        if "csv_input" in config_data:
            csv_config = config_data["csv_input"]
            click.echo(f"   File: {csv_config.get('default_file', 'Not set')}")
            click.echo(f"   Domain Column: {csv_config.get('domain_column', 'Not set')}")
            click.echo(f"   ID Column: {csv_config.get('id_column', 'Not set')}")
        else:
            click.echo("   No CSV configuration found")
        return
    
    # Check if any updates were requested
    if not any([csv_file, domain_column, id_column]):
        click.echo("❌ No changes specified. Use --help to see options.")
        click.echo("\nExamples:")
        click.echo("  python update_csv_config.py --csv-file new_domains.csv")
        click.echo("  python update_csv_config.py --domain-column website --id-column id")
        click.echo("  python update_csv_config.py --show")
        return
    
    # Update configuration
    update_csv_config(config, csv_file, domain_column, id_column)


if __name__ == "__main__":
    main()
