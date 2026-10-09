#!/usr/bin/env python
"""Quick test script to debug the realtime analysis"""
import sys
import os
sys.path.insert(0, 'D:/Ai Infosys/backend')
os.chdir('D:/Ai Infosys/backend')

from services.realtime_analysis import RealtimeAnalyzer
import json

print("=" * 80)
print("Testing RealtimeAnalyzer directly...")
print("=" * 80)

analyzer = RealtimeAnalyzer()

# Test with a simple product search
test_products = ["iPhone", "shoes"]

for product in test_products:
    print(f"\n\nTesting: {product}")
    print("-" * 80)
    try:
        result = analyzer.analyze_product(product=product, max_articles=25, force_refresh=True)
        
        print(f"Analysis Complete!")
        print(f"   Articles: {result.get('article_count', 0)}")
        print(f"   Source: {result.get('source', 'unknown')}")
        print(f"   Sentiment: {result.get('sentiment_breakdown', {})}")
        print(f"   Score: {result.get('sentiment_score', 0)}")
        
        if result.get('demographics'):
            print(f"   Gender: {result['demographics'].get('gender', {})}")
            locs = result['demographics'].get('location', {})
            print(f"   Locations: {locs}")
        
        print(f"   Insights (first 2):")
        for insight in result.get('insights', [])[:2]:
            print(f"     - {insight}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

print("\n\n" + "=" * 80)
print("Test Complete")
print("=" * 80)
