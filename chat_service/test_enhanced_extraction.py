#!/usr/bin/env python3
"""
Test script for enhanced content extraction.

Tests the hybrid fallback chain with free tools.
"""

import asyncio
import sys
from extractors import ExtractionOrchestrator

async def test_single_url(url: str):
    """Test extraction for a single URL."""
    print(f"\n{'='*70}")
    print(f"Testing: {url}")
    print('='*70)
    
    orchestrator = ExtractionOrchestrator(use_cache=True)
    
    try:
        result = await orchestrator.extract_url(url, method="auto", format="markdown")
        
        print(f"\n✅ Success: {result['success']}")
        print(f"📝 Title: {result['title']}")
        print(f"🔧 Method: {result['extraction_method']}")
        print(f"💾 Cached: {result['cached']}")
        print(f"⏱️  Time: {result.get('extraction_time', 0):.2f}s")
        print(f"📊 Content length: {len(result['content'])} characters")
        
        if result['success']:
            print(f"\n📄 First 300 characters of content:")
            print("-" * 70)
            print(result['content'][:300])
            print("...")
            print("-" * 70)
        else:
            print(f"\n❌ Error: {result.get('error', 'Unknown error')}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_multiple_urls():
    """Test extraction for multiple URLs."""
    print("\n" + "="*70)
    print("ENHANCED CONTENT EXTRACTION TEST")
    print("="*70)
    
    test_urls = [
        ("Wikipedia", "https://en.wikipedia.org/wiki/Artificial_intelligence"),
        ("GitHub", "https://github.com/microsoft/vscode"),
        ("News Article", "https://www.bbc.com/news"),
        ("Documentation", "https://docs.python.org/3/tutorial/"),
    ]
    
    orchestrator = ExtractionOrchestrator(use_cache=True)
    results = []
    
    for name, url in test_urls:
        print(f"\n{'='*70}")
        print(f"Test {len(results) + 1}/{len(test_urls)}: {name}")
        print(f"URL: {url}")
        print('='*70)
        
        try:
            result = await orchestrator.extract_url(url, method="auto", format="markdown")
            results.append((name, result))
            
            print(f"✅ Success: {result['success']}")
            print(f"🔧 Method: {result['extraction_method']}")
            print(f"⏱️  Time: {result.get('extraction_time', 0):.2f}s")
            print(f"📊 Length: {len(result['content'])} chars")
            
        except Exception as e:
            print(f"❌ Failed: {e}")
            results.append((name, None))
    
    # Print summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print('='*70)
    
    successful = sum(1 for _, r in results if r and r.get('success'))
    print(f"✅ Successful: {successful}/{len(results)}")
    
    # Print stats
    stats = orchestrator.get_stats()
    print(f"\n📊 Extraction Statistics:")
    print(f"   Total extractions: {stats['total_extractions']}")
    print(f"   Cache hits: {stats['cache_hits']}")
    print(f"   Cache hit rate: {stats['cache_hit_rate']}")
    print(f"   Methods used: {stats['method_usage']}")
    
    return results

async def test_fallback_chain():
    """Test that fallback chain works."""
    print("\n" + "="*70)
    print("TESTING FALLBACK CHAIN")
    print("="*70)
    
    # Test with a difficult URL
    url = "https://example.com"
    
    orchestrator = ExtractionOrchestrator(use_cache=False)
    result = await orchestrator.extract_url(url)
    
    print(f"\nURL: {url}")
    print(f"Method used: {result['extraction_method']}")
    print(f"Success: {result['success']}")
    
    if result['success']:
        print("✅ Fallback chain working correctly!")
    else:
        print("⚠️  All methods failed (this is OK for some URLs)")

async def main():
    """Main test function."""
    if len(sys.argv) > 1:
        # Test single URL from command line
        url = sys.argv[1]
        await test_single_url(url)
    else:
        # Run full test suite
        print("\n🚀 Starting Enhanced Extraction Tests...")
        print("This will test multiple extraction methods with real URLs.\n")
        
        # Test multiple URLs
        await test_multiple_urls()
        
        # Test fallback chain
        await test_fallback_chain()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS COMPLETE")
        print("="*70)
        print("\nTo test a specific URL, run:")
        print("  python test_enhanced_extraction.py <url>")
        print("\nExample:")
        print("  python test_enhanced_extraction.py https://en.wikipedia.org/wiki/Python\n")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
