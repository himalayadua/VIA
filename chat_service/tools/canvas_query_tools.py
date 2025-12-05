"""
Canvas Query Tools

Tools for chat agent to query canvas state and recent changes.
Enables "Talk to Canvas" functionality and follow-up conversations.

These tools allow the chat agent to:
- See what was just created
- Find cards by tag or category
- Explore card hierarchies
- Search canvas content
- Get canvas overview

Phase 2 of Task 22.2 Chat Integration
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from strands import tool

# Import canvas API helpers
from tools.canvas_api import (
    get_card,
    get_canvas_cards
)

logger = logging.getLogger(__name__)


@tool
def get_recent_cards(
    canvas_id: str,
    limit: int = 10,
    minutes: int = 5
) -> dict:
    """
    Get recently created cards on the canvas.
    
    Useful for:
    - Showing user what was just created
    - Answering questions about recent additions
    - Providing context for follow-up questions
    
    Args:
        canvas_id: Canvas ID
        limit: Maximum number of cards to return (default 10)
        minutes: Look back this many minutes (default 5)
        
    Returns:
        {
            "success": bool,
            "cards": list[dict],  # [{id, title, content_preview, created_at, tags}]
            "total": int,
            "time_window": str
        }
    """
    logger.info(f"Getting recent cards from canvas {canvas_id} (last {minutes} minutes)")
    
    try:
        # Validate parameters
        limit = max(1, min(limit, 50))  # Clamp between 1 and 50
        minutes = max(1, min(minutes, 60))  # Clamp between 1 and 60
        
        # Get all cards
        all_cards = get_canvas_cards(canvas_id)
        
        if not all_cards:
            return {
                "success": True,
                "cards": [],
                "total": 0,
                "time_window": f"last {minutes} minutes",
                "message": "No cards found on canvas"
            }
        
        # Filter by creation time
        cutoff = datetime.now() - timedelta(minutes=minutes)
        recent_cards = []
        
        for card in all_cards:
            created_at_str = card.get("created_at", "")
            if created_at_str:
                try:
                    created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                    if created_at > cutoff:
                        recent_cards.append(card)
                except (ValueError, AttributeError):
                    # Skip cards with invalid timestamps
                    continue
        
        # Sort by creation time (newest first)
        recent_cards.sort(
            key=lambda x: x.get("created_at", ""),
            reverse=True
        )
        
        # Limit results
        recent_cards = recent_cards[:limit]
        
        # Format for response
        formatted_cards = []
        for card in recent_cards:
            content = card.get("content", "")
            content_preview = content[:200] + "..." if len(content) > 200 else content
            
            formatted_cards.append({
                "id": card["id"],
                "title": card.get("title", "Untitled"),
                "content_preview": content_preview,
                "created_at": card.get("created_at"),
                "tags": card.get("tags", []),
                "type": card.get("card_type", "rich_text")
            })
        
        logger.info(f"Found {len(formatted_cards)} recent cards")
        
        return {
            "success": True,
            "cards": formatted_cards,
            "total": len(formatted_cards),
            "time_window": f"last {minutes} minutes"
        }
        
    except Exception as e:
        logger.error(f"Error getting recent cards: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "cards": [],
            "total": 0
        }


@tool
def get_cards_by_tag(
    canvas_id: str,
    tag: str,
    limit: int = 20
) -> dict:
    """
    Get cards filtered by tag.
    
    Useful for:
    - Finding all examples
    - Finding all questions
    - Finding cards by category
    - Exploring specific topics
    
    Args:
        canvas_id: Canvas ID
        tag: Tag to filter by (case-insensitive)
        limit: Maximum number of cards (default 20)
        
    Returns:
        {
            "success": bool,
            "cards": list[dict],
            "total": int,
            "tag": str
        }
    """
    logger.info(f"Getting cards with tag '{tag}' from canvas {canvas_id}")
    
    try:
        # Validate parameters
        limit = max(1, min(limit, 50))  # Clamp between 1 and 50
        tag_lower = tag.lower()
        
        # Get all cards
        all_cards = get_canvas_cards(canvas_id)
        
        if not all_cards:
            return {
                "success": True,
                "cards": [],
                "total": 0,
                "tag": tag,
                "message": "No cards found on canvas"
            }
        
        # Filter by tag
        tagged_cards = []
        for card in all_cards:
            card_tags = card.get("tags", [])
            if any(t.lower() == tag_lower for t in card_tags):
                tagged_cards.append(card)
        
        # Limit results
        tagged_cards = tagged_cards[:limit]
        
        # Format for response
        formatted_cards = []
        for card in tagged_cards:
            content = card.get("content", "")
            content_preview = content[:200] + "..." if len(content) > 200 else content
            
            formatted_cards.append({
                "id": card["id"],
                "title": card.get("title", "Untitled"),
                "content_preview": content_preview,
                "tags": card.get("tags", []),
                "type": card.get("card_type", "rich_text")
            })
        
        logger.info(f"Found {len(formatted_cards)} cards with tag '{tag}'")
        
        return {
            "success": True,
            "cards": formatted_cards,
            "total": len(formatted_cards),
            "tag": tag
        }
        
    except Exception as e:
        logger.error(f"Error getting cards by tag: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "cards": [],
            "total": 0,
            "tag": tag
        }


@tool
def get_card_children(
    card_id: str,
    canvas_id: str
) -> dict:
    """
    Get all child cards of a specific card.
    
    Useful for:
    - Exploring card hierarchies
    - Understanding what was generated from a parent
    - Navigating card relationships
    - Answering "what did you create under X?"
    
    Args:
        card_id: Parent card ID
        canvas_id: Canvas ID
        
    Returns:
        {
            "success": bool,
            "parent": dict,
            "children": list[dict],
            "total_children": int
        }
    """
    logger.info(f"Getting children of card {card_id}")
    
    try:
        # Get parent card
        parent_card = get_card(card_id)
        if not parent_card:
            return {
                "success": False,
                "error": f"Card {card_id} not found"
            }
        
        # Get all cards on canvas
        all_cards = get_canvas_cards(canvas_id)
        
        # Find children
        children = []
        for card in all_cards:
            if card.get("parent_id") == card_id:
                children.append(card)
        
        # Format parent
        parent_content = parent_card.get("content", "")
        parent_preview = parent_content[:200] + "..." if len(parent_content) > 200 else parent_content
        
        formatted_parent = {
            "id": parent_card["id"],
            "title": parent_card.get("title", "Untitled"),
            "content_preview": parent_preview,
            "type": parent_card.get("card_type", "rich_text")
        }
        
        # Format children
        formatted_children = []
        for child in children:
            content = child.get("content", "")
            content_preview = content[:200] + "..." if len(content) > 200 else content
            
            formatted_children.append({
                "id": child["id"],
                "title": child.get("title", "Untitled"),
                "content_preview": content_preview,
                "type": child.get("card_type", "rich_text"),
                "tags": child.get("tags", [])
            })
        
        logger.info(f"Found {len(formatted_children)} children for card {card_id}")
        
        return {
            "success": True,
            "parent": formatted_parent,
            "children": formatted_children,
            "total_children": len(formatted_children)
        }
        
    except Exception as e:
        logger.error(f"Error getting card children: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "parent": None,
            "children": [],
            "total_children": 0
        }


@tool
def search_canvas_by_content(
    canvas_id: str,
    query: str,
    limit: int = 10
) -> dict:
    """
    Search canvas cards by content.
    
    Useful for:
    - Finding specific information
    - Answering "where did I put X?"
    - Locating related cards
    - Content discovery
    
    Args:
        canvas_id: Canvas ID
        query: Search query
        limit: Maximum results (default 10)
        
    Returns:
        {
            "success": bool,
            "cards": list[dict],
            "total": int,
            "query": str
        }
    """
    logger.info(f"Searching canvas {canvas_id} for: {query}")
    
    try:
        # Validate parameters
        limit = max(1, min(limit, 50))  # Clamp between 1 and 50
        
        # Get all cards
        all_cards = get_canvas_cards(canvas_id)
        
        if not all_cards:
            return {
                "success": True,
                "cards": [],
                "total": 0,
                "query": query,
                "message": "No cards found on canvas"
            }
        
        # Simple text search (case-insensitive)
        query_lower = query.lower()
        matching_cards = []
        
        for card in all_cards:
            title = card.get("title", "").lower()
            content = card.get("content", "").lower()
            
            # Calculate relevance score
            title_match = query_lower in title
            content_match = query_lower in content
            
            if title_match or content_match:
                # Title matches are more relevant
                relevance = "high" if title_match else "medium"
                
                card_copy = card.copy()
                card_copy["_relevance"] = relevance
                matching_cards.append(card_copy)
        
        # Sort by relevance (high first)
        matching_cards.sort(key=lambda x: x.get("_relevance", "low"), reverse=True)
        
        # Limit results
        matching_cards = matching_cards[:limit]
        
        # Format for response
        formatted_cards = []
        for card in matching_cards:
            content = card.get("content", "")
            content_preview = content[:200] + "..." if len(content) > 200 else content
            
            formatted_cards.append({
                "id": card["id"],
                "title": card.get("title", "Untitled"),
                "content_preview": content_preview,
                "relevance": card.get("_relevance", "medium"),
                "type": card.get("card_type", "rich_text"),
                "tags": card.get("tags", [])
            })
        
        logger.info(f"Found {len(formatted_cards)} cards matching '{query}'")
        
        return {
            "success": True,
            "cards": formatted_cards,
            "total": len(formatted_cards),
            "query": query
        }
        
    except Exception as e:
        logger.error(f"Error searching canvas: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "cards": [],
            "total": 0,
            "query": query
        }


@tool
def get_canvas_summary(
    canvas_id: str
) -> dict:
    """
    Get a high-level summary of the canvas.
    
    Useful for:
    - Understanding canvas structure
    - Getting overview before answering questions
    - Providing context to user
    - Canvas statistics
    
    Args:
        canvas_id: Canvas ID
        
    Returns:
        {
            "success": bool,
            "summary": dict,
            "top_tags": list[str],
            "card_types": dict,
            "recent_activity": str
        }
    """
    logger.info(f"Getting summary for canvas {canvas_id}")
    
    try:
        # Get all cards
        all_cards = get_canvas_cards(canvas_id)
        
        if not all_cards:
            return {
                "success": True,
                "summary": {
                    "total_cards": 0,
                    "message": "Canvas is empty"
                },
                "top_tags": [],
                "card_types": {},
                "recent_activity": "No recent activity"
            }
        
        # Calculate statistics
        total_cards = len(all_cards)
        
        # Count card types
        card_types = {}
        for card in all_cards:
            card_type = card.get("card_type", "unknown")
            card_types[card_type] = card_types.get(card_type, 0) + 1
        
        # Count tags
        tag_counts = {}
        for card in all_cards:
            for tag in card.get("tags", []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # Get top 5 tags
        top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        top_tags = [tag for tag, count in top_tags]
        
        # Find recent activity
        recent_cards = sorted(
            all_cards,
            key=lambda x: x.get("created_at", ""),
            reverse=True
        )[:3]
        
        if recent_cards:
            recent_titles = [c.get("title", "Untitled") for c in recent_cards]
            recent_activity = f"Recently added: {', '.join(recent_titles)}"
        else:
            recent_activity = "No recent activity"
        
        # Count hierarchies (cards with children)
        parent_ids = set(card.get("parent_id") for card in all_cards if card.get("parent_id"))
        hierarchies = len(parent_ids)
        
        summary = {
            "total_cards": total_cards,
            "hierarchies": hierarchies,
            "unique_tags": len(tag_counts),
            "card_types_count": len(card_types)
        }
        
        logger.info(f"Canvas summary: {total_cards} cards, {hierarchies} hierarchies")
        
        return {
            "success": True,
            "summary": summary,
            "top_tags": top_tags,
            "card_types": card_types,
            "recent_activity": recent_activity
        }
        
    except Exception as e:
        logger.error(f"Error getting canvas summary: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "summary": {},
            "top_tags": [],
            "card_types": {},
            "recent_activity": "Error"
        }
