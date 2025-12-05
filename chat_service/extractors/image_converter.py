"""
Image Converter

Extracts text from images using OCR and generates descriptions using LLM.
Inspired by MarkItDown's image converter but adapted for NVIDIA NIM.
"""

import logging
import base64
import io
from typing import BinaryIO, Any, Optional
from PIL import Image

from .base_converter import BaseConverter, ConversionResult
from .stream_info import StreamInfo

logger = logging.getLogger(__name__)


ACCEPTED_MIME_TYPES = [
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/gif",
    "image/webp",
]

ACCEPTED_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".webp"]


class ImageConverter(BaseConverter):
    """
    Converts images to markdown via OCR and LLM description.
    
    Features:
    - OCR text extraction using pytesseract
    - Image description using NVIDIA NIM LLM
    - Image metadata extraction
    """
    
    def accepts(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any
    ) -> bool:
        """Check if this is an image file."""
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
        Extract content from image.
        
        Args:
            file_stream: Image file stream
            stream_info: File metadata
            **kwargs: Additional options:
                - llm_client: OpenAI-compatible client for descriptions
                - llm_model: Model name
                - llm_prompt: Custom prompt for description
                - use_ocr: Whether to use OCR (default: True)
            
        Returns:
            ConversionResult with extracted content
        """
        cur_pos = file_stream.tell()
        
        try:
            # Load image
            image = Image.open(file_stream)
            
            # Extract basic metadata
            width, height = image.size
            format_name = image.format or "Unknown"
            mode = image.mode
            
            title = stream_info.filename or "Image"
            
            markdown_content = f"# {title}\n\n"
            markdown_content += f"**Format:** {format_name}\n"
            markdown_content += f"**Size:** {width}x{height}\n"
            markdown_content += f"**Mode:** {mode}\n\n"
            
            # Try OCR if requested
            use_ocr = kwargs.get('use_ocr', True)
            ocr_text = ""
            
            if use_ocr:
                ocr_text = self._extract_text_ocr(image)
                if ocr_text:
                    markdown_content += f"## Extracted Text (OCR)\n\n{ocr_text}\n\n"
            
            # Try LLM description if client provided
            llm_client = kwargs.get('llm_client')
            llm_model = kwargs.get('llm_model')
            
            if llm_client and llm_model:
                file_stream.seek(cur_pos)
                description = self._get_llm_description(
                    file_stream,
                    stream_info,
                    client=llm_client,
                    model=llm_model,
                    prompt=kwargs.get('llm_prompt')
                )
                
                if description:
                    markdown_content += f"## AI Description\n\n{description}\n\n"
            
            # Build metadata
            result_metadata = {
                "source": stream_info.url or stream_info.local_path or "Image",
                "format": format_name,
                "width": width,
                "height": height,
                "mode": mode
            }
            
            if ocr_text:
                result_metadata["has_text"] = True
            
            logger.info(f"Successfully processed image: {title} ({width}x{height})")
            
            return ConversionResult(
                title=title,
                content=markdown_content,
                text=ocr_text or markdown_content,
                metadata=result_metadata,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Image extraction failed: {e}")
            return ConversionResult(
                title=stream_info.filename or "Image",
                content="",
                success=False,
                error=str(e)
            )
        finally:
            file_stream.seek(cur_pos)
    
    def _extract_text_ocr(self, image: Image.Image) -> str:
        """
        Extract text from image using OCR.
        
        Args:
            image: PIL Image object
            
        Returns:
            Extracted text or empty string
        """
        try:
            import pytesseract
            
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Extract text
            text = pytesseract.image_to_string(image)
            
            # Clean up text
            text = text.strip()
            
            if len(text) > 10:  # Only return if meaningful text found
                logger.info(f"OCR extracted {len(text)} characters")
                return text
            
            return ""
            
        except ImportError:
            logger.warning("pytesseract not installed. Install with: pip install pytesseract")
            return ""
        except Exception as e:
            logger.warning(f"OCR extraction failed: {e}")
            return ""
    
    def _get_llm_description(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        client,
        model: str,
        prompt: Optional[str] = None
    ) -> Optional[str]:
        """
        Get image description from LLM.
        
        Args:
            file_stream: Image file stream
            stream_info: File metadata
            client: OpenAI-compatible client (NVIDIA NIM)
            model: Model name
            prompt: Custom prompt (optional)
            
        Returns:
            Description text or None
        """
        try:
            if prompt is None or not prompt.strip():
                prompt = "Describe this image in detail. Focus on the main content, objects, text, and any important visual elements."
            
            # Get content type
            content_type = stream_info.mimetype
            if not content_type:
                # Guess from extension
                ext = (stream_info.extension or "").lower()
                type_map = {
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.png': 'image/png',
                    '.gif': 'image/gif',
                    '.webp': 'image/webp'
                }
                content_type = type_map.get(ext, 'image/jpeg')
            
            # Convert to base64
            cur_pos = file_stream.tell()
            try:
                image_bytes = file_stream.read()
                base64_image = base64.b64encode(image_bytes).decode('utf-8')
            finally:
                file_stream.seek(cur_pos)
            
            # Create data URI
            data_uri = f"data:{content_type};base64,{base64_image}"
            
            # Call LLM with vision capabilities
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": data_uri}
                        }
                    ]
                }
            ]
            
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            description = response.choices[0].message.content
            logger.info(f"Generated image description ({len(description)} chars)")
            
            return description
            
        except Exception as e:
            logger.warning(f"LLM description generation failed: {e}")
            return None
