"""
Unified Content Extractor

Combines MarkItDown-inspired converters with existing extraction logic.
Provides a single interface for all content extraction needs.
"""

import logging
import io
from typing import Dict, Optional, Union, BinaryIO
from pathlib import Path

from .stream_info import StreamInfo
from .converter_registry import ConverterRegistry, PRIORITY_SPECIFIC, PRIORITY_GENERIC
from .pdf_converter import PDFConverter
from .image_converter import ImageConverter
from .file_detector import FileDetector
from .extraction_orchestrator import ExtractionOrchestrator

logger = logging.getLogger(__name__)


class UnifiedExtractor:
    """
    Unified content extractor combining multiple extraction strategies.
    
    Features:
    - File-based extraction (PDF, images, etc.) using converters
    - URL-based extraction using orchestrator
    - Automatic file type detection
    - LLM integration for image descriptions
    - Priority-based fallback logic
    """
    
    def __init__(
        self,
        use_cache: bool = True,
        llm_client=None,
        llm_model: Optional[str] = None
    ):
        """
        Initialize unified extractor.
        
        Args:
            use_cache: Whether to cache URL extractions
            llm_client: OpenAI-compatible client for LLM features
            llm_model: Model name for LLM features
        """
        # Initialize converter registry
        self.registry = ConverterRegistry()
        
        # Register converters (in priority order)
        self.registry.register(PDFConverter(), priority=PRIORITY_SPECIFIC)
        self.registry.register(ImageConverter(), priority=PRIORITY_SPECIFIC)
        
        # Initialize URL orchestrator
        self.orchestrator = ExtractionOrchestrator(use_cache=use_cache)
        
        # Store LLM config
        self.llm_client = llm_client
        self.llm_model = llm_model
        
        logger.info("UnifiedExtractor initialized")
    
    async def extract(
        self,
        source: Union[str, Path, BinaryIO],
        **kwargs
    ) -> Dict:
        """
        Extract content from any source.
        
        Automatically detects source type and uses appropriate extractor:
        - URLs: Use orchestrator with enhanced extraction
        - Local files: Use converter registry
        - Binary streams: Use converter registry
        
        Args:
            source: URL, file path, or binary stream
            **kwargs: Additional options:
                - format: Output format ('markdown', 'text', 'html')
                - method: Extraction method for URLs
                - use_ocr: Whether to use OCR for images
                - llm_prompt: Custom prompt for LLM descriptions
                
        Returns:
            Dictionary with extracted content:
            {
                "title": str,
                "content": str,
                "text": str,
                "metadata": dict,
                "success": bool,
                "extraction_method": str
            }
        """
        # Determine source type
        if isinstance(source, str):
            if source.startswith(('http://', 'https://')):
                # URL extraction
                return await self._extract_url(source, **kwargs)
            else:
                # Local file path
                return await self._extract_file(source, **kwargs)
        elif isinstance(source, Path):
            # Path object
            return await self._extract_file(str(source), **kwargs)
        elif hasattr(source, 'read'):
            # Binary stream
            return await self._extract_stream(source, **kwargs)
        else:
            raise TypeError(f"Unsupported source type: {type(source)}")
    
    async def _extract_url(self, url: str, **kwargs) -> Dict:
        """Extract content from URL using orchestrator."""
        try:
            result = await self.orchestrator.extract_url(
                url,
                method=kwargs.get('method', 'auto'),
                format=kwargs.get('format', 'markdown')
            )
            
            return result
            
        except Exception as e:
            logger.error(f"URL extraction failed: {e}")
            return {
                "title": url,
                "content": "",
                "text": "",
                "metadata": {"url": url, "error": str(e)},
                "success": False,
                "extraction_method": "none",
                "error": str(e)
            }
    
    async def _extract_file(self, file_path: str, **kwargs) -> Dict:
        """Extract content from local file using converters."""
        try:
            # Build base StreamInfo from file path
            path_obj = Path(file_path)
            base_info = StreamInfo(
                local_path=file_path,
                filename=path_obj.name,
                extension=path_obj.suffix
            )
            
            # Open file and extract
            with open(file_path, 'rb') as f:
                return await self._extract_stream(f, base_info=base_info, **kwargs)
                
        except Exception as e:
            logger.error(f"File extraction failed: {e}")
            return {
                "title": Path(file_path).name,
                "content": "",
                "text": "",
                "metadata": {"file": file_path, "error": str(e)},
                "success": False,
                "extraction_method": "none",
                "error": str(e)
            }
    
    async def _extract_stream(
        self,
        stream: BinaryIO,
        base_info: Optional[StreamInfo] = None,
        **kwargs
    ) -> Dict:
        """Extract content from binary stream using converters."""
        try:
            if base_info is None:
                base_info = StreamInfo()
            
            # Detect file type
            guesses = FileDetector.detect(stream, base_info)
            
            # Try conversion with each guess
            for stream_info in guesses:
                logger.info(f"Trying conversion with: {stream_info}")
                
                # Prepare kwargs for converters
                converter_kwargs = {
                    'llm_client': self.llm_client,
                    'llm_model': self.llm_model,
                    'use_ocr': kwargs.get('use_ocr', True),
                    'llm_prompt': kwargs.get('llm_prompt')
                }
                
                # Try conversion
                result = self.registry.convert(
                    stream,
                    stream_info,
                    **converter_kwargs
                )
                
                if result.success:
                    # Convert to dict format
                    return {
                        "title": result.title,
                        "content": result.content,
                        "text": result.text,
                        "html": result.html,
                        "metadata": result.metadata,
                        "success": True,
                        "extraction_method": "converter"
                    }
            
            # All guesses failed
            return {
                "title": base_info.filename or "Unknown",
                "content": "",
                "text": "",
                "metadata": {"error": "No converter could handle this content"},
                "success": False,
                "extraction_method": "none",
                "error": "No converter could handle this content"
            }
            
        except Exception as e:
            logger.error(f"Stream extraction failed: {e}")
            return {
                "title": "Unknown",
                "content": "",
                "text": "",
                "metadata": {"error": str(e)},
                "success": False,
                "extraction_method": "none",
                "error": str(e)
            }
    
    def get_stats(self) -> Dict:
        """Get extraction statistics from all components."""
        return {
            "converter_stats": self.registry.get_stats(),
            "orchestrator_stats": self.orchestrator.get_stats()
        }
