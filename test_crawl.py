"""
Purpose: Test script for the deployed Modal crawler
Description: Tests the crawl_domains function with minimal parameters
"""

import modal

def test_crawler():
    """Test the deployed crawler with 1 domain."""
    print("🧪 Testing deployed Modal crawler...")
    
    try:
        # Get the deployed function
        crawl_fn = modal.Function.from_name("uptick-crawler", "crawl_domains")
        print("✅ Found deployed function")
        
        # Test with minimal parameters - just 1 domain
        print("🚀 Starting test crawl (limit=1)...")
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
        return None

if __name__ == "__main__":
    test_crawler()

