"""
URL Extractor Base Class

Base class for all content extractors with common functionality:
- URL validation and security checks
- Content fetching with timeout
- URL type detection
- Error handling
"""

import logging
import requests
from urllib.parse import urlparse
from enum import Enum
from typing import Dict, Optional
import ipaddress

logger = logging.getLogger(__name__)


class URLType(Enum):
    """Supported URL content types"""
    DOCUMENTATION = "documentation"
    GITHUB = "github"
    VIDEO = "video"
    PDF = "pdf"
    GENERIC = "generic"
    UNKNOWN = "unknown"


class URLExtractor:
    """
    Base class for URL content extraction.
    
    Provides common functionality for all extractors:
    - URL validation and security
    - Content fetching
    - Type detection
    """
    
    def __init__(self, url: str):
        """
        Initialize extractor with URL.
        
        Args:
            url: URL to extract content from
            
        Raises:
            ValueError: If URL is invalid or insecure
        """
        self.url = url
        self.parsed_url = urlparse(url)
        self.content = None
        
        # Validate URL
        self.validate_url()
        
        logger.info(f"URLExtractor initialized for: {url}")
    
    def validate_url(self):
        """
        Validate URL for security and correctness.
        
        Checks:
        - Valid scheme (http/https only)
        - Not localhost or private IP
        - Has valid hostname
        
        Raises:
            ValueError: If URL fails validation
        """
        # Check scheme
        if self.parsed_url.scheme not in ['http', 'https']:
            raise ValueError(f"Invalid URL scheme: {self.parsed_url.scheme}. Only HTTP and HTTPS are supported.")
        
        # Check hostname exists
        if not self.parsed_url.hostname:
            raise ValueError("URL must have a valid hostname")
        
        # Block localhost
        if self.parsed_url.hostname in ['localhost', '127.0.0.1', '0.0.0.0', '::1']:
            raise ValueError("Localhost URLs are not allowed for security reasons")
        
        # Block private IP ranges
        try:
            ip = ipaddress.ip_address(self.parsed_url.hostname)
            if ip.is_private:
                raise ValueError(f"Private IP addresses are not allowed: {self.parsed_url.hostname}")
        except ValueError:
            # Not an IP address, which is fine
            pass
        
        logger.debug(f"URL validation passed: {self.url}")
    
    def fetch_content(self, timeout: int = 30) -> str:
        """
        Fetch content from URL with timeout.
        
        Args:
            timeout: Request timeout in seconds (default: 30)
            
        Returns:
            Raw content as string
            
        Raises:
            requests.RequestException: If fetch fails
        """
        try:
            logger.info(f"Fetching content from: {self.url}")
            
            headers = {
                'User-Agent': 'Via-Canvas-Bot/1.0 (Content Extraction for Mind Mapping)'
            }
            
            response = requests.get(
                self.url,
                timeout=timeout,
                headers=headers,
                allow_redirects=True
            )
            
            response.raise_for_status()
            
            self.content = response.text
            logger.info(f"Successfully fetched {len(self.content)} characters from {self.url}")
            
            return self.content
            
        except requests.Timeout:
            logger.error(f"Timeout fetching URL: {self.url}")
            raise
        except requests.RequestException as e:
            logger.error(f"Error fetching URL {self.url}: {e}")
            raise
    
    @staticmethod
    def detect_url_type(url: str) -> URLType:
        """
        Detect the type of content at URL.
        
        Args:
            url: URL to analyze
            
        Returns:
            URLType enum value
        """
        parsed = urlparse(url.lower())
        hostname = parsed.hostname or ''
        path = parsed.path or ''
        
        # GitHub
        if 'github.com' in hostname:
            return URLType.GITHUB
        
        # Video platforms
        if any(platform in hostname for platform in ['youtube.com', 'youtu.be', 'vimeo.com']):
            return URLType.VIDEO
        
        # PDF
        if path.endswith('.pdf'):
            return URLType.PDF
        
        # Documentation (common patterns)
        doc_patterns = [
            'docs.', 'documentation.', 'doc.', 
            '/docs/', '/documentation/', '/guide/',
            'readthedocs.io', 'gitbook.io'
        ]
        if any(pattern in url.lower() for pattern in doc_patterns):
            return URLType.DOCUMENTATION
        
        # Default to generic
        return URLType.GENERIC
    
    def extract(self) -> Dict:
        """
        Extract structured content from URL.
        
        This method should be overridden by subclasses.
        
        Returns:
            Dictionary with extracted content structure:
            {
                "card_type": str,  # "link", "video", "rich_text"
                "title": str,
                "description": str,
                "sections": list[dict],
                "metadata": dict
            }
            
        Raises:
            NotImplementedError: If not overridden by subclass
        """
        raise NotImplementedError("Subclasses must implement extract() method")
    
    def get_metadata(self) -> Dict:
        """
        Get basic metadata about the URL.
        
        Returns:
            Dictionary with URL metadata
        """
        return {
            "url": self.url,
            "hostname": self.parsed_url.hostname,
            "scheme": self.parsed_url.scheme,
            "type": self.detect_url_type(self.url).value
        }
