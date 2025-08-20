#!/usr/bin/env python3
"""
Purpose: Enrich crawler data with HubSpot CSV data before scoring.
Description: Merges crawler JSONL output with HubSpot CSV to create enriched dataset for scoring.
Key Functions/Classes: `enrich_crawler_data`, `main`.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

import click


def load_hubspot_data(csv_path: str) -> Dict[str, Dict[str, str]]:
    """Load HubSpot CSV data indexed by domain."""
    hubspot_data = {}
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            # Try different possible domain columns
            domain = None
            for col in ['Company Domain Name', 'Website', 'tam_site']:
                if col in row and row[col]:
                    domain = row[col].strip().lower()
                    # Clean domain (remove http://, www., etc.)
                    if domain.startswith('http'):
                        from urllib.parse import urlparse
                        try:
                            domain = urlparse(domain).netloc
                        except:
                            continue
                    if domain.startswith('www.'):
                        domain = domain[4:]
                    break
            
            if domain:
                hubspot_data[domain] = row
    
    print(f"📊 Loaded {len(hubspot_data)} HubSpot records")
    return hubspot_data


def enrich_crawler_record(crawler_record: Dict, hubspot_data: Dict[str, Dict[str, str]]) -> Dict:
    """Enrich a single crawler record with HubSpot data."""
    domain = crawler_record.get('domain', '').lower()
    
    # Find matching HubSpot record
    hubspot_record = hubspot_data.get(domain, {})
    
    if not hubspot_record:
        print(f"⚠️  No HubSpot data found for domain: {domain}")
        # Create empty HubSpot fields
        hubspot_record = {
            "Company name": "",
            "NA State": "",
            "State/County": "",
            "Country": "",
            "Company Domain Name": domain,
            "Phone Number": "",
            "Company owner": "",
            "Lead Status": "",
            "Clay score": "",
            "Associated Note": "",
            "Current Software": "",
            "Current Software Contract End Date": "",
            "Core service": "",
            "Accounting software (US)": "",
            "Industry_": "",
            "Client Use Case": "",
            "Associated Note IDs": "",
            "Perform Search": "",
            "Link To Google Search": "",
            "Results Returned Count": "",
            "Serper Link": "",
            "Enrich Company": "",
            "Founded": "",
            "Employee Count": "",
            "Website": f"https://{domain}",
            "Find Contacts at Company": "",
            "PIC 1 Name": "",
            "PIC 1 TItle": "",
            "PIC 1 URL": "",
            "PIC 1 Contact Info": "",
            "PIC 2 Name": "",
            "PIC 2 Title": "",
            "PIC 2 URL": "",
            "PIC 2 Contact Info": "",
            "Find Contacts at Company (2)": "",
            "PIC 3 Name": "",
            "PIC 3 Title": "",
            "PIC 3 URL": "",
            "PIC 3 Contact Info": "",
            "CEO LinkedIn URL (2)": "",
            "Linkedin Url": "",
        }
    else:
        print(f"✅ Found HubSpot data for domain: {domain}")
    
    # Merge crawler data with HubSpot data
    enriched_record = {
        **crawler_record,  # All crawler fields
        **hubspot_record,  # All HubSpot fields
    }
    
    return enriched_record


def enrich_crawler_data(
    crawler_jsonl: str,
    hubspot_csv: str,
    output_jsonl: str,
    domain_column: str = "Company Domain Name"
) -> None:
    """Enrich crawler data with HubSpot CSV data."""
    print(f"🚀 Starting data enrichment...")
    print(f"📁 Crawler data: {crawler_jsonl}")
    print(f"📊 HubSpot data: {hubspot_csv}")
    print(f"📤 Output: {output_jsonl}")
    
    # Load HubSpot data
    hubspot_data = load_hubspot_data(hubspot_csv)
    
    # Process crawler records
    enriched_records = []
    total_records = 0
    
    with open(crawler_jsonl, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                crawler_record = json.loads(line)
                enriched_record = enrich_crawler_record(crawler_record, hubspot_data)
                enriched_records.append(enriched_record)
                total_records += 1
                
                if total_records % 10 == 0:
                    print(f"📝 Processed {total_records} records...")
                    
            except json.JSONDecodeError as e:
                print(f"⚠️  Error parsing line {line_num}: {e}")
                continue
    
    # Write enriched data
    print(f"\n💾 Writing {len(enriched_records)} enriched records...")
    with open(output_jsonl, 'w', encoding='utf-8') as f:
        for record in enriched_records:
            f.write(json.dumps(record, ensure_ascii=False))
            f.write('\n')
    
    print(f"✅ Enrichment complete!")
    print(f"📊 Total records: {total_records}")
    print(f"📁 Output saved to: {output_jsonl}")
    
    # Show sample of enriched data
    if enriched_records:
        sample = enriched_records[0]
        print(f"\n🔍 Sample enriched record for domain: {sample.get('domain', 'N/A')}")
        print(f"   Company name: {sample.get('Company name', 'N/A')}")
        print(f"   State: {sample.get('State/County', 'N/A')}")
        print(f"   Industry: {sample.get('Industry_', 'N/A')}")


@click.command()
@click.argument("crawler_jsonl", type=click.Path(exists=True, dir_okay=False))
@click.argument("hubspot_csv", type=click.Path(exists=True, dir_okay=False))
@click.option("--output", "-o", help="Output JSONL file path (auto-generated if not specified)")
@click.option("--domain-column", "-d", default="Company Domain Name", help="CSV column containing domains")
def main(crawler_jsonl: str, hubspot_csv: str, output: Optional[str], domain_column: str) -> None:
    """Enrich crawler data with HubSpot CSV data."""
    if not output:
        input_path = Path(crawler_jsonl)
        output = str(input_path.parent / f"{input_path.stem}_enriched{input_path.suffix}")
    
    enrich_crawler_data(
        crawler_jsonl=crawler_jsonl,
        hubspot_csv=hubspot_csv,
        output_jsonl=output,
        domain_column=domain_column
    )


if __name__ == "__main__":
    main()
