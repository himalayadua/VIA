"""
StreamInfo - Unified metadata container for content extraction.

Inspired by MarkItDown's StreamInfo pattern for handling file/stream metadata.
"""

from dataclasses import dataclass, replace
from typing import Optional


@dataclass(frozen=True)
class StreamInfo:
    """
    Immutable container for stream/file metadata.
    
    Used to pass information about content being extracted:
    - File type information (mimetype, extension)
    - Source information (url, local_path, filename)
    - Content encoding (charset)
    
    Immutable design allows safe sharing across extractors.
    Use copy_and_update() to create modified copies.
    """
    
    mimetype: Optional[str] = None
    charset: Optional[str] = None
    extension: Optional[str] = None
    filename: Optional[str] = None
    local_path: Optional[str] = None
    url: Optional[str] = None
    
    def copy_and_update(
        self,
        mimetype: Optional[str] = None,
        charset: Optional[str] = None,
        extension: Optional[str] = None,
        filename: Optional[str] = None,
        local_path: Optional[str] = None,
        url: Optional[str] = None
    ) -> 'StreamInfo':
        """
        Create a copy with updated fields.
        
        Only updates fields that are explicitly provided (not None).
        This allows partial updates while preserving other fields.
        
        Args:
            mimetype: MIME type (e.g., 'application/pdf')
            charset: Character encoding (e.g., 'utf-8')
            extension: File extension (e.g., '.pdf')
            filename: Original filename
            local_path: Local file path
            url: Source URL
            
        Returns:
            New StreamInfo instance with updated fields
        """
        updates = {}
        
        if mimetype is not None:
            updates['mimetype'] = mimetype
        if charset is not None:
            updates['charset'] = charset
        if extension is not None:
            updates['extension'] = extension
        if filename is not None:
            updates['filename'] = filename
        if local_path is not None:
            updates['local_path'] = local_path
        if url is not None:
            updates['url'] = url
        
        return replace(self, **updates)
    
    def __str__(self) -> str:
        """String representation for debugging."""
        parts = []
        if self.mimetype:
            parts.append(f"mimetype={self.mimetype}")
        if self.extension:
            parts.append(f"ext={self.extension}")
        if self.filename:
            parts.append(f"file={self.filename}")
        if self.url:
            parts.append(f"url={self.url[:50]}...")
        
        return f"StreamInfo({', '.join(parts)})"
