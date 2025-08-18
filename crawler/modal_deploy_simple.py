"""
Purpose: Simple Modal deployment for testing basic crawler functionality
Description: Minimal deployment to test Modal function execution
"""

import modal
from pathlib import Path

# Create Modal app with new name
app = modal.App("uptick-crawler-simple-v2")

# Define the container image with necessary dependencies
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "pandas",     # CSV handling
        "requests",   # HTTP requests
    )
    # Mount the CSV file
    .add_local_file(
        local_path="uptick-csvs/test.csv",
        remote_path="/root/test.csv"
    )
)

@app.function(
    image=image,
    timeout=300,  # 5 minute timeout
    memory=1024,  # 1GB RAM
    cpu=0.5,      # 0.5 CPU core
)
def test_crawl_simple(
    limit: int = 1
):
    """
    Simple test function to verify Modal deployment works.
    """
    import pandas as pd
    import requests
    import time
    
    print(f"🧪 Starting simple crawl test...")
    print(f"📁 Input CSV: /root/test.csv")
    print(f"🔢 Limit: {limit}")
    
    try:
        # Read the CSV
        print("📖 Reading CSV file...")
        df = pd.read_csv("/root/test.csv")
        print(f"✅ CSV loaded with {len(df)} rows")
        
        # Get the first domain
        if len(df) > 0:
            domain = df.iloc[0]['Company Domain Name']
            company = df.iloc[0]['Company name']
            print(f"🏢 Company: {company}")
            print(f"🌐 Domain: {domain}")
            
            # Simple HTTP test
            print(f"🔍 Testing domain accessibility...")
            try:
                response = requests.get(f"https://{domain}", timeout=10)
                print(f"✅ HTTP Status: {response.status_code}")
                print(f"📄 Content Length: {len(response.text)} characters")
                
                # Extract some basic info
                title_start = response.text.find('<title>')
                title_end = response.text.find('</title>')
                if title_start != -1 and title_end != -1:
                    title = response.text[title_start + 7:title_end].strip()
                    print(f"📝 Page Title: {title}")
                
            except Exception as e:
                print(f"⚠️  HTTP test failed: {e}")
            
            return {
                "status": "success",
                "company": company,
                "domain": domain,
                "csv_rows": len(df),
                "test_type": "simple_http_check"
            }
        else:
            return {
                "status": "error",
                "error": "CSV file is empty"
            }
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "error": str(e)
        }

@app.local_entrypoint()
def main():
    """Local entrypoint for testing."""
    print("Testing simple Modal crawler...")
    
    result = test_crawl_simple.remote(
        limit=1
    )
    
    print(f"Test result: {result}")

if __name__ == "__main__":
    # Deploy the app
    app.deploy()
