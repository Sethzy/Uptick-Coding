"""
Purpose: Real Modal deployment for the targeted domain crawler
Description: This deployment uses the full crawler logic to crawl domains and return output files
Key Functions: crawl_domains_real (full crawler with output)
"""

import modal
from pathlib import Path
import hashlib
from datetime import datetime

# Create Modal app
app = modal.App("uptick-crawler-real")

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
        local_path="crawler",
        remote_path="/root/crawler"
    )
    # Mount the CSV file
    .add_local_file(
        local_path="uptick-csvs/Hubspot TAM LIST.csv",
        remote_path="/root/hubspot_tam_list.csv"
    )
)

@app.function(
    image=image,
    timeout=1800,  # 30 minute timeout
    memory=4096,   # 4GB RAM
    cpu=2.0,       # 2 CPU cores
    volumes={"/mnt/crawler_outputs": crawler_volume},  # Mount volume for output storage
)
def crawl_domains_real(
    limit: int = 1,
    domain_column: str = "Company Domain Name",
    id_column: str = "Record ID",
    session_id: str = None
):
    """
    Real crawler function that uses the full crawler logic and saves output to persistent volume.
    
    Args:
        limit: Maximum number of domains to process
        domain_column: CSV column containing domains
        id_column: CSV column containing record IDs
        session_id: Unique session identifier for output files
    """
    import os
    import sys
    import subprocess
    import shutil
    from pathlib import Path
    
    # Generate session ID if not provided
    if session_id is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = f"crawl_{timestamp}_{limit}domains"
    
    # Add the mounted crawler directory to Python path
    sys.path.insert(0, "/root")
    
    # Define output paths
    temp_output_file = "/root/output.jsonl"
    volume_output_file = f"/mnt/crawler_outputs/{session_id}.jsonl"
    
    print(f"🚀 Starting REAL crawl with limit={limit} (Session: {session_id})")
    print(f"📁 Input CSV: /root/hubspot_tam_list.csv")
    print(f"📤 Temp Output: {temp_output_file}")
    print(f"💾 Volume Output: {volume_output_file}")
    print(f"🏷️  Domain column: {domain_column}")
    print(f"🏷️  ID column: {id_column}")
    
    try:
        # Change to the crawler directory
        os.chdir("/root/crawler")
        
        # Build the command line arguments for the crawler
        cmd = [
            "python", "run_crawl.py",
            "--input-csv", "/root/hubspot_tam_list.csv",
            "--output-jsonl", temp_output_file,
            "--limit", str(limit),
            "--column", domain_column,
            "--id-column", id_column,
            "--concurrency", "2",  # Use both CPU cores efficiently
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
            
            # Read the output file content to count lines
            with open(output_file, 'r', encoding='utf-8') as f:
                output_content = f.read()
            line_count = len(output_content.strip().split('\n')) if output_content.strip() else 0
            
            # Calculate file checksum for integrity verification
            with open(output_file, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            
            print(f"📊 Output file created: {output_file}")
            print(f"📄 Lines in output: {line_count}")
            print(f"📏 File size: {file_size} bytes")
            print(f"🔒 File hash: {file_hash[:16]}...")
            
            # Ensure output directory exists on volume
            os.makedirs("/mnt/crawler_outputs", exist_ok=True)
            
            # Copy the output file to the persistent volume
            print(f"💾 Copying output to volume: {volume_output_file}")
            shutil.copy2(temp_output_file, volume_output_file)
            
            # Verify the copy was successful
            if Path(volume_output_file).exists():
                volume_file_size = Path(volume_output_file).stat().st_size
                print(f"✅ File successfully saved to volume ({volume_file_size} bytes)")
                
                # Verify integrity
                with open(volume_output_file, 'rb') as f:
                    volume_file_hash = hashlib.sha256(f.read()).hexdigest()
                
                if file_hash == volume_file_hash:
                    print(f"✅ File integrity verified (hashes match)")
                else:
                    print(f"⚠️  File integrity warning: hashes don't match")
                
                return {
                    "status": "success",
                    "result_code": result.returncode,
                    "session_id": session_id,
                    "volume_file_path": volume_output_file,
                    "file_size": file_size,
                    "file_hash": file_hash,
                    "output_lines": line_count,
                    "domains_processed": limit,
                    "input_file": "/root/test.csv",
                    "temp_output_file": temp_output_file,
                    "crawler_stdout": result.stdout[:1000] if result.stdout else None,  # Truncate for return
                    "crawler_stderr": result.stderr[:1000] if result.stderr else None   # Truncate for return
                }
            else:
                print("❌ Failed to copy file to volume")
                return {
                    "status": "error",
                    "result_code": result.returncode,
                    "message": "Crawl completed but failed to save to volume",
                    "session_id": session_id,
                    "temp_file_exists": True,
                    "file_size": file_size,
                    "domains_processed": limit
                }
        else:
            print("⚠️  No output file created")
            return {
                "status": "warning",
                "result_code": result.returncode,
                "message": "Crawl completed but no output file was created",
                "session_id": session_id,
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
            "session_id": session_id,
            "input_file": "/root/hubspot_tam_list.csv"
        }

@app.local_entrypoint()
def main(
    limit: int = 2,
    domain_column: str = "Company Domain Name",
    id_column: str = "Record ID"
):
    """Local entrypoint for running crawler. Files are saved to Modal volume."""
    print(f"🚀 Starting Modal crawler with limit={limit}...")
    
    # Run the crawler on Modal
    result = crawl_domains_real.remote(
        limit=limit,
        domain_column=domain_column,
        id_column=id_column
    )
    
    print(f"📊 Crawl result: {result['status']}")
    
    if result.get('status') == 'success':
        session_id = result.get('session_id')
        print(f"✅ Crawl successful (Session: {session_id})")
        print(f"📄 Output lines: {result.get('output_lines', 0)}")
        print(f"💾 File size: {result.get('file_size', 0)} bytes")
        print(f"🖾 Volume file: {session_id}.jsonl")
        print(f"💡 To download manually, use Modal CLI: modal volume get uptick-crawler-outputs {session_id}.jsonl")
        
        return {"crawl_result": result}
    
    else:
        print(f"❌ Crawl failed: {result.get('message', 'Unknown error')}")
        if result.get('crawler_stderr'):
            print(f"🔍 Error details: {result['crawler_stderr'][:200]}...")
        return {"crawl_result": result}

if __name__ == "__main__":
    # Deploy the app
    app.deploy()
    print("🚀 App deployed! You can now run:")
    print("   modal run crawler/modal_deploy_real.py")
    print("   modal run crawler/modal_deploy_real.py --limit 5")
    print("   modal volume get uptick-crawler-outputs <session_id>.jsonl  # to download output")
