"""
Vector Store Service

Manages vector storage and retrieval using Qdrant.
Handles embedding storage, similarity search, and collection management.
"""

import logging
from typing import List, Dict, Any, Optional
import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    SearchRequest
)

logger = logging.getLogger(__name__)


class VectorStore:
    """Manages vector storage and retrieval using Qdrant"""
    
    def __init__(
        self,
        host: str,
        port: int,
        collection_name: str,
        api_key: Optional[str] = None,
        vector_size: int = 384  # all-MiniLM-L6-v2 dimension
    ):
        """
        Initialize Vector Store
        
        Args:
            host: Qdrant host
            port: Qdrant port
            collection_name: Name of the collection
            api_key: Optional API key for Qdrant Cloud
            vector_size: Dimension of embedding vectors
        """
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.vector_size = vector_size
        
        # Initialize Qdrant client
        self.client = QdrantClient(
            host=host,
            port=port,
            api_key=api_key if api_key else None
        )
        
        # Ensure collection exists
        self._ensure_collection()
        
        logger.info(f"VectorStore initialized: {host}:{port}/{collection_name}")
    
    def _ensure_collection(self):
        """Create collection if it doesn't exist"""
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)
            
            if not exists:
                logger.info(f"Creating collection: {self.collection_name}")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
                
                # Create payload indexes for efficient filtering
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="canvas_id",
                    field_schema="keyword"
                )
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="card_id",
                    field_schema="keyword"
                )
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="entity_type",
                    field_schema="keyword"
                )
                
                logger.info(f"Collection created successfully: {self.collection_name}")
            else:
                logger.info(f"Collection already exists: {self.collection_name}")
        
        except Exception as e:
            logger.error(f"Error ensuring collection exists: {e}")
            raise
    
    async def index_document(
        self,
        doc_id: str,
        chunks: List[str],
        embeddings: List[List[float]],
        metadata: Dict[str, Any]
    ) -> List[str]:
        """
        Index document chunks with embeddings
        
        Args:
            doc_id: Unique document identifier
            chunks: List of text chunks
            embeddings: List of embedding vectors
            metadata: Metadata to store with each chunk
        
        Returns:
            List of Qdrant point IDs
        """
        if len(chunks) != len(embeddings):
            raise ValueError(f"Chunks ({len(chunks)}) and embeddings ({len(embeddings)}) must have same length")
        
        points = []
        point_ids = []
        
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            point_id = str(uuid.uuid4())
            point_ids.append(point_id)
            
            points.append(
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "doc_id": doc_id,
                        "chunk_index": i,
                        "content": chunk,
                        "canvas_id": metadata.get("canvas_id"),
                        "card_id": metadata.get("card_id"),
                        "entity_id": metadata.get("entity_id"),
                        "entity_type": metadata.get("entity_type", "card"),
                        "card_type": metadata.get("card_type"),
                        **{k: v for k, v in metadata.items() if k not in ["canvas_id", "card_id", "entity_id", "entity_type", "card_type"]}
                    }
                )
            )
        
        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            logger.info(f"Indexed {len(points)} chunks for doc_id: {doc_id}")
            return point_ids
        
        except Exception as e:
            logger.error(f"Error indexing document {doc_id}: {e}")
            raise
    
    async def search(
        self,
        query_embedding: List[float],
        canvas_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        limit: int = 10,
        score_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Search for similar content
        
        Args:
            query_embedding: Query embedding vector
            canvas_id: Optional canvas ID to filter by
            entity_type: Optional entity type to filter by
            limit: Maximum number of results
            score_threshold: Minimum similarity score
        
        Returns:
            List of search results with scores and metadata
        """
        try:
            # Build filter
            filter_conditions = []
            if canvas_id:
                filter_conditions.append(
                    FieldCondition(
                        key="canvas_id",
                        match=MatchValue(value=canvas_id)
                    )
                )
            if entity_type:
                filter_conditions.append(
                    FieldCondition(
                        key="entity_type",
                        match=MatchValue(value=entity_type)
                    )
                )
            
            search_filter = Filter(must=filter_conditions) if filter_conditions else None
            
            # Perform search
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=search_filter
            )
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "id": result.id,
                    "score": result.score,
                    "content": result.payload.get("content"),
                    "card_id": result.payload.get("card_id"),
                    "entity_id": result.payload.get("entity_id"),
                    "entity_type": result.payload.get("entity_type"),
                    "chunk_index": result.payload.get("chunk_index"),
                    "metadata": result.payload
                })
            
            logger.info(f"Search returned {len(formatted_results)} results")
            return formatted_results
        
        except Exception as e:
            logger.error(f"Error searching: {e}")
            raise
    
    async def delete_document(self, doc_id: str) -> bool:
        """
        Delete all chunks for a document
        
        Args:
            doc_id: Document ID to delete
        
        Returns:
            True if successful
        """
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="doc_id",
                            match=MatchValue(value=doc_id)
                        )
                    ]
                )
            )
            logger.info(f"Deleted document: {doc_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {e}")
            raise
    
    async def delete_by_entity(self, entity_id: str, entity_type: str) -> bool:
        """
        Delete all chunks for an entity
        
        Args:
            entity_id: Entity ID to delete
            entity_type: Type of entity (card, document, resource)
        
        Returns:
            True if successful
        """
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="entity_id",
                            match=MatchValue(value=entity_id)
                        ),
                        FieldCondition(
                            key="entity_type",
                            match=MatchValue(value=entity_type)
                        )
                    ]
                )
            )
            logger.info(f"Deleted entity: {entity_type}/{entity_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error deleting entity {entity_type}/{entity_id}: {e}")
            raise
    
    async def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection"""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": info.config.params.vectors.size,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {}
