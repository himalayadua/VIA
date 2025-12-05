"""
Model Provider - Shared NVIDIA NIM Model Instance

Provides a shared Strands-compatible model instance for NVIDIA NIM.
Uses custom adapter to ensure proper StreamEvent format.
"""

import logging
from config import settings

logger = logging.getLogger(__name__)

# Global model instance
_model_instance = None


def get_nvidia_nim_model():
    """
    Get shared Strands-compatible NVIDIA NIM model.
    
    Creates model on first call, returns cached instance on subsequent calls.
    Uses NVIDIAStrandsModel adapter to ensure proper Strands StreamEvent format.
    
    Returns:
        NVIDIAStrandsModel instance configured for NVIDIA NIM
    """
    global _model_instance
    
    if _model_instance is None:
        logger.info("Creating NVIDIA NIM Strands model instance")
        
        if not settings.nvidia_nim_api_key:
            logger.error("NVIDIA_NIM_API_KEY not set!")
            raise ValueError("NVIDIA_NIM_API_KEY is required")
        
        from .nvidia_strands_adapter import NVIDIAStrandsModel
        
        _model_instance = NVIDIAStrandsModel(
            api_key=settings.nvidia_nim_api_key,
            model_id=settings.nvidia_nim_model
        )
        
        logger.info(f"✅ Strands model created for: {settings.nvidia_nim_model}")
    
    return _model_instance


def reset_model():
    """Reset model instance (useful for testing or config changes)"""
    global _model_instance
    _model_instance = None
    logger.info("Model instance reset")
