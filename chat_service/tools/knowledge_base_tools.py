"""
Knowledge Base Tools

Strands tools for interacting with the knowledge base.
Provides search and context retrieval capabilities for AI agents.
"""

import logging
from strands import tool
from typing import Optional

logger = logging.getLogger(__name__)

# Global RAG service instance (initialized in app.py)
rag_service = None


def set_rag_service(service):
    """Set the global RAG service instance"""
    global rag_service
    rag_service = service
    logger.info("RAG service set for knowledge base tools")


@tool
async def search_knowledge_base(
    query: str,
    canvas_id: str,
    top_k: int = 5
) -> dict:
    """Search the canvas knowledge base for relevant information.
    
    Use this tool to find relevant content from the canvas when answering questions.
    The knowledge base contains all indexed cards and their content.
    
    Args:
        query: Search query or question to find relevant content for
        canvas_id: Canvas ID to search within
        top_k: Number of results to return (default: 5)
    
    Returns:
        Dict with search results including content, scores, and metadata
    
    Example:
        result = await search_knowledge_base(
            query="What is machine learning?",
            canvas_id="canvas-123",
            top_k=5
        )
    """
    if not rag_service:
        return {
            "success": False,
            "error": "RAG service not initialized",
            "results": []
        }
    
    try:
        results = await rag_service.search_knowledge_base(
            query=query,
            canvas_id=canvas_id,
            top_k=top_k
        )
        
        return {
            "success": True,
            "results": results,
            "count": len(results),
            "query": query
        }
    
    except Exception as e:
        logger.error(f"Error in search_knowledge_base tool: {e}")
        return {
            "success": False,
            "error": str(e),
            "results": []
        }


@tool
async def get_knowledge_context(
    query: str,
    canvas_id: str,
    top_k: int = 5
) -> str:
    """Get formatted context from knowledge base for answering questions.
    
    This tool retrieves relevant context from the canvas and formats it
    for use in generating responses. Use this when you need background
    information to answer a user's question.
    
    Args:
        query: Query to find relevant context for
        canvas_id: Canvas ID to search within
        top_k: Number of context chunks to retrieve (default: 5)
    
    Returns:
        Formatted context string with relevance scores
    
    Example:
        context = await get_knowledge_context(
            query="Explain neural networks",
            canvas_id="canvas-123",
            top_k=3
        )
    """
    if not rag_service:
        return "Error: RAG service not initialized"
    
    try:
        context = await rag_service.retrieve_context(
            query=query,
            canvas_id=canvas_id,
            top_k=top_k
        )
        
        if not context:
            return "No relevant context found in knowledge base."
        
        return f"Context from canvas knowledge base:\n\n{context}"
    
    except Exception as e:
        logger.error(f"Error in get_knowledge_context tool: {e}")
        return f"Error retrieving context: {str(e)}"


@tool
async def get_knowledge_base_stats(
    canvas_id: Optional[str] = None
) -> dict:
    """Get statistics about the knowledge base.
    
    Returns information about indexed content, including number of
    entities, chunks, and indexing status.
    
    Args:
        canvas_id: Optional canvas ID to get stats for specific canvas
    
    Returns:
        Dict with knowledge base statistics
    
    Example:
        stats = await get_knowledge_base_stats(canvas_id="canvas-123")
    """
    if not rag_service:
        return {
            "success": False,
            "error": "RAG service not initialized"
        }
    
    try:
        stats = await rag_service.get_stats(canvas_id)
        
        return {
            "success": True,
            **stats
        }
    
    except Exception as e:
        logger.error(f"Error in get_knowledge_base_stats tool: {e}")
        return {
            "success": False,
            "error": str(e)
        }
