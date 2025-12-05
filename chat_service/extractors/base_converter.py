"""
Base Converter Interface

Defines the interface for all content converters.
Inspired by MarkItDown's DocumentConverter pattern.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import BinaryIO, Any, Optional
from .stream_info import StreamInfo


@dataclass
class ConversionResult:
    """
    Result of a content conversion operation.
    
    Attributes:
        title: Document title
        content: Main content (markdown by default)
        text: Plain text version
        html: HTML version (if available)
        metadata: Additional metadata dict
        success: Whether conversion succeeded
        error: Error message if failed
    """
    title: str
    content: str
    text: str = ""
    html: str = ""
    metadata: dict = None
    success: bool = True
    error: Optional[str] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.metadata is None:
            self.metadata = {}
        if not self.text and self.content:
            self.text = self.content


class BaseConverter(ABC):
    """
    Base class for all content converters.
    
    Converters transform content from various sources/formats
    into a standardized format (typically markdown).
    
    Each converter must implement:
    - accepts(): Check if converter can handle the content
    - convert(): Perform the actual conversion
    """
    
    @abstractmethod
    def accepts(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any
    ) -> bool:
        """
        Check if this converter can handle the given content.
        
        This method should be fast and not modify the stream position.
        It should check mimetype, extension, or other metadata to
        determine if the converter is appropriate.
        
        Args:
            file_stream: Binary stream of content
            stream_info: Metadata about the content
            **kwargs: Additional options
            
        Returns:
            True if converter can handle this content
        """
        pass
    
    @abstractmethod
    def convert(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any
    ) -> ConversionResult:
        """
        Convert content to standardized format.
        
        The stream position should be reset to its original position
        after conversion (or on error).
        
        Args:
            file_stream: Binary stream of content
            stream_info: Metadata about the content
            **kwargs: Additional options (e.g., llm_client, format)
            
        Returns:
            ConversionResult with extracted content
            
        Raises:
            Exception: If conversion fails
        """
        pass
    
    def get_name(self) -> str:
        """Get converter name for logging/debugging."""
        return self.__class__.__name__
