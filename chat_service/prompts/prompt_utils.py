"""
Prompt Utilities

Utilities for formatting, validating, and processing prompts.
Provides helper functions for prompt management and LLM response handling.
"""

import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class PromptFormatter:
    """
    Utilities for formatting and validating prompts.
    
    Provides methods for:
    - Prompt length validation
    - Content truncation
    - Context injection
    - JSON response parsing
    """
    
    # Configuration constants
    MAX_PROMPT_LENGTH = 4000  # Characters
    MAX_CONTENT_LENGTH = 2000  # Characters for content snippets
    MIN_TRUNCATE_RATIO = 0.7  # Minimum ratio when truncating at boundaries
    
    @staticmethod
    def format_prompt(template: str, **kwargs) -> str:
        """
        Format a prompt template with variable substitution.
        
        Args:
            template: Prompt template string with {variable} placeholders
            **kwargs: Variables to substitute in template
            
        Returns:
            Formatted prompt string
            
        Raises:
            ValueError: If required variables are missing
        """
        try:
            return template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing required variable in prompt template: {e}")
    
    @staticmethod
    def truncate_content(content: str, max_length: int = None) -> str:
        """
        Intelligently truncate content to fit within length limit.
        
        Tries to truncate at sentence or paragraph boundaries to maintain readability.
        
        Args:
            content: Content to truncate
            max_length: Maximum length (defaults to MAX_CONTENT_LENGTH)
            
        Returns:
            Truncated content with "..." suffix if truncated
        """
        if max_length is None:
            max_length = PromptFormatter.MAX_CONTENT_LENGTH
        
        if len(content) <= max_length:
            return content
        
        # Try to truncate at natural boundaries
        truncated = content[:max_length]
        
        # Look for good cut points (in order of preference)
        boundaries = [
            ('\n\n', 2),  # Paragraph break
            ('.\n', 2),   # Sentence with newline
            ('. ', 2),    # Sentence end
            ('\n', 1),    # Line break
            (' ', 1)      # Word boundary
        ]
        
        best_cut = max_length
        for boundary, offset in boundaries:
            pos = truncated.rfind(boundary)
            if pos > max_length * PromptFormatter.MIN_TRUNCATE_RATIO:
                best_cut = pos + offset
                break
        
        return content[:best_cut].rstrip() + "..."
    
    @staticmethod
    def validate_prompt_length(prompt: str) -> bool:
        """
        Check if prompt is within acceptable length limits.
        
        Args:
            prompt: Prompt to validate
            
        Returns:
            True if prompt length is acceptable
        """
        return len(prompt) <= PromptFormatter.MAX_PROMPT_LENGTH
    
    @staticmethod
    def inject_canvas_context(prompt: str, canvas_id: str, 
                              include_cards: bool = False) -> str:
        """
        Inject canvas context into prompt.
        
        Args:
            prompt: Base prompt
            canvas_id: Canvas ID for context
            include_cards: Whether to include existing cards summary
            
        Returns:
            Prompt with canvas context appended
        """
        context = f"\n\nCanvas Context:\n- Canvas ID: {canvas_id}\n"
        
        if include_cards:
            try:
                from tools.canvas_api import get_canvas_cards
                cards = get_canvas_cards(canvas_id)
                context += f"- Total cards on canvas: {len(cards)}\n"
                
                if cards:
                    recent_titles = [card.get('title', 'Untitled') for card in cards[:5]]
                    context += f"- Recent cards: {', '.join(recent_titles)}\n"
            except Exception as e:
                logger.warning(f"Could not fetch canvas cards for context: {e}")
                context += "- Cards: Unable to fetch\n"
        
        return prompt + context
    
    @staticmethod
    def extract_json_from_response(response: str) -> str:
        """
        Extract JSON from LLM response that may contain markdown code blocks.
        
        Handles various response formats:
        - ```json ... ```
        - ``` ... ```
        - Plain JSON
        - JSON with surrounding text
        
        Args:
            response: Raw LLM response
            
        Returns:
            Cleaned JSON string
        """
        response = str(response).strip()
        
        # Handle markdown code blocks
        if "```json" in response:
            # Extract from ```json ... ```
            parts = response.split("```json")
            if len(parts) > 1:
                json_part = parts[1].split("```")[0]
                return json_part.strip()
        
        elif "```" in response:
            # Extract from ``` ... ```
            parts = response.split("```")
            if len(parts) >= 3:  # Text, JSON, Text
                json_part = parts[1]
                return json_part.strip()
        
        # Try to find JSON object boundaries
        start = response.find('{')
        if start != -1:
            # Find matching closing brace
            brace_count = 0
            for i, char in enumerate(response[start:], start):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        return response[start:i+1]
        
        # Try to find JSON array boundaries
        start = response.find('[')
        if start != -1:
            bracket_count = 0
            for i, char in enumerate(response[start:], start):
                if char == '[':
                    bracket_count += 1
                elif char == ']':
                    bracket_count -= 1
                    if bracket_count == 0:
                        return response[start:i+1]
        
        # Return as-is if no clear JSON boundaries found
        return response.strip()
    
    @staticmethod
    def parse_json_response(response: str) -> Dict[str, Any]:
        """
        Parse JSON from LLM response with error handling.
        
        Args:
            response: Raw LLM response
            
        Returns:
            Parsed JSON as dictionary
            
        Raises:
            ValueError: If JSON cannot be parsed
        """
        try:
            json_str = PromptFormatter.extract_json_from_response(response)
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response was: {response[:200]}...")
            raise ValueError(f"Invalid JSON in LLM response: {e}")
    
    @staticmethod
    def validate_json_structure(data: Dict[str, Any], required_keys: list) -> bool:
        """
        Validate that parsed JSON contains required keys.
        
        Args:
            data: Parsed JSON data
            required_keys: List of required key names
            
        Returns:
            True if all required keys are present
        """
        return all(key in data for key in required_keys)
    
    @staticmethod
    def get_prompt_stats(prompt: str) -> Dict[str, Any]:
        """
        Get statistics about a prompt.
        
        Args:
            prompt: Prompt to analyze
            
        Returns:
            Dictionary with prompt statistics
        """
        lines = prompt.split('\n')
        words = prompt.split()
        
        return {
            'length': len(prompt),
            'lines': len(lines),
            'words': len(words),
            'within_limit': len(prompt) <= PromptFormatter.MAX_PROMPT_LENGTH,
            'estimated_tokens': len(words) * 1.3  # Rough estimate
        }
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """
        Sanitize user input for use in prompts.
        
        Args:
            text: User input text
            
        Returns:
            Sanitized text safe for prompt injection
        """
        if not text:
            return ""
        
        # Remove potential prompt injection attempts
        text = text.replace('"""', '""')
        text = text.replace('```', '``')
        
        # Limit length
        if len(text) > 1000:
            text = PromptFormatter.truncate_content(text, 1000)
        
        return text.strip()
