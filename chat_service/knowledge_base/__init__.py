"""
Knowledge Base Module

Provides RAG (Retrieval-Augmented Generation) capabilities for Via Canvas.
Includes vector storage, document indexing, and semantic search.
"""

from .vector_store import VectorStore
from .rag_service import RAGService
from .index_tracker import IndexTracker

__all__ = ['VectorStore', 'RAGService', 'IndexTracker']
