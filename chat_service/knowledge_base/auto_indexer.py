"""
Auto Indexer

Automatically indexes cards when they are created or updated.
Integrates with the canvas tools to provide seamless knowledge base updates.
"""

import logging
import asyncio
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Global RAG service instance (set in app.py)
_rag_service = None


def set_rag_service(service):
    """Set the global RAG service instance"""
    global _rag_service
    _rag_service = service
    logger.info("RAG service set for auto-indexer")


async def auto_index_card(
    card_id: str,
    content: str,
    canvas_id: str,
    card_type: str = "richtext",
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Automatically index a card in the knowledge base.
    
    This function is called after card creation to index the content.
    It runs asynchronously and doesn't block card creation.
    
    Args:
        card_id: Card ID
        content: Card content
        canvas_id: Canvas ID
        card_type: Card type
        metadata: Additional metadata
    
    Returns:
        Indexing result dictionary
    """
    if not _rag_service:
        logger.warning("RAG service not available, skipping auto-indexing")
        return {
            "indexed": False,
            "reason": "rag_service_not_available"
        }
    
    # Skip indexing for empty content
    if not content or len(content.strip()) < 10:
        logger.debug(f"Skipping indexing for card {card_id}: content too short")
        return {
            "indexed": False,
            "reason": "content_too_short"
        }
    
    try:
        logger.info(f"Auto-indexing card {card_id} on canvas {canvas_id}")
        
        result = await _rag_service.index_card(
            card_id=card_id,
            content=content,
            canvas_id=canvas_id,
            card_type=card_type,
            metadata=metadata,
            force_reindex=False  # Don't force, use smart detection
        )
        
        if result.get("indexed"):
            logger.info(f"✅ Auto-indexed card {card_id} ({result.get('num_chunks', 0)} chunks)")
        else:
            reason = result.get("reason", "unknown")
            logger.debug(f"Card {card_id} not indexed: {reason}")
        
        return result
    
    except Exception as e:
        logger.error(f"Error auto-indexing card {card_id}: {e}", exc_info=True)
        return {
            "indexed": False,
            "reason": "error",
            "error": str(e)
        }


def auto_index_card_sync(
    card_id: str,
    content: str,
    canvas_id: str,
    card_type: str = "richtext",
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Synchronous wrapper for auto_index_card.
    
    Schedules the indexing task to run in the background without blocking.
    Use this from synchronous code (like tool functions).
    
    Args:
        card_id: Card ID
        content: Card content
        canvas_id: Canvas ID
        card_type: Card type
        metadata: Additional metadata
    """
    try:
        # Get or create event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Schedule the indexing task
        if loop.is_running():
            # If loop is already running, create a task
            asyncio.create_task(auto_index_card(
                card_id=card_id,
                content=content,
                canvas_id=canvas_id,
                card_type=card_type,
                metadata=metadata
            ))
        else:
            # If loop is not running, run until complete
            loop.run_until_complete(auto_index_card(
                card_id=card_id,
                content=content,
                canvas_id=canvas_id,
                card_type=card_type,
                metadata=metadata
            ))
    
    except Exception as e:
        logger.error(f"Error scheduling auto-indexing for card {card_id}: {e}")


async def auto_delete_card_index(card_id: str) -> bool:
    """
    Automatically delete a card from the knowledge base index.
    
    Args:
        card_id: Card ID to delete
    
    Returns:
        True if successful
    """
    if not _rag_service:
        logger.warning("RAG service not available, skipping index deletion")
        return False
    
    try:
        logger.info(f"Auto-deleting index for card {card_id}")
        success = await _rag_service.delete_card_index(card_id)
        
        if success:
            logger.info(f"✅ Deleted index for card {card_id}")
        else:
            logger.warning(f"Failed to delete index for card {card_id}")
        
        return success
    
    except Exception as e:
        logger.error(f"Error deleting index for card {card_id}: {e}")
        return False


async def reindex_canvas(canvas_id: str, force: bool = False) -> Dict[str, Any]:
    """
    Re-index all cards on a canvas.
    
    Useful for:
    - Initial indexing of existing canvases
    - Re-indexing after model changes
    - Fixing failed indexing attempts
    
    Args:
        canvas_id: Canvas ID to re-index
        force: Force re-indexing even if content unchanged
    
    Returns:
        Summary of re-indexing operation
    """
    if not _rag_service:
        return {
            "success": False,
            "error": "RAG service not available"
        }
    
    try:
        from tools.canvas_api import get_canvas_cards
        
        logger.info(f"Re-indexing canvas {canvas_id} (force={force})")
        
        # Get all cards on canvas
        cards = get_canvas_cards(canvas_id)
        
        indexed_count = 0
        skipped_count = 0
        failed_count = 0
        
        for card in cards:
            card_id = card.get("id")
            content = card.get("content", "")
            card_type = card.get("card_type", "richtext")
            
            if not content or len(content.strip()) < 10:
                skipped_count += 1
                continue
            
            result = await _rag_service.index_card(
                card_id=card_id,
                content=content,
                canvas_id=canvas_id,
                card_type=card_type,
                force_reindex=force
            )
            
            if result.get("indexed"):
                indexed_count += 1
            elif result.get("reason") == "already_indexed":
                skipped_count += 1
            else:
                failed_count += 1
        
        logger.info(f"✅ Re-indexing complete: {indexed_count} indexed, {skipped_count} skipped, {failed_count} failed")
        
        return {
            "success": True,
            "canvas_id": canvas_id,
            "total_cards": len(cards),
            "indexed": indexed_count,
            "skipped": skipped_count,
            "failed": failed_count
        }
    
    except Exception as e:
        logger.error(f"Error re-indexing canvas {canvas_id}: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }
