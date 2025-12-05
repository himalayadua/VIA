"""
Test Unified Extraction System

Tests the MarkItDown-inspired extraction features:
- PDF extraction
- Image extraction with OCR
- File type detection
- Converter registry
"""

import asyncio
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_pdf_extraction():
    """Test PDF extraction."""
    print("\n" + "="*60)
    print("TEST 1: PDF Extraction")
    print("="*60)
    
    from extractors import UnifiedExtractor
    
    # Create extractor
    extractor = UnifiedExtractor(use_cache=False)
    
    # Test with a sample PDF (you'll need to provide one)
    pdf_path = "tests/data/sample.pdf"
    
    if not Path(pdf_path).exists():
        print(f"⚠️  PDF file not found: {pdf_path}")
        print("   Create a sample PDF to test this feature")
        return
    
    try:
        result = await extractor.extract(pdf_path)
        
        print(f"\n✅ PDF Extraction Result:")
        print(f"   Title: {result['title']}")
        print(f"   Success: {result['success']}")
        print(f"   Method: {result.get('extraction_method', 'N/A')}")
        print(f"   Content length: {len(result.get('content', ''))} chars")
        print(f"   Metadata: {result.get('metadata', {})}")
        
        if result['success']:
            print(f"\n   First 200 chars of content:")
            print(f"   {result['content'][:200]}...")
        
    except Exception as e:
        print(f"❌ PDF extraction failed: {e}")


async def test_image_extraction():
    """Test image extraction with OCR."""
    print("\n" + "="*60)
    print("TEST 2: Image Extraction (OCR)")
    print("="*60)
    
    from extractors import UnifiedExtractor
    
    # Create extractor (without LLM for now)
    extractor = UnifiedExtractor(use_cache=False)
    
    # Test with a sample image
    image_path = "tests/data/sample.png"
    
    if not Path(image_path).exists():
        print(f"⚠️  Image file not found: {image_path}")
        print("   Create a sample image to test this feature")
        return
    
    try:
        result = await extractor.extract(image_path, use_ocr=True)
        
        print(f"\n✅ Image Extraction Result:")
        print(f"   Title: {result['title']}")
        print(f"   Success: {result['success']}")
        print(f"   Method: {result.get('extraction_method', 'N/A')}")
        print(f"   Metadata: {result.get('metadata', {})}")
        
        if result['success']:
            print(f"\n   Content:")
            print(f"   {result['content'][:500]}...")
        
    except Exception as e:
        print(f"❌ Image extraction failed: {e}")


async def test_file_detection():
    """Test file type detection."""
    print("\n" + "="*60)
    print("TEST 3: File Type Detection")
    print("="*60)
    
    from extractors import FileDetector, StreamInfo
    import io
    
    # Test PDF detection
    pdf_magic = b'%PDF-1.4\n'
    stream = io.BytesIO(pdf_magic)
    
    guesses = FileDetector.detect(stream)
    
    print(f"\n✅ PDF Magic Bytes Detection:")
    for i, guess in enumerate(guesses, 1):
        print(f"   Guess {i}: {guess}")
    
    # Test JPEG detection
    jpeg_magic = b'\xFF\xD8\xFF\xE0\x00\x10JFIF'
    stream = io.BytesIO(jpeg_magic)
    
    guesses = FileDetector.detect(stream)
    
    print(f"\n✅ JPEG Magic Bytes Detection:")
    for i, guess in enumerate(guesses, 1):
        print(f"   Guess {i}: {guess}")
    
    # Test with extension hint
    base_info = StreamInfo(extension='.pdf', filename='document.pdf')
    stream = io.BytesIO(b'some content')
    
    guesses = FileDetector.detect(stream, base_info)
    
    print(f"\n✅ Extension-based Detection:")
    for i, guess in enumerate(guesses, 1):
        print(f"   Guess {i}: {guess}")


async def test_converter_registry():
    """Test converter registry."""
    print("\n" + "="*60)
    print("TEST 4: Converter Registry")
    print("="*60)
    
    from extractors import (
        ConverterRegistry,
        PDFConverter,
        ImageConverter,
        PRIORITY_SPECIFIC
    )
    
    # Create registry
    registry = ConverterRegistry()
    
    # Register converters
    registry.register(PDFConverter(), priority=PRIORITY_SPECIFIC)
    registry.register(ImageConverter(), priority=PRIORITY_SPECIFIC)
    
    # Get converters
    converters = registry.get_converters()
    
    print(f"\n✅ Registered Converters:")
    for i, converter in enumerate(converters, 1):
        print(f"   {i}. {converter.get_name()}")
    
    # Get stats
    stats = registry.get_stats()
    
    print(f"\n✅ Registry Stats:")
    for key, value in stats.items():
        print(f"   {key}: {value}")


async def test_url_extraction():
    """Test URL extraction (existing functionality)."""
    print("\n" + "="*60)
    print("TEST 5: URL Extraction")
    print("="*60)
    
    from extractors import UnifiedExtractor
    
    # Create extractor
    extractor = UnifiedExtractor(use_cache=False)
    
    # Test with a simple URL
    test_url = "https://example.com"
    
    try:
        result = await extractor.extract(test_url)
        
        print(f"\n✅ URL Extraction Result:")
        print(f"   URL: {test_url}")
        print(f"   Title: {result['title']}")
        print(f"   Success: {result['success']}")
        print(f"   Method: {result.get('extraction_method', 'N/A')}")
        print(f"   Content length: {len(result.get('content', ''))} chars")
        
        if result['success']:
            print(f"\n   First 200 chars:")
            print(f"   {result['content'][:200]}...")
        
    except Exception as e:
        print(f"❌ URL extraction failed: {e}")


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("UNIFIED EXTRACTION SYSTEM TESTS")
    print("="*60)
    
    # Run tests
    await test_file_detection()
    await test_converter_registry()
    await test_url_extraction()
    await test_pdf_extraction()
    await test_image_extraction()
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETE")
    print("="*60)
    print("\nNote: PDF and Image tests require sample files in tests/data/")
    print("Create sample.pdf and sample.png to test those features.")


if __name__ == "__main__":
    asyncio.run(main())
