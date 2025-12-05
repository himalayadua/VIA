"""
Extraction Orchestrator

Coordinates content extraction using multiple methods with caching and fallback logic.
Integrates with existing Via Canvas extraction system.
"""

import logging
import asyncio
from typing import Dict, Optional
from datetime import datetime

from .enhanced_extractor import EnhancedExtractor
from .cache import ExtractionCache
from .url_extractor import URLType, URLExtractor

logger = logging.getLogger(__name__)


class ExtractionOrchestrator:
    """
    Orchestrates content extraction with caching and fallback logic.
    
    Features:
    - Automatic caching of successful extractions
    - Fallback chain for robust extraction
    - Integration with existing extractors
    - Extraction metrics and logging
    """
    
    def __init__(self, use_cache: bool = True):
        """
        Initialize orchestrator.
        
        Args:
            use_cache: Whether to use caching (default: True)
        """
        self.use_cache = use_cache
        self.cache = ExtractionCache() if use_cache else None
        self.stats = {
            "total_extractions": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "method_usage": {}
        }
        
        logger.info("ExtractionOrchestrator initialized")
    
    async def extract_url(
        self,
        url: str,
        method: str = "auto",
        format: str = "markdown"
    ) -> Dict:
        """
        Extract content from URL with caching and fallback.
        
        Args:
            url: URL to extract content from
            method: Extraction method ('auto', 'enhanced', 'basic', 'github', 'video')
            format: Output format ('markdown', 'html', 'text')
            
        Returns:
            Dictionary with extracted content:
            {
                "title": str,
                "content": str,
                "metadata": dict,
                "success": bool,
                "extraction_method": str,
                "cached": bool
            }
        """
        self.stats["total_extractions"] += 1
        start_time = datetime.now()
        
        # Check cache first
        if self.use_cache and self.cache:
            cached_result = self.cache.get(url)
            if cached_result:
                self.stats["cache_hits"] += 1
                logger.info(f"Cache hit for: {url}")
                cached_result["cached"] = True
                return cached_result
        
        self.stats["cache_misses"] += 1
        
        # Determine extraction method
        if method == "auto":
            url_type = URLExtractor.detect_url_type(url)
            method = self._select_method_for_type(url_type)
        
        # Extract content
        try:
            result = await self._extract_with_method(url, method, format)
            
            # Cache successful extraction
            if result.get("success") and self.use_cache and self.cache:
                self.cache.set(url, result)
            
            # Update stats
            extraction_method = result.get("extraction_method", method)
            self.stats["method_usage"][extraction_method] = \
                self.stats["method_usage"].get(extraction_method, 0) + 1
            
            # Add timing
            result["extraction_time"] = (datetime.now() - start_time).total_seconds()
            result["cached"] = False
            
            logger.info(
                f"Extracted {url} using {extraction_method} "
                f"in {result['extraction_time']:.2f}s"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Extraction failed for {url}: {e}")
            return {
                "title": url,
                "content": "",
                "metadata": {"url": url, "error": str(e)},
                "success": False,
                "extraction_method": "none",
                "cached": False,
                "error": str(e)
            }
    
    async def _extract_with_method(
        self,
        url: str,
        method: str,
        format: str
    ) -> Dict:
        """
        Extract content using specified method.
        
        Args:
            url: URL to extract
            method: Extraction method
            format: Output format
            
        Returns:
            Extracted content dictionary
        """
        if method == "enhanced":
            return await self._extract_enhanced(url, format)
        elif method == "github":
            return await self._extract_github(url, format)
        elif method == "video":
            return await self._extract_video(url, format)
        elif method == "basic":
            return await self._extract_basic(url, format)
        else:
            # Default to enhanced
            return await self._extract_enhanced(url, format)
    
    async def _extract_enhanced(self, url: str, format: str) -> Dict:
        """Extract using enhanced extractor with fallback chain."""
        extractor = EnhancedExtractor(url, use_cache=False)
        result = await extractor.extract()
        
        # Format content based on requested format
        if format == "markdown":
            result["content"] = self._html_to_markdown(result.get("html", "")) or result.get("text", "")
        elif format == "text":
            result["content"] = result.get("text", "")
        elif format == "html":
            result["content"] = result.get("html", "")
        
        return result
    
    async def _extract_github(self, url: str, format: str) -> Dict:
        """Extract using GitHub extractor."""
        try:
            from .github_extractor import GitHubExtractor
            
            extractor = GitHubExtractor(url)
            result = extractor.extract()
            result["success"] = True
            result["extraction_method"] = "github"
            return result
            
        except Exception as e:
            logger.warning(f"GitHub extraction failed, falling back to enhanced: {e}")
            return await self._extract_enhanced(url, format)
    
    async def _extract_video(self, url: str, format: str) -> Dict:
        """Extract using video extractor."""
        try:
            from .video_extractor import VideoExtractor
            
            extractor = VideoExtractor(url)
            result = extractor.extract()
            result["success"] = True
            result["extraction_method"] = "video"
            return result
            
        except Exception as e:
            logger.warning(f"Video extraction failed, falling back to enhanced: {e}")
            return await self._extract_enhanced(url, format)
    
    async def _extract_basic(self, url: str, format: str) -> Dict:
        """Extract using basic BeautifulSoup method."""
        try:
            import requests
            from bs4 import BeautifulSoup
            
            headers = {'User-Agent': 'Via-Canvas-Bot/1.0'}
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title = soup.title.string if soup.title else url
            
            # Remove unwanted elements
            for element in soup(["script", "style", "nav", "footer"]):
                element.decompose()
            
            # Get text
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            text = '\n'.join(line for line in lines if line)
            
            return {
                "title": title,
                "content": text,
                "text": text,
                "html": str(soup),
                "metadata": {"url": url},
                "success": True,
                "extraction_method": "basic"
            }
            
        except Exception as e:
            logger.error(f"Basic extraction failed: {e}")
            return {
                "title": url,
                "content": "",
                "metadata": {"url": url, "error": str(e)},
                "success": False,
                "extraction_method": "basic",
                "error": str(e)
            }
    
    def _select_method_for_type(self, url_type: URLType) -> str:
        """Select best extraction method for URL type."""
        method_map = {
            URLType.GITHUB: "github",
            URLType.VIDEO: "video",
            URLType.DOCUMENTATION: "enhanced",
            URLType.GENERIC: "enhanced",
            URLType.PDF: "basic",
            URLType.UNKNOWN: "enhanced"
        }
        return method_map.get(url_type, "enhanced")
    
    def _html_to_markdown(self, html: str) -> str:
        """Convert HTML to Markdown (basic conversion)."""
        if not html:
            return ""
        
        try:
            from bs4 import BeautifulSoup
            import re
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Convert headings
            for i in range(1, 7):
                for heading in soup.find_all(f'h{i}'):
                    heading.string = f"{'#' * i} {heading.get_text()}\n\n"
            
            # Convert links
            for link in soup.find_all('a'):
                text = link.get_text()
                href = link.get('href', '')
                link.string = f"[{text}]({href})"
            
            # Convert bold
            for bold in soup.find_all(['b', 'strong']):
                bold.string = f"**{bold.get_text()}**"
            
            # Convert italic
            for italic in soup.find_all(['i', 'em']):
                italic.string = f"*{italic.get_text()}*"
            
            # Convert lists
            for ul in soup.find_all('ul'):
                for li in ul.find_all('li'):
                    li.string = f"- {li.get_text()}\n"
            
            for ol in soup.find_all('ol'):
                for idx, li in enumerate(ol.find_all('li'), 1):
                    li.string = f"{idx}. {li.get_text()}\n"
            
            # Get text
            text = soup.get_text()
            
            # Clean up extra whitespace
            text = re.sub(r'\n{3,}', '\n\n', text)
            
            return text.strip()
            
        except Exception as e:
            logger.warning(f"HTML to Markdown conversion failed: {e}")
            return html
    
    def get_stats(self) -> Dict:
        """
        Get extraction statistics.
        
        Returns:
            Dictionary with extraction stats
        """
        cache_hit_rate = 0
        if self.stats["total_extractions"] > 0:
            cache_hit_rate = (
                self.stats["cache_hits"] / self.stats["total_extractions"]
            ) * 100
        
        return {
            "total_extractions": self.stats["total_extractions"],
            "cache_hits": self.stats["cache_hits"],
            "cache_misses": self.stats["cache_misses"],
            "cache_hit_rate": f"{cache_hit_rate:.1f}%",
            "method_usage": self.stats["method_usage"]
        }
    
    def clear_cache(self):
        """Clear extraction cache."""
        if self.cache:
            self.cache.clear()
            logger.info("Extraction cache cleared")
