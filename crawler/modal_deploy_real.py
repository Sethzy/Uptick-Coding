"""
Purpose: Real Modal deployment for the targeted domain crawler
Description: This deployment uses the full crawler logic to crawl domains with 3-container concurrent processing
Key Functions: crawl_domains_concurrent (3 containers × 1 CPU + 2GB RAM)
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
        local_path="uptick-csvs/enriched-hubspot-TAM-08-25.csv",
        remote_path="/root/enriched_hubspot_tam_data.csv"
    )
)

@app.function(
    image=image,
    timeout=18000,  # 5 hour timeout (for 5000 domains)
    memory=2048,   # 2GB RAM (optimized for web crawling)
    cpu=1.0,       # 1 CPU core (optimized for I/O bound operations)
    volumes={"/mnt/crawler_outputs": crawler_volume},  # Mount volume for output storage
)
def crawl_domains_worker(
    worker_args: tuple
):
    """
    Worker function for individual containers in the concurrent setup.
    Each container gets 1 CPU + 2GB RAM for cost-effective web crawling.
    
    Args:
        worker_args: Tuple containing (limit, domain_column, id_column, session_id, from_index)
    """
    import os
    import sys
    import subprocess
    import shutil
    from pathlib import Path
    
    # Unpack the tuple arguments that Modal's .map() method passes
    limit, domain_column, id_column, session_id, from_index = worker_args
    
    # Generate session ID if not provided
    if session_id is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = f"crawl_{timestamp}_{from_index}-{from_index+limit}_1cpu_2gb"
    
    # Add the mounted crawler directory to Python path
    sys.path.insert(0, "/root")
    
    # Define output paths
    temp_output_file = "/root/output.jsonl"
    volume_output_file = f"/mnt/crawler_outputs/{session_id}.jsonl"
    
    print(f"🚀 Starting worker container with limit={limit}, from_index={from_index} (Session: {session_id})")
    print(f"💻 Container: 1 CPU + 2GB RAM (cost-optimized)")
    print(f"📁 Input CSV: /root/enriched_hubspot_tam_data.csv")
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
            "--input-csv", "/root/enriched_hubspot_tam_data.csv",
            "--output-jsonl", temp_output_file,
            "--limit", str(limit),
            "--from-index", str(from_index),
            "--column", domain_column,
            "--id-column", id_column,
            "--concurrency", "1",  # Single-threaded for 1 CPU core
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
                "container_spec": "1 CPU + 2GB RAM",
                "domains_processed": output_lines,
                "from_index": from_index,
                "limit": limit
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

@app.function(
    image=image,
    timeout=18000,  # 5 hour timeout
    memory=2048,   # 2GB RAM
    cpu=1.0,       # 1 CPU core
    volumes={"/mnt/crawler_outputs": crawler_volume},
)
def crawl_domains_concurrent(
    total_domains: int = 1000,
    domain_column: str = "Company Domain Name",
    id_column: str = "Record ID"
):
    """
    Use Modal's built-in .map() method to run containers in parallel.
    Each container gets 1 CPU + 2GB RAM for optimal cost/performance.
    
    Args:
        total_domains: Total number of domains to process
        domain_column: CSV column containing domains
        id_column: CSV column containing record IDs
    """
    from datetime import datetime
    
    # Calculate container distribution
    container_count = 3
    domains_per_container = total_domains // container_count
    
    print(f"🚀 Starting CONCURRENT crawl with {container_count} containers")
    print(f"💻 Each container: 1 CPU + 2GB RAM")
    print(f"📊 Total domains: {total_domains}")
    print(f"📦 Domains per container: {domains_per_container}")
    print(f"💰 Cost optimization: {container_count} small containers vs 1 large container")
    
    # Calculate cost comparison
    old_cost_per_hour = 0.09432  # 2 CPU + 4GB RAM
    new_cost_per_hour = 0.04716  # 1 CPU + 2GB RAM
    total_new_cost_per_hour = new_cost_per_hour * container_count
    
    print(f"💰 Cost comparison:")
    print(f"   Old setup (1 container): ${old_cost_per_hour:.5f}/hour")
    print(f"   New setup ({container_count} containers): ${total_new_cost_per_hour:.5f}/hour")
    print(f"   Cost difference: ${total_new_cost_per_hour - old_cost_per_hour:.5f}/hour")
    
    # Prepare inputs for .map() - each tuple represents one container's work
    map_inputs = []
    for i in range(container_count):
        start_index = i * domains_per_container
        end_index = start_index + domains_per_container
        
        # Adjust last container to handle remainder
        if i == container_count - 1:
            end_index = total_domains
        
        actual_limit = end_index - start_index
        
        print(f"📦 Container {i+1}: domains {start_index}-{end_index-1} (limit: {actual_limit})")
        
        # Create input tuple for this container
        container_input = (
            actual_limit,                    # limit
            domain_column,                   # domain_column
            id_column,                       # id_column
            f"concurrent_batch_{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",  # session_id
            start_index                      # from_index
        )
        map_inputs.append(container_input)
    
    print(f"🔄 Launching {container_count} containers using Modal's .map() method!")
    print(f"⏱️  Expected completion: ~{total_domains * 2 / 60:.1f} minutes (vs ~{total_domains * 2 / 60 * 3:.1f} minutes with 1 container)")
    
    # Use Modal's .map() method for true parallel execution
    # This will launch all containers simultaneously and wait for all to complete
    results = crawl_domains_worker.map(map_inputs)
    
    # Collect results from all containers
    all_results = []
    total_processed = 0
    successful_containers = 0
    
    for i, result in enumerate(results):
        all_results.append(result)
        
        if result.get('status') == 'success':
            successful_containers += 1
            total_processed += result.get('domains_processed', 0)
            print(f"✅ Container {i+1} completed successfully: {result.get('domains_processed', 0)} domains")
        else:
            print(f"❌ Container {i+1} failed: {result.get('message', 'Unknown error')}")
    
    print(f"📊 Final Results:")
    print(f"   Successful containers: {successful_containers}/{container_count}")
    print(f"   Total domains processed: {total_processed}")
    print(f"   All results: {all_results}")
    
    return {
        "status": "completed",
        "container_count": container_count,
        "total_domains": total_domains,
        "domains_per_container": domains_per_container,
        "cost_per_hour": total_new_cost_per_hour,
        "successful_containers": successful_containers,
        "total_processed": total_processed,
        "container_results": all_results,
        "message": f"Completed {container_count} containers with 1 CPU + 2GB RAM each"
    }

@app.local_entrypoint()
def main(
    total_domains: int = 1000,
    domain_column: str = "Company Domain Name",
    id_column: str = "Record ID"
):
    """
    Local entrypoint for running the concurrent crawler.
    
    Args:
        total_domains: Total domains to process
        domain_column: CSV column containing domains
        id_column: CSV column containing record IDs
    """
    print(f"🚀 Starting Modal crawler with 3-container concurrent setup...")
    print(f"🔄 Using 3-container concurrent setup")
    print(f"💻 Each container: 1 CPU + 2GB RAM")
    print(f"📊 Total domains to process: {total_domains}")
    
    # Calculate cost comparison
    old_cost_per_hour = 0.09432  # 2 CPU + 4GB RAM
    new_cost_per_hour = 0.04716  # 1 CPU + 2GB RAM
    total_new_cost_per_hour = new_cost_per_hour * 3
    
    print(f"💰 Cost Analysis:")
    print(f"   Old setup (1 container): ${old_cost_per_hour:.5f}/hour")
    print(f"   New setup (3 containers): ${total_new_cost_per_hour:.5f}/hour")
    print(f"   Cost difference: ${total_new_cost_per_hour - old_cost_per_hour:.5f}/hour")
    print(f"   Performance gain: 3x faster completion")
    
    # Run the concurrent crawler
    result = crawl_domains_concurrent.remote(
        total_domains=total_domains,
        domain_column=domain_column,
        id_column=id_column
    )
    
    print(f"\n🎉 Concurrent crawl completed!")
    print(f"📊 Final Status: {result['status']}")
    print(f"📦 Containers used: {result['container_count']}")
    print(f"✅ Successful containers: {result['successful_containers']}/{result['container_count']}")
    print(f"🌐 Total domains processed: {result['total_processed']}")
    
    # Show individual container results
    if result.get('container_results'):
        print(f"\n📋 Container Results:")
        for i, container_result in enumerate(result['container_results']):
            if container_result.get('status') == 'success':
                print(f"   Container {i+1}: ✅ {container_result.get('domains_processed', 0)} domains, {container_result.get('file_size', 0)} bytes")
                print(f"     Output file: {container_result.get('volume_file', 'N/A')}")
            else:
                print(f"   Container {i+1}: ❌ {container_result.get('message', 'Unknown error')}")
    
    print(f"\n💡 To download results manually, use Modal CLI:")
    if result.get('container_results'):
        for container_result in result['container_results']:
            if container_result.get('status') == 'success' and container_result.get('volume_file'):
                print(f"   modal volume get uptick-crawler-outputs {container_result['volume_file']}")
    
    return {"concurrent_result": result}

if __name__ == "__main__":
    # Deploy the app
    app.deploy()
    print("🚀 App deployed! You can now run:")
    print("   modal run crawler/modal_deploy_real.py --total-domains 1000")
    print("   modal volume get uptick-crawler-outputs <session_id>.jsonl  # to download output")
