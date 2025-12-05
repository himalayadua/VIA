"""
Documentation Extractor

Extracts structured content from documentation websites.
Parses HTML to extract titles, headings, sections, and code blocks.
"""

import logging
from typing import Dict, List
from bs4 import BeautifulSoup
from .url_extractor import URLExtractor

logger = logging.getLogger(__name__)


class DocumentationExtractor(URLExtractor):
    """
    Extract content from documentation websites.
    
    Extracts:
    - Page title and description
    - Heading hierarchy (h1, h2, h3)
    - Content sections
    - Code blocks with language detection
    """
    
    def extract(self) -> Dict:
        """
        Extract structured content from documentation page.
        
        Returns:
            Dictionary with extracted documentation structure
        """
        # Fetch content if not already fetched
        if not self.content:
            self.fetch_content()
        
        logger.info(f"Extracting documentation from: {self.url}")
        
        # Parse HTML
        soup = BeautifulSoup(self.content, 'html.parser')
        
        # Extract title
        title = self._extract_title(soup)
        
        # Extract description
        description = self._extract_description(soup)
        
        # Extract sections
        sections = self._extract_sections(soup)
        
        # Extract code blocks
        code_blocks = self._extract_code_blocks(soup)
        
        result = {
            "card_type": "link",
            "title": title,
            "description": description,
            "sections": sections,
            "code_blocks": code_blocks,
            "metadata": self.get_metadata()
        }
        
        logger.info(f"Extracted {len(sections)} sections and {len(code_blocks)} code blocks")
        return result
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        # Try h1 first
        h1 = soup.find('h1')
        if h1:
            return h1.get_text().strip()
        
        # Fall back to title tag
        title = soup.find('title')
        if title:
            return title.get_text().strip()
        
        return "Untitled Document"
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract page description from meta tags or first paragraph"""
        # Try meta description
        meta = soup.find('meta', attrs={'name': 'description'})
        if meta and meta.get('content'):
            return meta['content']
        
        # Try og:description
        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc and og_desc.get('content'):
            return og_desc['content']
        
        # Fall back to first paragraph
        first_p = soup.find('p')
        if first_p:
            return first_p.get_text().strip()[:200]
        
        return ""
    
    def _extract_sections(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract content sections based on h2 headings"""
        sections = []
        
        # Find main content area
        main = soup.find('main') or soup.find('article') or soup.find('body')
        if not main:
            return sections
        
        # Extract h2 sections
        for h2 in main.find_all('h2'):
            section_title = h2.get_text().strip()
            
            # Get content until next h2
            content_parts = []
            for sibling in h2.find_next_siblings():
                if sibling.name == 'h2':
                    break
                if sibling.name in ['p', 'ul', 'ol']:
                    content_parts.append(sibling.get_text().strip())
            
            if content_parts:
                sections.append({
                    "title": section_title,
                    "content": "\n\n".join(content_parts),
                    "level": 2
                })
        
        return sections
    
    def _extract_code_blocks(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract code blocks with language detection"""
        code_blocks = []
        
        for pre in soup.find_all('pre'):
            code = pre.find('code')
            if code:
                code_text = code.get_text().strip()
                
                # Try to detect language from class
                language = "unknown"
                if code.get('class'):
                    classes = code.get('class')
                    for cls in classes:
                        if cls.startswith('language-'):
                            language = cls.replace('language-', '')
                            break
                
                code_blocks.append({
                    "code": code_text,
                    "language": language
                })
        
        return code_blocks
