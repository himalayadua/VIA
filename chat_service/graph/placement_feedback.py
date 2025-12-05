"""
Placement Feedback System

Learning system that tracks user manual adjustments to card placement
and uses feedback to improve future placement decisions.
"""

import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class PlacementFeedback:
    """
    Placement feedback and learning system.
    
    Tracks user manual adjustments to AI-suggested placements
    and learns from feedback to improve future suggestions.
    """
    
    def __init__(self):
        """Initialize placement feedback system."""
        logger.info("PlacementFeedback system initialized")
    
    def record_placement(
        self,
        card_id: str,
        canvas_id: str,
        suggested_parent_id: Optional[str],
        actual_parent_id: Optional[str],
        suggested_position: Dict[str, float],
        actual_position: Dict[str, float],
        similarity_score: float,
        user_accepted: bool
    ) -> Dict:
        """
        Record placement feedback when user manually adjusts card position.
        
        Args:
            card_id: ID of the card that was placed
            canvas_id: Canvas ID
            suggested_parent_id: AI-suggested parent card ID
            actual_parent_id: User's chosen parent card ID
            suggested_position: AI-suggested position {x, y}
            actual_position: User's final position {x, y}
            similarity_score: Similarity score with suggested parent
            user_accepted: Whether user accepted AI suggestion
            
        Returns:
            Feedback record dict
        """
        try:
            feedback = {
                "card_id": card_id,
                "canvas_id": canvas_id,
                "suggested_parent_id": suggested_parent_id,
                "actual_parent_id": actual_parent_id,
                "suggested_position": suggested_position,
                "actual_position": actual_position,
                "similarity_score": similarity_score,
                "user_accepted": user_accepted,
                "created_at": datetime.now().isoformat()
            }
            
            # TODO: Store in database when placement_feedback table is created
            # For now, just log it
            logger.info(
                f"Placement feedback recorded: "
                f"card={card_id}, accepted={user_accepted}, "
                f"similarity={similarity_score:.2f}"
            )
            
            return feedback
            
        except Exception as e:
            logger.error(f"Error recording placement feedback: {e}", exc_info=True)
            return {}
    
    def get_acceptance_rate(
        self,
        canvas_id: str,
        similarity_threshold: float
    ) -> float:
        """
        Calculate acceptance rate for placements at given similarity threshold.
        
        Args:
            canvas_id: Canvas ID to analyze
            similarity_threshold: Similarity threshold to check
            
        Returns:
            Acceptance rate (0.0 to 1.0)
        """
        try:
            # TODO: Query database for feedback records
            # For now, return default
            logger.debug(
                f"Getting acceptance rate for canvas {canvas_id} "
                f"at threshold {similarity_threshold}"
            )
            
            # Placeholder: return 0.75 (75% acceptance rate)
            return 0.75
            
        except Exception as e:
            logger.error(f"Error calculating acceptance rate: {e}", exc_info=True)
            return 0.5  # Default to 50%
    
    def get_optimal_threshold(self, canvas_id: str) -> float:
        """
        Determine optimal similarity threshold based on historical feedback.
        
        Analyzes past placements to find the threshold that maximizes
        user acceptance rate.
        
        Args:
            canvas_id: Canvas ID to analyze
            
        Returns:
            Optimal similarity threshold
        """
        try:
            # TODO: Analyze feedback data to find optimal threshold
            # For now, return default
            logger.debug(f"Calculating optimal threshold for canvas {canvas_id}")
            
            # Placeholder: return default threshold
            return 0.5
            
        except Exception as e:
            logger.error(f"Error calculating optimal threshold: {e}", exc_info=True)
            return 0.5
    
    def get_placement_preferences(self, canvas_id: str) -> Dict:
        """
        Analyze user's placement preferences for this canvas.
        
        Returns insights like:
        - Preferred parent types
        - Preferred spatial arrangements
        - Common manual adjustments
        
        Args:
            canvas_id: Canvas ID to analyze
            
        Returns:
            Dict with preference insights
        """
        try:
            # TODO: Analyze feedback data for patterns
            logger.debug(f"Analyzing placement preferences for canvas {canvas_id}")
            
            # Placeholder: return default preferences
            return {
                "prefers_broader_categories": False,
                "prefers_tight_clustering": False,
                "average_manual_adjustment_distance": 0,
                "most_common_parent_type": "similar_content"
            }
            
        except Exception as e:
            logger.error(f"Error analyzing preferences: {e}", exc_info=True)
            return {}
    
    def should_adjust_placement(
        self,
        suggested_parent_id: str,
        similarity_score: float,
        canvas_id: str
    ) -> bool:
        """
        Determine if placement should be adjusted based on historical feedback.
        
        Args:
            suggested_parent_id: AI-suggested parent
            similarity_score: Similarity with parent
            canvas_id: Canvas ID
            
        Returns:
            True if placement should be adjusted, False otherwise
        """
        try:
            # Get optimal threshold for this canvas
            optimal_threshold = self.get_optimal_threshold(canvas_id)
            
            # If similarity is below optimal threshold, suggest adjustment
            if similarity_score < optimal_threshold:
                logger.debug(
                    f"Suggesting placement adjustment: "
                    f"similarity {similarity_score:.2f} < threshold {optimal_threshold:.2f}"
                )
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking placement adjustment: {e}", exc_info=True)
            return False


# Database migration SQL for placement_feedback table
# This should be added to a migration file when implementing Task 6.3 fully

PLACEMENT_FEEDBACK_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS placement_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    card_id UUID NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    canvas_id UUID NOT NULL REFERENCES canvases(id) ON DELETE CASCADE,
    suggested_parent_id UUID REFERENCES nodes(id) ON DELETE SET NULL,
    actual_parent_id UUID REFERENCES nodes(id) ON DELETE SET NULL,
    suggested_position JSONB NOT NULL,
    actual_position JSONB NOT NULL,
    similarity_score FLOAT NOT NULL,
    user_accepted BOOLEAN NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_placement_feedback_canvas (canvas_id),
    INDEX idx_placement_feedback_card (card_id),
    INDEX idx_placement_feedback_similarity (similarity_score),
    INDEX idx_placement_feedback_accepted (user_accepted)
);

COMMENT ON TABLE placement_feedback IS 'Tracks user feedback on AI-suggested card placements for learning';
COMMENT ON COLUMN placement_feedback.user_accepted IS 'Whether user accepted AI suggestion without manual adjustment';
COMMENT ON COLUMN placement_feedback.similarity_score IS 'Similarity score between card and suggested parent';
"""
