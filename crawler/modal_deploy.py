"""
Purpose: Modal deployment wrapper for the targeted domain crawler.
Description: This file provides a simple Modal function wrapper around the existing crawler
            functionality, enabling cloud deployment without overengineering.
Key Functions: crawl_domains (Modal function wrapper)
"""

import modal
from pathlib import Path

# Create Modal app
app = modal.App("uptick-crawler")

# Define the container image with necessary dependencies
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "python-dotenv>=1.0.1",
        "crawl4ai",  # Core crawling dependency
        "playwright",  # Browser automation
        "pandas",     # CSV handling
        "aiohttp",    # Async HTTP
    )
    .run_commands(
        "playwright install chromium",  # Install browser
        "playwright install-deps chromium"  # Install system dependencies
    )
    # Mount the local crawler code
    .add_local_dir(
        local_path="crawler",
        remote_path="/root/crawler"
    )
)

@app.function(
    image=image,
    timeout=3600,  # 1 hour timeout
    memory=2048,   # 2GB RAM
    cpu=1.0,       # 1 CPU core
)
def crawl_domains(
    input_csv_path: str = "uptick-csvs/final_merged_hubspot_tam_data_resolved.csv",
    output_jsonl_path: str = "llm-input.jsonl",
    limit: int = 10,  # Limit for testing
    domain_column: str = "Company Domain Name",  # Updated to match test CSV
    id_column: str = "Record ID"
):
    """
    Modal function wrapper for the crawler.
    
    Args:
        input_csv_path: Path to input CSV file
        output_jsonl_path: Path for output JSONL file
        limit: Maximum number of domains to process
        domain_column: CSV column containing domains
        id_column: CSV column containing record IDs
    """
    import os
    import sys
    import asyncio
    
    # Add the mounted crawler directory to Python path
    sys.path.insert(0, "/root")
    
    # Import crawler modules
    from crawler.run_crawl import main as run_crawl_main
    
    # Set environment variables for the crawler
    os.environ["INPUT_CSV"] = input_csv_path
    os.environ["OUTPUT_JSONL"] = output_jsonl_path
    os.environ["LIMIT"] = str(limit)
    os.environ["DOMAIN_COLUMN"] = domain_column
    os.environ["ID_COLUMN"] = id_column
    os.environ["CONCURRENCY"] = "2"  # Lower concurrency for Modal
    os.environ["ROBOTS_MODE"] = "ignore"  # Simpler robots handling
    
    print(f"Starting crawl with limit={limit}")
    print(f"Input: {input_csv_path}")
    print(f"Output: {output_jsonl_path}")
    print(f"Domain column: {domain_column}")
    print(f"ID column: {id_column}")
    
    try:
        # Run the crawler
        result = run_crawl_main()
        print(f"Crawl completed with result code: {result}")
        return {
            "status": "success",
            "result_code": result,
            "input_file": input_csv_path,
            "output_file": output_jsonl_path,
            "domains_processed": limit
        }
    except Exception as e:
        print(f"Error during crawl: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "error": str(e),
            "input_file": input_csv_path
        }

@app.local_entrypoint()
def main():
    """Local entrypoint for testing the Modal function."""
    print("Testing Modal crawler function...")
    
    # Test with a small limit
    result = crawl_domains.remote(
        limit=1,
        input_csv_path="uptick-csvs/test.csv"  # Use test CSV
    )
    
    print(f"Test result: {result}")

if __name__ == "__main__":
    # Deploy the app
    app.deploy()
