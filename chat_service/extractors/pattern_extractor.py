"""
Pattern Extractor

Extracts code patterns and examples from content.
Detects sections marked as "Example:", "Pattern:", "Usage:", etc.
"""

import logging
import re
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class PatternExtractor:
    """
    Extracts patterns and examples from content.
    
    Detects sections marked as:
    - Example:
    - Pattern:
    - Usage:
    - Sample:
    - Demo:
    - Try this:
    """
    
    # Pattern markers to detect
    PATTERN_MARKERS = [
        r"Example:\s*(.+?)(?:\n|$)",
        r"Pattern:\s*(.+?)(?:\n|$)",
        r"Usage:\s*(.+?)(?:\n|$)",
        r"Sample Code:\s*(.+?)(?:\n|$)",
        r"Sample:\s*(.+?)(?:\n|$)",
        r"Demo:\s*(.+?)(?:\n|$)",
        r"Try this:\s*(.+?)(?:\n|$)",
        r"Here's an example:\s*(.+?)(?:\n|$)",
    ]
    
    def __init__(self, content: str):
        """
        Initialize pattern extractor.
        
        Args:
            content: Text content to extract patterns from
        """
        self.content = content
        self.patterns = []
    
    def extract_patterns(self) -> List[Dict]:
        """
        Extract all pattern sections from content.
        
        Returns:
            List of pattern dictionaries:
            [
                {
                    "type": "example" | "pattern" | "usage",
                    "title": str,
                    "description": str,
                    "code": str,
                    "language": str,
                    "line_number": int
                }
            ]
        """
        logger.info("Extracting patterns from content")
        
        # Find all pattern markers
        for marker_pattern in self.PATTERN_MARKERS:
            matches = re.finditer(marker_pattern, self.content, re.IGNORECASE | re.MULTILINE)
            
            for match in matches:
                try:
                    pattern = self._extract_pattern_content(match)
                    if pattern and pattern.get("code"):  # Only add if code was found
                        self.patterns.append(pattern)
                        logger.debug(f"Extracted pattern: {pattern['title']}")
                except Exception as e:
                    logger.error(f"Error extracting pattern at line {match.start()}: {e}")
        
        logger.info(f"Extracted {len(self.patterns)} patterns")
        return self.patterns
    
    def _extract_pattern_content(self, match: re.Match) -> Optional[Dict]:
        """
        Extract content following a pattern marker.
        
        Args:
            match: Regex match object for the pattern marker
            
        Returns:
            Pattern dictionary or None if extraction failed
        """
        # Get title from marker
        title = match.group(1).strip() if match.lastindex >= 1 else "Untitled"
        
        # Find code block following marker
        start_pos = match.end()
        code_block = self._find_next_code_block(start_pos)
        
        if not code_block or not code_block.get("code"):
            return None
        
        # Extract description (text between marker and code)
        description = self._extract_description(start_pos, code_block['start'])
        
        # Determine pattern type
        pattern_type = self._determine_type(match.group(0))
        
        return {
            "type": pattern_type,
            "title": title,
            "description": description,
            "code": code_block['code'],
            "language": code_block['language'],
            "line_number": self._get_line_number(match.start())
        }
    
    def _find_next_code_block(self, start_pos: int) -> Optional[Dict]:
        """
        Find the next code block after a position.
        
        Args:
            start_pos: Position to start searching from
            
        Returns:
            Dictionary with code, language, start, end or None
        """
        # Look for markdown code blocks: ```language\ncode\n```
        code_pattern = r"```(\w+)?\n(.*?)```"
        remaining_content = self.content[start_pos:]
        
        match = re.search(code_pattern, remaining_content, re.DOTALL)
        
        if match:
            language = match.group(1) or "unknown"
            code = match.group(2).strip()
            
            return {
                "code": code,
                "language": language,
                "start": start_pos + match.start(),
                "end": start_pos + match.end()
            }
        
        # Try to find indented code blocks (4 spaces or tab)
        indented_pattern = r"\n((?:    |\t).+(?:\n(?:    |\t).+)*)"
        match = re.search(indented_pattern, remaining_content)
        
        if match:
            code = match.group(1).strip()
            # Remove indentation
            code = re.sub(r"^(?:    |\t)", "", code, flags=re.MULTILINE)
            
            return {
                "code": code,
                "language": "unknown",
                "start": start_pos + match.start(),
                "end": start_pos + match.end()
            }
        
        return None
    
    def _extract_description(self, start: int, end: int) -> str:
        """
        Extract description text between marker and code.
        
        Args:
            start: Start position
            end: End position
            
        Returns:
            Description text
        """
        if end == -1 or end <= start:
            return ""
        
        text = self.content[start:end].strip()
        
        # Remove code block markers if any
        text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
        
        # Clean up extra whitespace
        text = re.sub(r"\n\s*\n", "\n", text)
        
        return text.strip()
    
    def _determine_type(self, marker: str) -> str:
        """
        Determine pattern type from marker text.
        
        Args:
            marker: The marker text (e.g., "Example:", "Pattern:")
            
        Returns:
            Pattern type: "example", "pattern", or "usage"
        """
        marker_lower = marker.lower()
        
        if any(word in marker_lower for word in ["example", "demo", "try this", "here's"]):
            return "example"
        elif "pattern" in marker_lower:
            return "pattern"
        elif any(word in marker_lower for word in ["usage", "sample"]):
            return "usage"
        
        return "example"  # Default to example
    
    def _get_line_number(self, position: int) -> int:
        """
        Get line number for a position in content.
        
        Args:
            position: Character position
            
        Returns:
            Line number (1-indexed)
        """
        return self.content[:position].count('\n') + 1
    
    def parse_pattern_relationships(self, patterns: List[Dict]) -> Dict:
        """
        Analyze relationships between patterns and group them.
        
        Args:
            patterns: List of extracted patterns
            
        Returns:
            Dictionary with groups and relationships:
            {
                "groups": {
                    "examples": [...],
                    "patterns": [...],
                    "usage": [...]
                },
                "relationships": [
                    {"pattern": str, "concept": str, "type": "demonstrates"}
                ]
            }
        """
        logger.info(f"Parsing relationships for {len(patterns)} patterns")
        
        # Group by type
        groups = {
            "examples": [],
            "patterns": [],
            "usage": []
        }
        
        for pattern in patterns:
            pattern_type = pattern.get("type", "example")
            if pattern_type in groups:
                groups[pattern_type].append(pattern)
        
        # Detect relationships
        relationships = self._detect_relationships(patterns)
        
        logger.info(f"Found {len(relationships)} relationships")
        
        return {
            "groups": groups,
            "relationships": relationships
        }
    
    def _detect_relationships(self, patterns: List[Dict]) -> List[Dict]:
        """
        Detect which concepts each pattern demonstrates.
        
        Args:
            patterns: List of patterns
            
        Returns:
            List of relationship dictionaries
        """
        relationships = []
        
        for pattern in patterns:
            # Combine title and description for analysis
            text = f"{pattern.get('title', '')} {pattern.get('description', '')}"
            
            # Extract potential concept names
            concepts = self._extract_concepts(text)
            
            for concept in concepts:
                relationships.append({
                    "pattern": pattern.get("title", "Untitled"),
                    "concept": concept,
                    "type": "demonstrates"
                })
        
        return relationships
    
    def _extract_concepts(self, text: str) -> List[str]:
        """
        Extract concept names from text.
        
        Looks for:
        - Capitalized words (likely concepts)
        - Technical terms (camelCase, PascalCase)
        - Common programming concepts
        
        Args:
            text: Text to extract concepts from
            
        Returns:
            List of concept names
        """
        concepts = []
        
        # Capitalized words (likely concepts)
        # Match sequences like "React Hooks", "Factory Pattern"
        capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        concepts.extend(capitalized)
        
        # Technical terms (camelCase, PascalCase)
        technical = re.findall(r'\b[a-z]+[A-Z][a-zA-Z]*\b', text)
        concepts.extend(technical)
        
        # PascalCase
        pascal = re.findall(r'\b[A-Z][a-z]+[A-Z][a-zA-Z]*\b', text)
        concepts.extend(pascal)
        
        # Remove duplicates and filter out common words
        concepts = list(set(concepts))
        
        # Filter out very short or common words
        common_words = {'The', 'This', 'That', 'With', 'From', 'Into', 'Here', 'There'}
        concepts = [c for c in concepts if len(c) > 2 and c not in common_words]
        
        return concepts
    
    def get_summary(self) -> Dict:
        """
        Get summary statistics of extracted patterns.
        
        Returns:
            Dictionary with counts and statistics
        """
        grouped = self.parse_pattern_relationships(self.patterns)
        
        return {
            "total_patterns": len(self.patterns),
            "examples_count": len(grouped["groups"]["examples"]),
            "patterns_count": len(grouped["groups"]["patterns"]),
            "usage_count": len(grouped["groups"]["usage"]),
            "relationships_count": len(grouped["relationships"]),
            "languages": list(set(p.get("language", "unknown") for p in self.patterns))
        }
