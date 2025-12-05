"""
PDF Converter

Extracts text content from PDF files using PyMuPDF (faster than pdfminer).
Inspired by MarkItDown's PDF converter but using PyMuPDF for better performance.
"""

import logging
import io
from typing import BinaryIO, Any

from .base_converter import BaseConverter, ConversionResult
from .stream_info import StreamInfo

logger = logging.getLogger(__name__)


ACCEPTED_MIME_TYPES = [
    "application/pdf",
    "application/x-pdf",
]

ACCEPTED_EXTENSIONS = [".pdf"]


class PDFConverter(BaseConverter):
    """
    Converts PDF files to markdown/text.
    
    Uses PyMuPDF (fitz) for fast and accurate text extraction.
    Handles Unicode properly and preserves document structure.
    """
    
    def accepts(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any
    ) -> bool:
        """Check if this is a PDF file."""
        mimetype = (stream_info.mimetype or "").lower()
        extension = (stream_info.extension or "").lower()
        
        # Check extension
        if extension in ACCEPTED_EXTENSIONS:
            return True
        
        # Check mimetype
        for accepted_type in ACCEPTED_MIME_TYPES:
            if mimetype.startswith(accepted_type):
                return True
        
        return False
    
    def convert(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any
    ) -> ConversionResult:
        """
        Extract text from PDF.
        
        Args:
            file_stream: PDF file stream
            stream_info: File metadata
            **kwargs: Additional options
            
        Returns:
            ConversionResult with extracted text
        """
        try:
            import pymupdf  # PyMuPDF
            import unicodedata
        except ImportError:
            logger.error("PyMuPDF not installed. Install with: pip install pymupdf")
            return ConversionResult(
                title=stream_info.filename or "PDF Document",
                content="",
                success=False,
                error="PyMuPDF not installed"
            )
        
        cur_pos = file_stream.tell()
        
        try:
            # Read PDF from stream
            pdf_bytes = file_stream.read()
            doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
            
            # Extract metadata
            metadata = doc.metadata or {}
            title = metadata.get('title', '') or stream_info.filename or "PDF Document"
            author = metadata.get('author', '')
            subject = metadata.get('subject', '')
            
            # Extract text from all pages
            text_parts = []
            for page_num, page in enumerate(doc, 1):
                page_text = page.get_text()
                if page_text.strip():
                    text_parts.append(page_text)
            
            doc.close()
            
            # Combine all text
            full_text = "\n\n".join(text_parts)
            
            # Normalize Unicode (handle special characters, remove accents)
            normalized_text = unicodedata.normalize('NFKD', full_text)
            
            # Create markdown format
            markdown_content = f"# {title}\n\n"
            
            if author:
                markdown_content += f"**Author:** {author}\n\n"
            
            if subject:
                markdown_content += f"**Subject:** {subject}\n\n"
            
            markdown_content += normalized_text
            
            # Build metadata
            result_metadata = {
                "source": stream_info.url or stream_info.local_path or "PDF",
                "pages": len(doc),
                "format": "PDF"
            }
            
            if author:
                result_metadata["author"] = author
            if subject:
                result_metadata["subject"] = subject
            
            logger.info(f"Successfully extracted PDF: {title} ({len(doc)} pages)")
            
            return ConversionResult(
                title=title,
                content=markdown_content,
                text=normalized_text,
                metadata=result_metadata,
                success=True
            )
            
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            return ConversionResult(
                title=stream_info.filename or "PDF Document",
                content="",
                success=False,
                error=str(e)
            )
        finally:
            file_stream.seek(cur_pos)
