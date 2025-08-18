"""
Purpose: Real Modal deployment for the targeted domain crawler
Description: This deployment uses the full crawler logic to crawl domains and return output files
Key Functions: crawl_domains_real (full crawler with output)
"""

import modal
from pathlib import Path

# Create Modal app
app = modal.App("uptick-crawler-real")

# Define the container image with necessary dependencies
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "python-dotenv>=1.0.1",
        "crawl4ai",  # Core crawling dependency
        "playwright",  # Browser automation
        "pandas",     # CSV handling
        "aiohttp",    # Async HTTP
        "httpx>=0.27.0",
        "click>=8.1.7",
        "pydantic>=2.8.2",
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
    # Mount the CSV file
    .add_local_file(
        local_path="uptick-csvs/test.csv",
        remote_path="/root/test.csv"
    )
)

@app.function(
    image=image,
    timeout=1800,  # 30 minute timeout
    memory=4096,   # 4GB RAM
    cpu=2.0,       # 2 CPU cores
)
def crawl_domains_real(
    limit: int = 1,
    domain_column: str = "Company Domain Name",
    id_column: str = "Record ID"
):
    """
    Real crawler function that uses the full crawler logic and returns output files.
    
    Args:
        limit: Maximum number of domains to process
        domain_column: CSV column containing domains
        id_column: CSV column containing record IDs
    """
    import os
    import sys
    import json
    import subprocess
    from pathlib import Path
    
    # Add the mounted crawler directory to Python path
    sys.path.insert(0, "/root")
    
    print(f"🚀 Starting REAL crawl with limit={limit}")
    print(f"📁 Input CSV: /root/test.csv")
    print(f"📤 Output: /root/output.jsonl")
    print(f"🏷️  Domain column: {domain_column}")
    print(f"🏷️  ID column: {id_column}")
    
    try:
        # Change to the crawler directory
        os.chdir("/root/crawler")
        
        # Build the command line arguments for the crawler
        cmd = [
            "python", "run_crawl.py",
            "--input-csv", "/root/test.csv",
            "--output-jsonl", "/root/output.jsonl",
            "--limit", str(limit),
            "--column", domain_column,
            "--id-column", id_column,
            "--concurrency", "1",  # Single domain, so low concurrency
            "--robots", "ignore"   # Simpler robots handling
        ]
        
        print(f"🔍 Executing crawler with command: {' '.join(cmd)}")
        
        # Run the crawler as a subprocess
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd="/root/crawler"
        )
        
        print(f"✅ Crawl completed with return code: {result.returncode}")
        if result.stdout:
            print(f"📤 Crawler stdout: {result.stdout[:500]}...")
        if result.stderr:
            print(f"⚠️  Crawler stderr: {result.stderr[:500]}...")
        
        # Check if output file was created
        output_file = Path("/root/output.jsonl")
        if output_file.exists():
            # Read the output file content
            with open(output_file, 'r', encoding='utf-8') as f:
                output_content = f.read()
            
            # Count lines (each line is a JSON record)
            line_count = len(output_content.strip().split('\n')) if output_content.strip() else 0
            
            print(f"📊 Output file created: {output_file}")
            print(f"📄 Lines in output: {line_count}")
            
            # Return the file content and metadata
            return {
                "status": "success",
                "result_code": result.returncode,
                "output_file_content": output_content,
                "output_file_size": len(output_content),
                "output_lines": line_count,
                "domains_processed": limit,
                "input_file": "/root/test.csv",
                "output_file": "/root/output.jsonl",
                "crawler_stdout": result.stdout,
                "crawler_stderr": result.stderr
            }
        else:
            print("⚠️  No output file created")
            return {
                "status": "warning",
                "result_code": result.returncode,
                "message": "Crawl completed but no output file was created",
                "domains_processed": limit,
                "crawler_stdout": result.stdout,
                "crawler_stderr": result.stderr
            }
            
    except Exception as e:
        print(f"❌ Error during crawl: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "error": str(e),
            "input_file": "/root/test.csv"
        }

@app.local_entrypoint()
def main():
    """Local entrypoint for testing."""
    print("Testing real Modal crawler...")
    
    result = crawl_domains_real.remote(
        limit=1,
        domain_column="Company Domain Name",
        id_column="Record ID"
    )
    
    print(f"Test result: {result}")
    
    # If successful, save the output file locally
    if result.get('status') == 'success' and result.get('output_file_content'):
        output_content = result['output_file_content']
        with open('modal_crawl_output.jsonl', 'w', encoding='utf-8') as f:
            f.write(output_content)
        print(f"💾 Output saved to: modal_crawl_output.jsonl")

if __name__ == "__main__":
    # Deploy the app
    app.deploy()
