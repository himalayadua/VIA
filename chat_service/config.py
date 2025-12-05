"""
Configuration management for Via Canvas AI Service

Loads configuration from environment variables using pydantic-settings.
"""

import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # NVIDIA NIM Configuration
    nvidia_nim_api_key: str = Field(
        default="",
        description="NVIDIA NIM API key",
        alias="NVIDIA_NIM_API_KEY"
    )
    nvidia_nim_base_url: str = Field(
        default="https://integrate.api.nvidia.com/v1",
        description="NVIDIA NIM base URL",
        alias="NVIDIA_NIM_BASE_URL"
    )
    nvidia_nim_model: str = Field(
        default="meta/llama-3.1-70b-instruct",
        description="NVIDIA NIM model ID",
        alias="NVIDIA_NIM_MODEL"
    )
    nvidia_nim_temperature: float = Field(
        default=0.7,
        description="Model temperature",
        alias="NVIDIA_NIM_TEMPERATURE"
    )
    nvidia_nim_max_tokens: int = Field(
        default=4096,
        description="Maximum tokens",
        alias="NVIDIA_NIM_MAX_TOKENS"
    )
    
    # Category System - LLM API Key
    api_key_llm: str = Field(
        default="",
        description="API key for LLM (category classification)",
        alias="API_KEY_LLM"
    )
    llm_model: str = Field(
        default="openai/gpt-oss-120b",
        description="LLM model for category classification",
        alias="LLM_MODEL"
    )
    
    # Category System - Embedding API Key
    api_key_emb: str = Field(
        default="",
        description="API key for embeddings",
        alias="API_KEY_EMB"
    )
    embedding_model: str = Field(
        default="nvidia/llama-3.2-nemoretriever-1b-vlm-embed-v1",
        description="Embedding model",
        alias="EMBEDDING_MODEL"
    )
    
    # Database Configuration
    db_host: str = Field(
        default="localhost",
        description="PostgreSQL host",
        alias="DB_HOST"
    )
    db_port: int = Field(
        default=5432,
        description="PostgreSQL port",
        alias="DB_PORT"
    )
    db_name: str = Field(
        default="via_canvas",
        description="PostgreSQL database name",
        alias="DB_NAME"
    )
    db_user: str = Field(
        default="viacanvas",
        description="PostgreSQL user",
        alias="DB_USER"
    )
    db_password: str = Field(
        default="viacanvas_dev",
        description="PostgreSQL password",
        alias="DB_PASSWORD"
    )
    
    # Server Configuration
    port: int = Field(
        default=8000,
        description="Server port",
        alias="PORT"
    )
    host: str = Field(
        default="0.0.0.0",
        description="Server host",
        alias="HOST"
    )
    
    # CORS Configuration
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:5173",
        description="Comma-separated list of allowed CORS origins",
        alias="CORS_ORIGINS"
    )
    
    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level",
        alias="LOG_LEVEL"
    )
    
    # Qdrant Configuration
    qdrant_host: str = Field(
        default="localhost",
        description="Qdrant host",
        alias="QDRANT_HOST"
    )
    qdrant_port: int = Field(
        default=6333,
        description="Qdrant port",
        alias="QDRANT_PORT"
    )
    qdrant_collection: str = Field(
        default="via_canvas_kb",
        description="Qdrant collection name",
        alias="QDRANT_COLLECTION"
    )
    qdrant_api_key: str = Field(
        default="",
        description="Qdrant API key (optional)",
        alias="QDRANT_API_KEY"
    )
    
    # RAG Configuration
    rag_chunk_size: int = Field(
        default=500,
        description="Text chunk size in words for RAG",
        alias="RAG_CHUNK_SIZE"
    )
    rag_chunk_overlap: int = Field(
        default=50,
        description="Chunk overlap in words",
        alias="RAG_CHUNK_OVERLAP"
    )
    rag_top_k: int = Field(
        default=5,
        description="Number of top results to retrieve",
        alias="RAG_TOP_K"
    )
    rag_score_threshold: float = Field(
        default=0.7,
        description="Minimum similarity score threshold",
        alias="RAG_SCORE_THRESHOLD"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def get_cors_origins(self) -> List[str]:
        """Get CORS origins as a list"""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
    
    def get_db_connection_string(self) -> str:
        """Get PostgreSQL connection string"""
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    def get_db_config(self) -> dict:
        """Get database configuration as a dictionary"""
        return {
            "host": self.db_host,
            "port": self.db_port,
            "database": self.db_name,
            "user": self.db_user,
            "password": self.db_password,
        }


# Global settings instance
settings = Settings()


# Validation on import
if not settings.nvidia_nim_api_key:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning("⚠️  NVIDIA_NIM_API_KEY not set! AI features will not work.")
    logger.warning("   Please set NVIDIA_NIM_API_KEY in your .env file")
