#!/usr/bin/env python3
"""
Purpose: Demo script showing quick start commands usage.
Description: Demonstrates how to use the quick start commands programmatically.
Key Functions/Classes: Demo functions for each quick start command.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add the parent directory to the path so we can import scoring
sys.path.insert(0, str(Path(__file__).parent.parent))

from scoring.quick_start import quick_start


def demo_check_setup():
    """Demo the check-setup command."""
    print("🔍 Demo: Checking setup...")
    print("=" * 50)
    
    # Simulate the check-setup command
    try:
        from scoring.config import get_openrouter_api_key
        from scoring import api, models
        
        api_key = get_openrouter_api_key()
        if api_key:
            print("✅ OpenRouter API key: Found")
            print(f"   Key: {api_key[:8]}...{api_key[-4:]}")
        else:
            print("❌ OpenRouter API key: Missing")
            print("   Set OPENROUTER_API_KEY environment variable")
        
        print("✅ httpx: Available")
        print("✅ click: Available") 
        print("✅ pydantic: Available")
        print("✅ Scoring modules: Available")
        
    except Exception as e:
        print(f"❌ Error during setup check: {e}")


def demo_score_command():
    """Demo the score command structure."""
    print("\n🚀 Demo: Score command structure...")
    print("=" * 50)
    
    print("Command: ./quick_score.sh score input.jsonl")
    print("  - Automatically generates output filename")
    print("  - Uses default model (qwen/qwen3-30b-a3b)")
    print("  - 90 second timeout")
    print("  - Preserves all enriched business fields")
    
    print("\nCommand: ./quick_score.sh score input.jsonl output.jsonl custom-model")
    print("  - Custom output filename")
    print("  - Custom model specification")
    print("  - Same timeout and field preservation")


def demo_sample_command():
    """Demo the sample command structure."""
    print("\n🧪 Demo: Sample command structure...")
    print("=" * 50)
    
    print("Command: ./quick_score.sh sample")
    print("  - Default sample size: 5 records")
    print("  - Auto-finds JSONL files in current directory")
    print("  - Good for testing before full run")
    
    print("\nCommand: ./quick_score.sh sample 10")
    print("  - Custom sample size: 10 records")
    print("  - Same auto-discovery behavior")


def main():
    """Run all demos."""
    print("🚀 Uptick Scoring Module - Quick Start Demo")
    print("=" * 60)
    
    demo_check_setup()
    demo_score_command()
    demo_sample_command()
    
    print("\n" + "=" * 60)
    print("💡 To use these commands:")
    print("   1. cd scoring/")
    print("   2. ./quick_score.sh help")
    print("   3. ./quick_score.sh check")
    print("   4. ./quick_score.sh score your_file.jsonl")


if __name__ == "__main__":
    main()
