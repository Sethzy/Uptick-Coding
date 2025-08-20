#!/usr/bin/env python3
"""
Quick analysis script for scoring results
"""

import json

def analyze_results(filename):
    with open(filename, 'r') as f:
        data = [json.loads(line) for line in f]
    
    print(f"Total records: {len(data)}")
    
    # Analyze classifications
    classifications = {}
    scores = []
    
    for record in data:
        cls = record.get('classification', 'Unknown')
        classifications[cls] = classifications.get(cls, 0) + 1
        scores.append(record.get('numerical_score', 0))
    
    print(f"\nClassifications:")
    for k, v in sorted(classifications.items()):
        print(f"  {k}: {v}")
    
    print(f"\nScore Statistics:")
    print(f"  Average: {sum(scores)/len(scores):.1f}")
    print(f"  Min: {min(scores)}")
    print(f"  Max: {max(scores)}")
    print(f"  High scores (40+): {len([s for s in scores if s >= 40])}")
    print(f"  Low scores (0-): {len([s for s in scores if s <= 0])}")
    
    # Show some examples of high-scoring records
    high_scoring = [r for r in data if r.get('numerical_score', 0) >= 40]
    if high_scoring:
        print(f"\nHigh-scoring examples (score >= 40):")
        for record in high_scoring[:5]:  # Show first 5
            print(f"  {record.get('domain', 'Unknown')}: {record.get('classification', 'Unknown')} (score: {record.get('numerical_score', 0)})")

if __name__ == "__main__":
    analyze_results('crawl-runs/concurrent_batch_1_20250820_044213_enriched_scored.jsonl')
