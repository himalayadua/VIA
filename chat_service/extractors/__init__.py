"""
Content Extractors for Via Canvas

Specialized extractors for different content types:
- URLExtractor: Base class for all extractors
- DocumentationExtractor: HTML documentation sites
- GitHubExtractor: GitHub repositories
- VideoExtractor: YouTube and other video platforms
- EnhancedExtractor: Multi-method extractor with fallback chain (FREE)
- ExtractionOrchestrator: Coordinates extraction with caching (FREE)

MarkItDown-inspired components:
- StreamInfo: Unified metadata container
- BaseConverter: Base class for all converters
- ConversionResult: Standardized conversion result
- ConverterRegistry: Priority-based converter management
- PDFConverter: PDF to markdown conversion
- ImageConverter: Image OCR and LLM description
- FileDetector: Content-based file type detection
"""

from .url_extractor import URLExtractor, URLType
from .documentation_extractor import DocumentationExtractor
from .github_extractor import GitHubExtractor
from .video_extractor import VideoExtractor
from .enhanced_extractor import EnhancedExtractor
from .extraction_orchestrator import ExtractionOrchestrator

# MarkItDown-inspired components
from .stream_info import StreamInfo
from .base_converter import BaseConverter, ConversionResult
from .converter_registry import ConverterRegistry, PRIORITY_SPECIFIC, PRIORITY_GENERIC
from .pdf_converter import PDFConverter
from .image_converter import ImageConverter
from .file_detector import FileDetector
from .unified_extractor import UnifiedExtractor

__all__ = [
    # Original extractors
    'URLExtractor',
    'URLType',
    'DocumentationExtractor',
    'GitHubExtractor',
    'VideoExtractor',
    'EnhancedExtractor',
    'ExtractionOrchestrator',
    
    # MarkItDown-inspired
    'StreamInfo',
    'BaseConverter',
    'ConversionResult',
    'ConverterRegistry',
    'PRIORITY_SPECIFIC',
    'PRIORITY_GENERIC',
    'PDFConverter',
    'ImageConverter',
    'FileDetector',
    'UnifiedExtractor',  # Main interface
]
