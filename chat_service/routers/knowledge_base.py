"""
Knowledge Base API Router

REST API endpoints for knowledge base operations.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/knowledge-base", tags=["knowledge-base"])

# Global RAG service instance (set in app.py)
rag_service = None


def set_rag_service(service):
    """Set the global RAG service instance"""
    global rag_service
    rag_service = service
    logger.info("RAG service set for knowledge base router")


class SearchRequest(BaseModel):
    """Search request model"""
    query: str = Field(..., description="Search query")
    canvas_id: str = Field(..., description="Canvas ID to search within")
    top_k: int = Field(default=10, ge=1, le=50, description="Number of results")
    score_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum similarity score")


class IndexCardRequest(BaseModel):
    """Index card request model"""
    card_id: str = Field(..., description="Card ID")
    canvas_id: str = Field(..., description="Canvas ID")
    content: str = Field(..., description="Card content")
    card_type: str = Field(default="richtext", description="Card type")
    force_reindex: bool = Field(default=False, description="Force re-indexing")


class DeleteIndexRequest(BaseModel):
    """Delete index request model"""
    card_id: str = Field(..., description="Card ID to delete from index")


@router.post("/search")
async def search_knowledge_base(request: SearchRequest):
    """
    Search the knowledge base
    
    Performs semantic search across indexed content in the specified canvas.
    Returns relevant chunks with similarity scores.
    """
    if not rag_service:
        raise HTTPException(status_code=503, detail="RAG service not initialized")
    
    try:
        results = await rag_service.search_knowledge_base(
            query=request.query,
            canvas_id=request.canvas_id,
            top_k=request.top_k,
            score_threshold=request.score_threshold
        )
        
        return {
            "success": True,
            "results": results,
            "count": len(results),
            "query": request.query
        }
    
    except Exception as e:
        logger.error(f"Error in search endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/index")
async def index_card(request: IndexCardRequest):
    """
    Index a card in the knowledge base
    
    Manually trigger indexing for a specific card. Useful for:
    - Re-indexing after content updates
    - Indexing cards that failed auto-indexing
    - Bulk indexing operations
    """
    if not rag_service:
        raise HTTPException(status_code=503, detail="RAG service not initialized")
    
    try:
        result = await rag_service.index_card(
            card_id=request.card_id,
            content=request.content,
            canvas_id=request.canvas_id,
            card_type=request.card_type,
            force_reindex=request.force_reindex
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Error in index endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/index")
async def delete_card_index(request: DeleteIndexRequest):
    """
    Delete a card from the knowledge base index
    
    Removes all indexed chunks for the specified card.
    """
    if not rag_service:
        raise HTTPException(status_code=503, detail="RAG service not initialized")
    
    try:
        success = await rag_service.delete_card_index(request.card_id)
        
        return {
            "success": success,
            "card_id": request.card_id,
            "message": "Card index deleted" if success else "Failed to delete card index"
        }
    
    except Exception as e:
        logger.error(f"Error in delete endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats(canvas_id: Optional[str] = None):
    """
    Get knowledge base statistics
    
    Returns information about indexed content, including:
    - Number of indexed entities
    - Total chunks
    - Indexing status
    - Collection information
    """
    if not rag_service:
        raise HTTPException(status_code=503, detail="RAG service not initialized")
    
    try:
        stats = await rag_service.get_stats(canvas_id)
        
        return {
            "success": True,
            **stats
        }
    
    except Exception as e:
        logger.error(f"Error in stats endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_status():
    """
    Get knowledge base service status
    
    Health check endpoint to verify the service is operational.
    """
    if not rag_service:
        return {
            "status": "unavailable",
            "message": "RAG service not initialized"
        }
    
    try:
        # Try to get collection info to verify Qdrant connection
        collection_info = await rag_service.vector_store.get_collection_info()
        
        return {
            "status": "operational",
            "backend": "qdrant",
            "collection": rag_service.vector_store.collection_name,
            "collection_info": collection_info
        }
    
    except Exception as e:
        logger.error(f"Error in status endpoint: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


@router.get("/indexed-entities")
async def get_indexed_entities(
    canvas_id: Optional[str] = None,
    entity_type: Optional[str] = None,
    limit: int = 100
):
    """
    Get list of indexed entities
    
    Returns information about entities that have been indexed,
    including their status and metadata.
    """
    if not rag_service:
        raise HTTPException(status_code=503, detail="RAG service not initialized")
    
    try:
        entities = await rag_service.index_tracker.get_indexed_entities(
            canvas_id=canvas_id,
            entity_type=entity_type,
            limit=limit
        )
        
        return {
            "success": True,
            "entities": entities,
            "count": len(entities)
        }
    
    except Exception as e:
        logger.error(f"Error in indexed-entities endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
