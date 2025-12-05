"""
Card Placer

Intelligent card placement system that determines semantic relationships
between cards based on content similarity.

This module focuses on SEMANTIC INTELLIGENCE:
- Finding the best parent card based on content similarity
- Analyzing relationships between cards
- Learning from user feedback

POSITIONING is handled by the frontend layout algorithms (ReactFlow/Dagre).
"""

import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class CardPlacer:
    """
    Intelligent card placement system.
    
    Determines semantic relationships based on:
    - Content similarity (TF-IDF)
    - Parent-child relationships
    - User feedback and learning
    
    Note: Visual positioning is handled by frontend layout algorithms.
    This class focuses purely on semantic intelligence.
    """
    
    # Configuration constants
    MIN_SIMILARITY_THRESHOLD = 0.3  # Minimum similarity to consider as parent
    PARENT_SIMILARITY_THRESHOLD = 0.5  # Preferred similarity for parent
    
    def __init__(self):
        """Initialize card placer."""
        logger.info("CardPlacer initialized - semantic intelligence mode")
    
    def find_best_parent(
        self,
        new_card_content: str,
        canvas_id: str,
        min_similarity: float = None
    ) -> Tuple[Optional[str], float]:
        """
        Find the best parent card for a new card based on content similarity.
        
        Uses the find_similar_cards tool to calculate TF-IDF similarity
        between the new card content and all existing cards.
        
        Args:
            new_card_content: Content of the new card
            canvas_id: Canvas ID to search in
            min_similarity: Minimum similarity threshold (default: 0.3)
            
        Returns:
            Tuple of (parent_card_id, similarity_score)
            Returns (None, 0.0) if no suitable parent found
        """
        if min_similarity is None:
            min_similarity = self.MIN_SIMILARITY_THRESHOLD
        
        try:
            # Import here to avoid circular dependency
            from tools.canvas_tools import find_similar_cards
            
            logger.info(f"Finding best parent for new card on canvas {canvas_id}")
            
            # Find similar cards
            result = find_similar_cards(
                content=new_card_content,
                canvas_id=canvas_id,
                limit=5,
                min_similarity=min_similarity
            )
            
            if not result.get("success") or not result.get("similar_cards"):
                logger.info("No similar cards found, card will be root-level")
                return None, 0.0
            
            # Get the most similar card as parent
            similar_cards = result["similar_cards"]
            best_match = similar_cards[0]
            
            parent_id = best_match["id"]
            similarity = best_match["similarity_score"]
            
            logger.info(f"Found best parent: {parent_id} (similarity: {similarity:.2f})")
            
            return parent_id, similarity
            
        except Exception as e:
            logger.error(f"Error finding best parent: {e}", exc_info=True)
            return None, 0.0
    
    def get_parent_confidence(self, similarity_score: float) -> str:
        """
        Get confidence level for parent selection.
        
        Args:
            similarity_score: Similarity score (0.0 to 1.0)
            
        Returns:
            Confidence level: "very_high", "high", "moderate", "low"
        """
        if similarity_score >= 0.8:
            return "very_high"
        elif similarity_score >= 0.6:
            return "high"
        elif similarity_score >= 0.4:
            return "moderate"
        else:
            return "low"
    
    def get_placement_reasoning(
        self,
        parent_card: Optional[Dict],
        similarity_score: float
    ) -> str:
        """
        Generate human-readable explanation of placement decision.
        
        Args:
            parent_card: Parent card dict or None
            similarity_score: Similarity score with parent
            
        Returns:
            Reasoning string
        """
        if parent_card and similarity_score > 0:
            parent_title = parent_card.get("title", "Untitled")
            confidence = self.get_parent_confidence(similarity_score)
            
            confidence_text = {
                "very_high": "very high",
                "high": "high",
                "moderate": "moderate",
                "low": "low"
            }.get(confidence, "unknown")
            
            return f"Placed as child of '{parent_title}' due to {confidence_text} content similarity ({similarity_score:.2f})"
        else:
            return "Placed as root-level card (no similar content found)"
