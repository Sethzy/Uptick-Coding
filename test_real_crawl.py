"""
Purpose: Test script for the real Modal crawler
Description: Tests the crawl_domains_real function to get actual crawl output
"""

import modal

def test_real_crawler():
    """Test the real deployed crawler to get actual output."""
    print("🧪 Testing REAL Modal crawler...")
    
    try:
        # Get the deployed function
        crawl_fn = modal.Function.from_name("uptick-crawler-real", "crawl_domains_real")
        print("✅ Found deployed function")
        
        # Test with 1 domain to get real output
        print("🚀 Starting REAL crawl (limit=1)...")
        print("📝 This will crawl: firepumpsystems.co")
        
        # Call the remote function
        result = crawl_fn.remote(
            limit=1,
            domain_column="Company Domain Name",
            id_column="Record ID"
        )
        
        print("📊 Crawl Result:")
        print(f"Status: {result.get('status', 'unknown')}")
        
        if result.get('status') == 'success':
            print(f"✅ Result Code: {result.get('result_code')}")
            print(f"📄 Output Lines: {result.get('output_lines')}")
            print(f"📁 Output File Size: {result.get('output_file_size')} bytes")
            print(f"🏢 Domains Processed: {result.get('domains_processed')}")
            
            # Save the output file locally
            if result.get('output_file_content'):
                output_content = result['output_file_content']
                with open('modal_real_crawl_output.jsonl', 'w', encoding='utf-8') as f:
                    f.write(output_content)
                print(f"💾 Output saved to: modal_real_crawl_output.jsonl")
                
                # Show first few lines of output
                lines = output_content.strip().split('\n')
                print(f"\n📋 First few lines of output:")
                for i, line in enumerate(lines[:3]):
                    print(f"  {i+1}: {line[:100]}{'...' if len(line) > 100 else ''}")
                    
        elif result.get('status') == 'warning':
            print(f"⚠️  Warning: {result.get('message')}")
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_real_crawler()

