"""
File Type Detector

Detects file types based on content (magic bytes) and metadata.
Simplified version inspired by MarkItDown's Magika integration.
"""

import logging
import mimetypes
from typing import BinaryIO, Optional, List
from .stream_info import StreamInfo

logger = logging.getLogger(__name__)


# Magic byte signatures for common file types
MAGIC_SIGNATURES = {
    # PDF
    b'%PDF': ('application/pdf', '.pdf'),
    
    # Images
    b'\xFF\xD8\xFF': ('image/jpeg', '.jpg'),
    b'\x89PNG\r\n\x1a\n': ('image/png', '.png'),
    b'GIF87a': ('image/gif', '.gif'),
    b'GIF89a': ('image/gif', '.gif'),
    b'RIFF': ('image/webp', '.webp'),  # Needs further check
    
    # Office documents
    b'PK\x03\x04': ('application/zip', '.zip'),  # Also DOCX, XLSX, etc.
    b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1': ('application/msword', '.doc'),
    
    # Archives
    b'\x1F\x8B': ('application/gzip', '.gz'),
    b'BZh': ('application/x-bzip2', '.bz2'),
    b'7z\xBC\xAF\x27\x1C': ('application/x-7z-compressed', '.7z'),
}


class FileDetector:
    """
    Detects file types from content and metadata.
    
    Uses multiple detection methods:
    1. Magic bytes (content-based)
    2. File extension
    3. MIME type from metadata
    """
    
    @staticmethod
    def detect(
        file_stream: BinaryIO,
        base_info: Optional[StreamInfo] = None
    ) -> List[StreamInfo]:
        """
        Detect file type and generate StreamInfo guesses.
        
        Returns multiple guesses in priority order:
        1. Content-based detection (magic bytes)
        2. Extension-based detection
        3. MIME type from metadata
        
        Args:
            file_stream: Binary stream to analyze
            base_info: Base StreamInfo with known metadata
            
        Returns:
            List of StreamInfo guesses (most confident first)
        """
        if base_info is None:
            base_info = StreamInfo()
        
        guesses = []
        
        # Remember position
        cur_pos = file_stream.tell()
        
        try:
            # Read first 16 bytes for magic byte detection
            magic_bytes = file_stream.read(16)
            file_stream.seek(cur_pos)
            
            # Try magic byte detection
            detected_mimetype, detected_ext = FileDetector._detect_from_magic(
                magic_bytes
            )
            
            if detected_mimetype:
                # Content-based detection (highest confidence)
                guess = base_info.copy_and_update(
                    mimetype=detected_mimetype,
                    extension=detected_ext
                )
                guesses.append(guess)
                logger.debug(
                    f"Magic bytes detected: {detected_mimetype} ({detected_ext})"
                )
            
            # Try extension-based detection
            if base_info.extension:
                ext_mimetype = FileDetector._mimetype_from_extension(
                    base_info.extension
                )
                if ext_mimetype and ext_mimetype != detected_mimetype:
                    guess = base_info.copy_and_update(
                        mimetype=ext_mimetype
                    )
                    guesses.append(guess)
                    logger.debug(
                        f"Extension detected: {ext_mimetype} ({base_info.extension})"
                    )
            
            # Try MIME type to extension
            if base_info.mimetype and not base_info.extension:
                ext = FileDetector._extension_from_mimetype(
                    base_info.mimetype
                )
                if ext:
                    guess = base_info.copy_and_update(extension=ext)
                    guesses.append(guess)
                    logger.debug(
                        f"MIME type to extension: {base_info.mimetype} -> {ext}"
                    )
            
            # If no guesses, return base info
            if not guesses:
                guesses.append(base_info)
            
            return guesses
            
        except Exception as e:
            logger.warning(f"File detection failed: {e}")
            return [base_info]
        finally:
            file_stream.seek(cur_pos)
    
    @staticmethod
    def _detect_from_magic(magic_bytes: bytes) -> tuple:
        """
        Detect file type from magic bytes.
        
        Args:
            magic_bytes: First bytes of file
            
        Returns:
            Tuple of (mimetype, extension) or (None, None)
        """
        for signature, (mimetype, ext) in MAGIC_SIGNATURES.items():
            if magic_bytes.startswith(signature):
                # Special handling for WEBP (needs WEBP in header)
                if signature == b'RIFF':
                    if b'WEBP' in magic_bytes[:16]:
                        return mimetype, ext
                    else:
                        continue
                
                return mimetype, ext
        
        return None, None
    
    @staticmethod
    def _mimetype_from_extension(extension: str) -> Optional[str]:
        """Get MIME type from file extension."""
        if not extension:
            return None
        
        # Ensure extension starts with dot
        if not extension.startswith('.'):
            extension = '.' + extension
        
        mimetype, _ = mimetypes.guess_type(f"file{extension}")
        return mimetype
    
    @staticmethod
    def _extension_from_mimetype(mimetype: str) -> Optional[str]:
        """Get file extension from MIME type."""
        if not mimetype:
            return None
        
        extensions = mimetypes.guess_all_extensions(mimetype)
        if extensions:
            # Return most common extension
            return extensions[0]
        
        return None
    
    @staticmethod
    def is_text_file(stream_info: StreamInfo) -> bool:
        """Check if file is likely text-based."""
        if not stream_info.mimetype:
            return False
        
        text_types = [
            'text/',
            'application/json',
            'application/xml',
            'application/javascript',
        ]
        
        mimetype = stream_info.mimetype.lower()
        return any(mimetype.startswith(t) for t in text_types)
