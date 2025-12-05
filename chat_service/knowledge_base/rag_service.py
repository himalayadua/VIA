"""
RAG Service

Provides Retrieval-Augmented Generation capabilities.
Handles document chunking, indexing, and semantic search.
"""

import logging
import re
from typing import List, Dict, Any, Optional
from .vector_store import VectorStore
from .index_tracker import IndexTracker
from graph.embedding_provider import EmbeddingProvider

logger = logging.getLogger(__name__)


class RAGService:
    """RAG (Retrieval-Augmented Generation) service"""
    
    def __init__(
        self,
        vector_store: VectorStore,
        index_tracker: IndexTracker,
        embedding_provider: EmbeddingProvider,
        chunk_size: int = 500,
        chunk_overlap: int = 50
    ):
        """
        Initialize RAG Service
        
        Args:
            vector_store: Vector store instance
            index_tracker: Index tracker instance
            embedding_provider: Embedding provider instance
            chunk_size: Chunk size in words
            chunk_overlap: Overlap size in words
        """
        self.vector_store = vector_store
        self.index_tracker = index_tracker
        self.embedding_provider = embedding_provider
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        logger.info(f"RAGService initialized (chunk_size={chunk_size}, overlap={chunk_overlap})")
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks
        
        Args:
            text: Text to chunk
        
        Returns:
            List of text chunks
        """
        # Clean text
        text = re.sub(r'\s+', ' ', text).strip()
        
        if not text:
            return []
        
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk = ' '.join(words[i:i + self.chunk_size])
            if chunk:
                chunks.append(chunk)
            
            # Stop if we've reached the end
            if i + self.chunk_size >= len(words):
                break
        
        return chunks
    
    async def index_card(
        self,
        card_id: str,
        content: str,
        canvas_id: str,
        card_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        force_reindex: bool = False
    ) -> Dict[str, Any]:
        """
        Index a card's content
        
        Args:
            card_id: Card ID
            content: Card content
            canvas_id: Canvas ID
            card_type: Card type
            metadata: Additional metadata
            force_reindex: Force re-indexing even if already indexed
        
        Returns:
            Indexing result dictionary
        """
        entity_type = "card"
        
        try:
            # Check if already indexed and content unchanged
            if not force_reindex:
                is_indexed = await self.index_tracker.is_indexed(card_id, entity_type)
                if is_indexed:
                    needs_reindex = await self.index_tracker.needs_reindex(
                        card_id, entity_type, content
                    )
                    if not needs_reindex:
                        logger.info(f"Card {card_id} already indexed with same content, skipping")
                        return {
                            "indexed": False,
                            "reason": "already_indexed",
                            "card_id": card_id
                        }
            
            # Chunk the content
            chunks = self.chunk_text(content)
            
            if not chunks:
                logger.warning(f"No content to index for card {card_id}")
                return {
                    "indexed": False,
                    "reason": "no_content",
                    "card_id": card_id
                }
            
            # Generate embeddings (one at a time since get_embedding is not async)
            embeddings = []
            for chunk in chunks:
                embedding = self.embedding_provider.get_embedding(chunk)
                embeddings.append(embedding)
            
            # Convert numpy arrays to lists
            embeddings_list = [emb.tolist() if hasattr(emb, 'tolist') else list(emb) for emb in embeddings]
            
            # Store in vector database
            doc_id = f"card_{card_id}"
            point_ids = await self.vector_store.index_document(
                doc_id=doc_id,
                chunks=chunks,
                embeddings=embeddings_list,
                metadata={
                    "canvas_id": canvas_id,
                    "card_id": card_id,
                    "entity_id": card_id,
                    "entity_type": entity_type,
                    "card_type": card_type,
                    **(metadata or {})
                }
            )
            
            # Record in tracking table
            await self.index_tracker.record_index(
                entity_id=card_id,
                entity_type=entity_type,
                canvas_id=canvas_id,
                content=content,
                num_chunks=len(chunks),
                qdrant_point_ids=point_ids
            )
            
            logger.info(f"Successfully indexed card {card_id} ({len(chunks)} chunks)")
            
            return {
                "indexed": True,
                "card_id": card_id,
                "doc_id": doc_id,
                "num_chunks": len(chunks),
                "point_ids": point_ids
            }
        
        except Exception as e:
            logger.error(f"Error indexing card {card_id}: {e}", exc_info=True)
            
            # Record failure
            await self.index_tracker.record_index_failure(
                entity_id=card_id,
                entity_type=entity_type,
                canvas_id=canvas_id,
                error_message=str(e)
            )
            
            return {
                "indexed": False,
                "reason": "error",
                "error": str(e),
                "card_id": card_id
            }
    
    async def delete_card_index(
        self,
        card_id: str
    ) -> bool:
        """
        Delete card from index
        
        Args:
            card_id: Card ID
        
        Returns:
            True if successful
        """
        entity_type = "card"
        
        try:
            # Delete from vector store
            await self.vector_store.delete_by_entity(card_id, entity_type)
            
            # Mark as deleted in tracking
            await self.index_tracker.mark_deleted(card_id, entity_type)
            
            logger.info(f"Deleted card index: {card_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error deleting card index {card_id}: {e}")
            return False
    
    async def search_knowledge_base(
        self,
        query: str,
        canvas_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        top_k: int = 5,
        score_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Search the knowledge base
        
        Args:
            query: Search query
            canvas_id: Optional canvas ID filter
            entity_type: Optional entity type filter
            top_k: Number of results to return
            score_threshold: Minimum similarity score
        
        Returns:
            List of search results
        """
        try:
            # Generate query embedding (not async)
            query_embedding = self.embedding_provider.get_embedding(query)
            
            # Convert to list
            query_embedding_list = query_embedding.tolist() if hasattr(query_embedding, 'tolist') else list(query_embedding)
            
            # Search vector store
            results = await self.vector_store.search(
                query_embedding=query_embedding_list,
                canvas_id=canvas_id,
                entity_type=entity_type,
                limit=top_k,
                score_threshold=score_threshold
            )
            
            logger.info(f"Search for '{query}' returned {len(results)} results")
            return results
        
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return []
    
    async def retrieve_context(
        self,
        query: str,
        canvas_id: str,
        top_k: int = 5,
        score_threshold: float = 0.7
    ) -> str:
        """
        Retrieve formatted context for RAG
        
        Args:
            query: Query to find context for
            canvas_id: Canvas ID
            top_k: Number of context chunks
            score_threshold: Minimum similarity score
        
        Returns:
            Formatted context string
        """
        results = await self.search_knowledge_base(
            query=query,
            canvas_id=canvas_id,
            top_k=top_k,
            score_threshold=score_threshold
        )
        
        if not results:
            return ""
        
        # Format context
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(
                f"[{i}] (Relevance: {result['score']:.2f})\n{result['content']}\n"
            )
        
        return "\n".join(context_parts)
    
    async def get_stats(self, canvas_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get knowledge base statistics
        
        Args:
            canvas_id: Optional canvas ID filter
        
        Returns:
            Statistics dictionary
        """
        try:
            # Get tracking stats
            tracking_stats = await self.index_tracker.get_stats(canvas_id)
            
            # Get vector store info
            collection_info = await self.vector_store.get_collection_info()
            
            return {
                **tracking_stats,
                "collection_info": collection_info
            }
        
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}
