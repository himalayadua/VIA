"""
Enhanced Content Extractor with Hybrid Fallback Chain

Uses multiple free extraction methods in priority order:
1. Trafilatura (fast, works 80% of time)
2. Readability + Playwright (for JS-heavy sites)
3. Newspaper3k (for articles/news)
4. BeautifulSoup (fallback)

All methods are free and open-source with no API keys required.
"""

import logging
import asyncio
from typing import Dict, Optional, List
from urllib.parse import urlparse
from datetime import datetime

logger = logging.getLogger(__name__)


class EnhancedExtractor:
    """
    Enhanced content extractor using multiple free tools.
    
    Implements a fallback chain for robust content extraction:
    - Trafilatura: Fast, works for most sites
    - Readability + Playwright: For JavaScript-heavy sites
    - Newspaper3k: Specialized for articles
    - BeautifulSoup: Basic fallback
    """
    
    def __init__(self, url: str, use_cache: bool = True):
        """
        Initialize enhanced extractor.
        
        Args:
            url: URL to extract content from
            use_cache: Whether to use caching (default: True)
        """
        self.url = url
        self.use_cache = use_cache
        self.parsed_url = urlparse(url)
        self.extraction_method = None
        self.extraction_time = None
        
        logger.info(f"EnhancedExtractor initialized for: {url}")
    
    async def extract(self) -> Dict:
        """
        Extract content using fallback chain.
        
        Returns:
            Dictionary with extracted content:
            {
                "title": str,
                "content": str,
                "text": str,  # Plain text version
                "html": str,  # Clean HTML
                "author": str,
                "date": str,
                "images": list[str],
                "metadata": dict,
                "extraction_method": str,
                "success": bool
            }
        """
        start_time = datetime.now()
        
        # Try extraction methods in order
        methods = [
            ("trafilatura", self._extract_trafilatura),
            ("readability", self._extract_readability),
            ("newspaper", self._extract_newspaper),
            ("beautifulsoup", self._extract_beautifulsoup)
        ]
        
        for method_name, method_func in methods:
            try:
                logger.info(f"Trying extraction method: {method_name}")
                result = await method_func()
                
                if result and result.get("success"):
                    self.extraction_method = method_name
                    self.extraction_time = (datetime.now() - start_time).total_seconds()
                    
                    result["extraction_method"] = method_name
                    result["extraction_time"] = self.extraction_time
                    
                    logger.info(f"Successfully extracted using {method_name} in {self.extraction_time:.2f}s")
                    return result
                    
            except Exception as e:
                logger.warning(f"Method {method_name} failed: {e}")
                continue
        
        # All methods failed
        logger.error(f"All extraction methods failed for: {self.url}")
        return {
            "title": self.url,
            "content": "",
            "text": "",
            "html": "",
            "author": "",
            "date": "",
            "images": [],
            "metadata": {"url": self.url},
            "extraction_method": "none",
            "success": False,
            "error": "All extraction methods failed"
        }
    
    async def _extract_trafilatura(self) -> Optional[Dict]:
        """
        Extract using Trafilatura (fast, works for most sites).
        
        Returns:
            Extracted content dict or None if failed
        """
        try:
            import trafilatura
            
            # Fetch content
            downloaded = trafilatura.fetch_url(self.url)
            if not downloaded:
                return None
            
            # Extract text
            text = trafilatura.extract(
                downloaded,
                include_comments=False,
                include_tables=True,
                include_images=False
            )
            
            if not text or len(text) < 100:
                return None
            
            # Extract metadata
            metadata = trafilatura.extract_metadata(downloaded)
            
            # Extract with formatting
            html = trafilatura.extract(
                downloaded,
                output_format='html',
                include_comments=False,
                include_tables=True
            )
            
            return {
                "title": metadata.title if metadata and metadata.title else self._extract_title_from_html(downloaded),
                "content": html or text,
                "text": text,
                "html": html or "",
                "author": metadata.author if metadata and metadata.author else "",
                "date": metadata.date if metadata and metadata.date else "",
                "images": [],
                "metadata": {
                    "url": self.url,
                    "sitename": metadata.sitename if metadata and metadata.sitename else "",
                    "description": metadata.description if metadata and metadata.description else ""
                },
                "success": True
            }
            
        except ImportError:
            logger.warning("Trafilatura not installed. Install with: pip install trafilatura")
            return None
        except Exception as e:
            logger.debug(f"Trafilatura extraction failed: {e}")
            return None
    
    async def _extract_readability(self) -> Optional[Dict]:
        """
        Extract using Readability + Playwright (for JS sites).
        
        Returns:
            Extracted content dict or None if failed
        """
        try:
            from playwright.async_api import async_playwright
            from readability import Document
            
            async with async_playwright() as p:
                # Launch browser
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # Navigate and wait for content
                await page.goto(self.url, wait_until='networkidle', timeout=30000)
                
                # Get rendered HTML
                html = await page.content()
                
                # Extract title
                title = await page.title()
                
                await browser.close()
            
            # Use Readability to extract main content
            doc = Document(html)
            
            return {
                "title": doc.title() or title,
                "content": doc.summary(),
                "text": self._html_to_text(doc.summary()),
                "html": doc.summary(),
                "author": "",
                "date": "",
                "images": [],
                "metadata": {
                    "url": self.url,
                    "short_title": doc.short_title()
                },
                "success": True
            }
            
        except ImportError:
            logger.warning("Playwright or Readability not installed. Install with: pip install playwright readability-lxml")
            return None
        except Exception as e:
            logger.debug(f"Readability extraction failed: {e}")
            return None
    
    async def _extract_newspaper(self) -> Optional[Dict]:
        """
        Extract using Newspaper3k (specialized for articles).
        
        Returns:
            Extracted content dict or None if failed
        """
        try:
            from newspaper import Article
            
            # Create and download article
            article = Article(self.url)
            article.download()
            article.parse()
            
            # Check if we got meaningful content
            if not article.text or len(article.text) < 100:
                return None
            
            return {
                "title": article.title or "",
                "content": article.text,
                "text": article.text,
                "html": article.html or "",
                "author": ", ".join(article.authors) if article.authors else "",
                "date": article.publish_date.isoformat() if article.publish_date else "",
                "images": [article.top_image] if article.top_image else [],
                "metadata": {
                    "url": self.url,
                    "keywords": article.keywords[:10] if article.keywords else [],
                    "summary": article.summary[:500] if article.summary else ""
                },
                "success": True
            }
            
        except ImportError:
            logger.warning("Newspaper3k not installed. Install with: pip install newspaper3k")
            return None
        except Exception as e:
            logger.debug(f"Newspaper extraction failed: {e}")
            return None
    
    async def _extract_beautifulsoup(self) -> Optional[Dict]:
        """
        Extract using BeautifulSoup (basic fallback).
        
        Returns:
            Extracted content dict or None if failed
        """
        try:
            import requests
            from bs4 import BeautifulSoup
            
            # Fetch content
            headers = {
                'User-Agent': 'Via-Canvas-Bot/1.0 (Content Extraction)'
            }
            response = requests.get(self.url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title = ""
            if soup.title:
                title = soup.title.string
            elif soup.find('h1'):
                title = soup.find('h1').get_text()
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Get text
            text = soup.get_text()
            
            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            if not text or len(text) < 100:
                return None
            
            # Extract images
            images = [img.get('src') for img in soup.find_all('img') if img.get('src')][:5]
            
            return {
                "title": title or self.url,
                "content": text,
                "text": text,
                "html": str(soup),
                "author": "",
                "date": "",
                "images": images,
                "metadata": {
                    "url": self.url
                },
                "success": True
            }
            
        except Exception as e:
            logger.debug(f"BeautifulSoup extraction failed: {e}")
            return None
    
    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text."""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            return soup.get_text()
        except:
            return html
    
    def _extract_title_from_html(self, html: str) -> str:
        """Extract title from HTML."""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            if soup.title:
                return soup.title.string
            elif soup.find('h1'):
                return soup.find('h1').get_text()
            return self.url
        except:
            return self.url
    
    def get_stats(self) -> Dict:
        """
        Get extraction statistics.
        
        Returns:
            Dictionary with extraction stats
        """
        return {
            "url": self.url,
            "method": self.extraction_method,
            "time": self.extraction_time,
            "hostname": self.parsed_url.hostname
        }
