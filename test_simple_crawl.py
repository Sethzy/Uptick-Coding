"""
Purpose: Test script for the simple Modal crawler
Description: Tests the test_crawl_simple function
"""

import modal

def test_simple_crawler():
    """Test the simple deployed crawler."""
    print("🧪 Testing simple Modal crawler...")
    
    try:
        # Get the deployed function
        crawl_fn = modal.Function.from_name("uptick-crawler-simple-v2", "test_crawl_simple")
        print("✅ Found deployed function")
        
        # Test with minimal parameters - just 1 domain
        print("🚀 Starting simple crawl test...")
        print("📝 This will test: firepumpsystems.co")
        
        # Call the remote function (no CSV path needed - it's mounted)
        result = crawl_fn.remote(limit=1)
        
        print("📊 Crawl Result:")
        print(f"Status: {result.get('status', 'unknown')}")
        
        if result.get('status') == 'success':
            print(f"🏢 Company: {result.get('company', 'unknown')}")
            print(f"🌐 Domain: {result.get('domain', 'unknown')}")
            print(f"📊 CSV Rows: {result.get('csv_rows', 'unknown')}")
            print(f"🔍 Test Type: {result.get('test_type', 'unknown')}")
            print("✅ Test completed successfully!")
        else:
            print(f"❌ Error: {result.get('error', 'unknown error')}")
            
        return result
        
    except Exception as e:
        print(f"❌ Error testing crawler: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_simple_crawler()
