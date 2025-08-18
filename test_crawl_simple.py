"""
Purpose: Simple test for the deployed Modal crawler
Description: Tests the remote function directly without local module dependencies
"""

import modal

def test_remote_crawler():
    """Test the deployed crawler by calling it remotely."""
    print("🧪 Testing deployed Modal crawler (remote)...")
    
    try:
        # Get the deployed function
        crawl_fn = modal.Function.from_name("uptick-crawler", "crawl_domains")
        print("✅ Found deployed function")
        
        # Test with minimal parameters - just 1 domain
        print("🚀 Starting remote crawl (limit=1)...")
        print("📝 This will crawl: firepumpsystems.co")
        
        # Call the remote function
        result = crawl_fn.remote(
            limit=1,
            input_csv_path="uptick-csvs/test.csv"
        )
        
        print("📊 Crawl Result:")
        print(f"Status: {result.get('status', 'unknown')}")
        print(f"Result Code: {result.get('result_code', 'unknown')}")
        print(f"Domains Processed: {result.get('domains_processed', 'unknown')}")
        
        if result.get('status') == 'error':
            print(f"❌ Error: {result.get('error', 'unknown error')}")
        else:
            print("✅ Crawl completed successfully!")
            
        return result
        
    except Exception as e:
        print(f"❌ Error testing crawler: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_remote_crawler()

