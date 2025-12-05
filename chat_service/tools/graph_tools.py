"""
Graph Tools

Tools for intelligent graph operations:
- suggest_card_placement: Suggest optimal placement for a new card
- create_intelligent_connections: Create semantic connections between cards
"""

import logging
from typing import Dict, Optional
from strands import tool

from graph import CardPlacer, ConnectionManager

logger = logging.getLogger(__name__)


@tool
def suggest_card_placement(
    card_content: str,
    canvas_id: str,
    card_title: str = ""
) -> dict:
    """
    Suggest optimal parent for a new card based on content similarity.
    
    This tool analyzes existing cards on the canvas and suggests:
    - Best parent card (if any) based on semantic similarity
    - Confidence level of the suggestion
    - Reasoning for the suggestion
    
    Note: Visual positioning is handled by frontend layout algorithms.
    This tool focuses on semantic relationships only.
    
    Args:
        card_content: Content of the new card
        canvas_id: Canvas ID where card will be placed
        card_title: Optional title for additional context
        
    Returns:
        {
            "success": bool,
            "suggested_parent_id": str | None,
            "similarity_score": float,
            "confidence": str,
            "reasoning": str
        }
    """
    logger.info(f"Suggesting parent for new card on canvas {canvas_id}")
    
    try:
        from tools.canvas_api import get_canvas_cards
        
        placer = CardPlacer()
        
        # Find best parent based on semantic similarity
        parent_id, similarity = placer.find_best_parent(
            new_card_content=card_content,
            canvas_id=canvas_id
        )
        
        # Get existing cards
        existing_cards = get_canvas_cards(canvas_id)
        
        # Find parent card object
        parent_card = None
        if parent_id:
            parent_card = next(
                (c for c in existing_cards if c["id"] == parent_id),
                None
            )
        
        # Get confidence level
        confidence = placer.get_parent_confidence(similarity)
        
        # Get reasoning
        reasoning = placer.get_placement_reasoning(parent_card, similarity)
        
        result = {
            "success": True,
            "suggested_parent_id": parent_id,
            "similarity_score": similarity,
            "confidence": confidence,
            "reasoning": reasoning
        }
        
        logger.info(f"Parent suggestion: {reasoning}")
        return result
        
    except Exception as e:
        logger.error(f"Error suggesting parent: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "suggested_parent_id": None,
            "similarity_score": 0.0,
            "confidence": "none",
            "reasoning": "Error occurred, no parent suggestion available"
        }


@tool
def create_intelligent_connections(
    card_id: str,
    canvas_id: str,
    max_connections: int = 5
) -> dict:
    """
    Create intelligent connections between a card and related cards.
    
    Analyzes semantic relationships and creates appropriate connections
    with proper types (parent-child, related, reference) and strengths.
    
    Args:
        card_id: ID of the card to create connections for
        canvas_id: Canvas ID
        max_connections: Maximum number of connections to create (default: 5)
        
    Returns:
        {
            "success": bool,
            "connections_created": int,
            "connections": list[dict],
            "summary": str
        }
    """
    logger.info(f"Creating intelligent connections for card {card_id}")
    
    try:
        from tools.canvas_api import get_card, get_canvas_cards
        
        # Get the card
        card = get_card(card_id)
        if not card:
            return {
                "success": False,
                "error": f"Card {card_id} not found",
                "connections_created": 0
            }
        
        # Get existing cards
        existing_cards = get_canvas_cards(canvas_id)
        
        # Filter out the card itself
        existing_cards = [c for c in existing_cards if c["id"] != card_id]
        
        manager = ConnectionManager()
        
        # Analyze relationships
        relationships = manager.analyze_relationships(
            new_card=card,
            existing_cards=existing_cards,
            canvas_id=canvas_id
        )
        
        # Limit to max_connections
        relationships = relationships[:max_connections]
        
        # Create connections
        connections = manager.create_connections(
            new_card_id=card_id,
            relationships=relationships,
            canvas_id=canvas_id
        )
        
        # Get summary
        summary = manager.get_connection_summary(connections)
        
        result = {
            "success": True,
            "connections_created": len(connections),
            "connections": connections,
            "summary": summary
        }
        
        logger.info(f"Created {len(connections)} intelligent connections")
        return result
        
    except Exception as e:
        logger.error(f"Error creating intelligent connections: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "connections_created": 0,
            "connections": [],
            "summary": "Error occurred while creating connections"
        }
