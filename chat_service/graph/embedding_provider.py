"""Embedding Provider using NVIDIA API.

Generates embeddings for text content using NVIDIA's embedding models.
"""

import logging
from typing import List
import numpy as np
from openai import OpenAI

from config import settings

logger = logging.getLogger(__name__)


class EmbeddingProvider:
    """Provides text embeddings using NVIDIA API."""
    
    def __init__(self, api_key: str = None, model: str = None):
        """Initialize embedding provider.
        
        Args:
            api_key: API key (defaults to settings.api_key_emb)
            model: Model name (defaults to settings.embedding_model)
        """
        self.api_key = api_key or settings.api_key_emb
        self.model = model or settings.embedding_model
        
        if not self.api_key:
            logger.warning("No embedding API key provided, embeddings will use fallback")
            self.client = None
        else:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://integrate.api.nvidia.com/v1"
            )
        
        logger.info(f"Initialized EmbeddingProvider with model: {self.model}")
    
    def get_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for text.
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector as numpy array
        """
        if not self.client:
            # Fallback: return random vector
            logger.warning("No API key, using random embedding (fallback)")
            return np.random.randn(768)
        
        try:
            response = self.client.embeddings.create(
                input=[text],
                model=self.model,
                encoding_format="float",
                extra_body={
                    "modality": ["text"],
                    "input_type": "query",
                    "truncate": "NONE"
                }
            )
            
            embedding = np.array(response.data[0].embedding)
            logger.debug(f"Generated embedding of dimension {len(embedding)}")
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            # Fallback: return random vector
            return np.random.randn(768)
    
    def get_embeddings_batch(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for multiple texts.
        
        Args:
            texts: List of input texts
            
        Returns:
            List of embedding vectors
        """
        if not self.client:
            logger.warning("No API key, using random embeddings (fallback)")
            return [np.random.randn(768) for _ in texts]
        
        try:
            response = self.client.embeddings.create(
                input=texts,
                model=self.model,
                encoding_format="float",
                extra_body={
                    "modality": ["text"],
                    "input_type": "query",
                    "truncate": "NONE"
                }
            )
            
            embeddings = [np.array(data.embedding) for data in response.data]
            logger.debug(f"Generated {len(embeddings)} embeddings")
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            # Fallback: return random vectors
            return [np.random.randn(768) for _ in texts]


# Global instance
_embedding_provider = None


def get_embedding_provider() -> EmbeddingProvider:
    """Get global embedding provider instance."""
    global _embedding_provider
    
    if _embedding_provider is None:
        _embedding_provider = EmbeddingProvider()
    
    return _embedding_provider
