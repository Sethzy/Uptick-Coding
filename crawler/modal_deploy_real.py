"""
Purpose: Simple Modal deployment for the targeted domain crawler
Description: Single-container deployment following Modal best practices
"""

import modal
from pathlib import Path
from datetime import datetime

# Create Modal app
app = modal.App("uptick-crawler-simple")

# Create a Modal Volume for persistent crawler output storage
crawler_volume = modal.Volume.from_name("uptick-crawler-outputs", create_if_missing=True)

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
        local_path=".",
        remote_path="/root/crawler"
    )
    # Mount the CSV file
    .add_local_file(
        local_path="../uptick-csvs/filtered-records.csv",
        remote_path="/root/filtered_records.csv"
    )
)

@app.function(
    image=image,
    timeout=18000,  # 5 hour timeout
    memory=2048,   # 2GB RAM
    cpu=1.0,       # 1 CPU core
    volumes={"/mnt/crawler_outputs": crawler_volume},  # Mount volume for output storage
)
def crawl_domains(
    total_domains: int = 1000,
    domain_column: str = "Company Domain Name",
    id_column: str = "Record ID"
):
    """
    Simple single-container crawler function.
    Processes all domains with internal concurrency.
    """
    import os
    import sys
    import subprocess
    import shutil
    from pathlib import Path
    
    # Generate session ID
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_id = f"simple_crawl_{timestamp}"
    
    # Add the mounted crawler directory to Python path
    sys.path.insert(0, "/root")
    
    # Define output paths
    temp_output_file = "/root/output.jsonl"
    volume_output_file = f"/mnt/crawler_outputs/{session_id}.jsonl"
    
    print(f"🚀 Starting simple crawler (Session: {session_id})")
    print(f"💻 Container: 1 CPU + 2GB RAM")
    print(f"📁 Input CSV: /root/filtered_records.csv")
    print(f"📊 Total domains to process: {total_domains}")
    print(f"⚡ Concurrency: 50 domains simultaneously")
    print(f"📤 Temp Output: {temp_output_file}")
    print(f"💾 Volume Output: {volume_output_file}")
    
    try:
        # Change to the crawler directory
        os.chdir("/root/crawler")
        
        # Build the command line arguments for the crawler
        cmd = [
            "python", "run_crawl.py",
            "--input-csv", "/root/filtered_records.csv",
            "--output-jsonl", temp_output_file,
            "--limit", str(total_domains),
            "--from-index", "0",
            "--column", domain_column,
            "--id-column", id_column,
            "--concurrency", "50",  # 50 concurrent domains
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
        output_file = Path(temp_output_file)
        if output_file.exists():
            # Get file statistics
            file_size = output_file.stat().st_size
            output_lines = sum(1 for _ in open(output_file))
            
            print(f"📄 Output file created: {output_file}")
            print(f"📊 File size: {file_size} bytes")
            print(f"📄 Output lines: {output_lines}")
            
            # Copy to volume for persistence
            shutil.copy2(temp_output_file, volume_output_file)
            print(f"💾 File copied to volume: {volume_output_file}")
            
            # Clean up temp file
            os.remove(temp_output_file)
            print(f"🧹 Temp file cleaned up")
            
            return {
                "status": "success",
                "session_id": session_id,
                "file_size": file_size,
                "output_lines": output_lines,
                "volume_file": f"{session_id}.jsonl",
                "domains_processed": output_lines,
                "total_domains": total_domains,
                "concurrency": 50,
                "message": f"Successfully processed {output_lines} domains"
            }
        else:
            error_msg = f"Output file not created. Return code: {result.returncode}"
            print(f"❌ {error_msg}")
            return {
                "status": "error",
                "message": error_msg,
                "crawler_stdout": result.stdout,
                "crawler_stderr": result.stderr,
                "return_code": result.returncode
            }
            
    except Exception as e:
        error_msg = f"Exception during crawl: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "status": "error",
            "message": error_msg,
            "exception": str(e)
        }

@app.local_entrypoint()
def main(
    total_domains: int = 1000,
    domain_column: str = "Company Domain Name",
    id_column: str = "Record ID"
):
    """
    Local entrypoint for running the simple crawler.
    """
    print(f"🚀 Starting simple Modal crawler...")
    print(f"📊 Total domains to process: {total_domains}")
    print(f"💻 Single container with 50 concurrent crawlers")
    
    # Run the crawler function
    result = crawl_domains.remote(
        total_domains=total_domains,
        domain_column=domain_column,
        id_column=id_column
    )
    
    print(f"\n🎉 Crawl completed!")
    print(f"📊 Status: {result['status']}")
    
    if result['status'] == 'success':
        print(f"✅ Domains processed: {result['domains_processed']}")
        print(f"📁 Output file: {result['volume_file']}")
        print(f"📊 File size: {result['file_size']} bytes")
        print(f"\n💡 To download results:")
        print(f"   modal volume get uptick-crawler-outputs {result['volume_file']}")
    else:
        print(f"❌ Error: {result['message']}")
        if result.get('crawler_stderr'):
            print(f"⚠️  Stderr: {result['crawler_stderr'][:200]}...")
    
    return result

if __name__ == "__main__":
    # Deploy the app
    app.deploy()
    print("🚀 App deployed! You can now run:")
    print("   modal run crawler/modal_deploy_real.py --total-domains 1000")
    print("   modal volume get uptick-crawler-outputs <session_id>.jsonl  # to download output")