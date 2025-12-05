"""LLM Provider for Category Classification.

Provides LLM inference using NVIDIA API for category classification.
"""

import logging
import json
from typing import Dict, Optional
from openai import OpenAI

from config import settings

logger = logging.getLogger(__name__)


class CategoryLLM:
    """LLM for category classification."""
    
    def __init__(self, api_key: str = None, model: str = None):
        """Initialize LLM provider.
        
        Args:
            api_key: API key (defaults to settings.api_key_llm)
            model: Model name (defaults to settings.llm_model)
        """
        self.api_key = api_key or settings.api_key_llm
        self.model = model or settings.llm_model
        
        if not self.api_key:
            logger.warning("No LLM API key provided, will use fallback classification")
            self.client = None
        else:
            self.client = OpenAI(
                base_url="https://integrate.api.nvidia.com/v1",
                api_key=self.api_key
            )
        
        logger.info(f"Initialized CategoryLLM with model: {self.model}")
    
    def generate(
        self,
        prompt: str,
        response_format: str = "json",
        max_tokens: int = 500,
        temperature: float = 0.7
    ) -> str:
        """Generate response from LLM.
        
        Args:
            prompt: Input prompt
            response_format: Expected format ("json" or "text")
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Generated text response
        """
        if not self.client:
            logger.warning("No API key, cannot generate LLM response")
            raise ValueError("LLM API key not configured")
        
        try:
            # Add JSON instruction if needed
            if response_format == "json":
                prompt += "\n\nIMPORTANT: Respond with valid JSON only, no additional text."
            
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                top_p=1,
                max_tokens=max_tokens,
                stream=False  # Non-streaming for classification
            )
            
            response = completion.choices[0].message.content
            
            logger.debug(f"Generated response ({len(response)} chars)")
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            raise
    
    def classify_category(
        self,
        card_content: str,
        card_title: str,
        card_keywords: list,
        candidates: list
    ) -> Dict:
        """Classify card into category (convenience method).
        
        Args:
            card_content: Card content
            card_title: Card title
            card_keywords: Card keywords
            candidates: List of (CategoryProfile, score) tuples
            
        Returns:
            Classification result dict
        """
        # This will be called by CategoryClassifier
        # Just a placeholder for now
        pass


# Global instance
_llm_provider = None


def get_llm_provider() -> CategoryLLM:
    """Get global LLM provider instance."""
    global _llm_provider
    
    if _llm_provider is None:
        _llm_provider = CategoryLLM()
    
    return _llm_provider
