"""
Converter Registry

Manages content converters with priority-based selection and fallback logic.
Inspired by MarkItDown's converter registration system.
"""

import logging
import io
from typing import List, Tuple, BinaryIO, Any, Optional
from dataclasses import dataclass

from .base_converter import BaseConverter, ConversionResult
from .stream_info import StreamInfo

logger = logging.getLogger(__name__)


# Priority constants (lower = higher priority, tried first)
PRIORITY_SPECIFIC = 0.0  # Specific file formats (PDF, images, etc.)
PRIORITY_GENERIC = 10.0  # Generic formats (HTML, text, etc.)


@dataclass
class ConverterRegistration:
    """Registration of a converter with its priority."""
    converter: BaseConverter
    priority: float


class ConverterRegistry:
    """
    Registry for content converters with priority-based selection.
    
    Features:
    - Priority-based converter selection
    - Automatic fallback to next converter on failure
    - Stable sort maintains registration order for same priority
    - Tracks failed attempts for debugging
    """
    
    def __init__(self):
        """Initialize empty registry."""
        self._converters: List[ConverterRegistration] = []
        self._stats = {
            "total_conversions": 0,
            "successful_conversions": 0,
            "failed_conversions": 0,
            "converter_usage": {}
        }
        
        logger.info("ConverterRegistry initialized")
    
    def register(
        self,
        converter: BaseConverter,
        priority: float = PRIORITY_SPECIFIC
    ) -> None:
        """
        Register a converter with given priority.
        
        Lower priority values are tried first (higher priority).
        Converters with same priority maintain registration order.
        
        Args:
            converter: Converter instance to register
            priority: Priority value (default: PRIORITY_SPECIFIC = 0.0)
        """
        registration = ConverterRegistration(
            converter=converter,
            priority=priority
        )
        
        # Insert at beginning (will be sorted later)
        self._converters.insert(0, registration)
        
        logger.info(
            f"Registered {converter.get_name()} "
            f"with priority {priority}"
        )
    
    def convert(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any
    ) -> ConversionResult:
        """
        Convert content using registered converters.
        
        Tries converters in priority order until one succeeds.
        Tracks failed attempts for debugging.
        
        Args:
            file_stream: Binary stream of content
            stream_info: Metadata about content
            **kwargs: Additional options passed to converters
            
        Returns:
            ConversionResult from successful converter
            
        Raises:
            ValueError: If no converter can handle the content
        """
        self._stats["total_conversions"] += 1
        
        # Sort converters by priority (stable sort)
        sorted_converters = sorted(
            self._converters,
            key=lambda x: x.priority
        )
        
        # Track failed attempts
        failed_attempts = []
        
        # Remember stream position
        cur_pos = file_stream.tell()
        
        # Try each converter
        for registration in sorted_converters:
            converter = registration.converter
            converter_name = converter.get_name()
            
            try:
                # Check if converter accepts this content
                file_stream.seek(cur_pos)
                
                if not converter.accepts(file_stream, stream_info, **kwargs):
                    logger.debug(f"{converter_name} declined content")
                    continue
                
                # Try conversion
                logger.info(f"Attempting conversion with {converter_name}")
                file_stream.seek(cur_pos)
                
                result = converter.convert(file_stream, stream_info, **kwargs)
                
                if result.success:
                    # Success!
                    self._stats["successful_conversions"] += 1
                    self._stats["converter_usage"][converter_name] = \
                        self._stats["converter_usage"].get(converter_name, 0) + 1
                    
                    logger.info(
                        f"Successfully converted using {converter_name}"
                    )
                    
                    return result
                else:
                    # Converter accepted but failed
                    failed_attempts.append((converter_name, result.error))
                    logger.warning(
                        f"{converter_name} failed: {result.error}"
                    )
                    
            except Exception as e:
                # Converter threw exception
                failed_attempts.append((converter_name, str(e)))
                logger.warning(f"{converter_name} threw exception: {e}")
                continue
            finally:
                # Always reset stream position
                file_stream.seek(cur_pos)
        
        # All converters failed
        self._stats["failed_conversions"] += 1
        
        error_msg = "No converter could handle this content"
        if failed_attempts:
            attempts_str = "; ".join(
                f"{name}: {error}" for name, error in failed_attempts
            )
            error_msg += f". Failed attempts: {attempts_str}"
        
        logger.error(error_msg)
        
        return ConversionResult(
            title=stream_info.filename or stream_info.url or "Unknown",
            content="",
            success=False,
            error=error_msg
        )
    
    def get_converters(self) -> List[BaseConverter]:
        """Get list of registered converters (in priority order)."""
        sorted_converters = sorted(
            self._converters,
            key=lambda x: x.priority
        )
        return [reg.converter for reg in sorted_converters]
    
    def get_stats(self) -> dict:
        """Get conversion statistics."""
        success_rate = 0
        if self._stats["total_conversions"] > 0:
            success_rate = (
                self._stats["successful_conversions"] /
                self._stats["total_conversions"]
            ) * 100
        
        return {
            "total_conversions": self._stats["total_conversions"],
            "successful_conversions": self._stats["successful_conversions"],
            "failed_conversions": self._stats["failed_conversions"],
            "success_rate": f"{success_rate:.1f}%",
            "converter_usage": self._stats["converter_usage"],
            "registered_converters": len(self._converters)
        }
    
    def clear_stats(self):
        """Clear conversion statistics."""
        self._stats = {
            "total_conversions": 0,
            "successful_conversions": 0,
            "failed_conversions": 0,
            "converter_usage": {}
        }
        logger.info("Converter statistics cleared")
