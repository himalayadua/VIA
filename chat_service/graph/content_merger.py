"""
Content Merger

Intelligently merges content from multiple sources to avoid duplicates
and maintain source attribution.
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class ContentMerger:
    """
    Merges content from multiple sources intelligently.
    
    Handles:
    - Detecting overlapping content
    - Merging related information
    - Maintaining source attribution
    - Detecting conflicts
    """
    
    # Thresholds for merging decisions
    DUPLICATE_THRESHOLD = 0.9  # >90% similar = duplicate
    MERGE_THRESHOLD = 0.7      # >70% similar = merge
    CONFLICT_THRESHOLD = 0.6   # >60% similar but different = conflict
    
    def __init__(self):
        """Initialize content merger."""
        logger.info("ContentMerger initialized")
    
    def detect_overlapping_content(
        self,
        new_content: Dict,
        existing_cards: List[Dict],
        canvas_id: str
    ) -> Dict:
        """
        Detect if new content overlaps with existing cards.
        
        Args:
            new_content: New content to check (title, description, sections)
            existing_cards: List of existing cards on canvas
            canvas_id: Canvas ID
            
        Returns:
            {
                "has_overlap": bool,
                "overlapping_cards": list[dict],  # [{card_id, similarity, overlap_type}]
                "merge_candidates": list[str],    # Card IDs to merge
                "conflict_candidates": list[str]  # Card IDs with conflicts
            }
        """
        logger.info(f"Detecting overlapping content on canvas {canvas_id}")
        
        overlapping_cards = []
        merge_candidates = []
        conflict_candidates = []
        
        # Compare new content title and description against existing cards
        new_title = new_content.get("title", "")
        new_description = new_content.get("description", "")
        new_text = f"{new_title} {new_description}"
        
        for card in existing_cards:
            card_title = card.get("title", "")
            card_content = card.get("content", "")
            card_text = f"{card_title} {card_content}"
            
            # Calculate similarity
            similarity = self._calculate_similarity(new_text, card_text)
            
            if similarity > self.CONFLICT_THRESHOLD:
                overlap_info = {
                    "card_id": card["id"],
                    "card_title": card_title,
                    "similarity": similarity,
                    "overlap_type": self._determine_overlap_type(similarity)
                }
                overlapping_cards.append(overlap_info)
                
                # Categorize based on similarity
                if similarity >= self.DUPLICATE_THRESHOLD:
                    merge_candidates.append(card["id"])
                elif similarity >= self.MERGE_THRESHOLD:
                    merge_candidates.append(card["id"])
                elif similarity >= self.CONFLICT_THRESHOLD:
                    # Check if content actually conflicts
                    if self._has_conflicting_info(new_text, card_text):
                        conflict_candidates.append(card["id"])
        
        has_overlap = len(overlapping_cards) > 0
        
        logger.info(f"Found {len(overlapping_cards)} overlapping cards: "
                   f"{len(merge_candidates)} merge candidates, "
                   f"{len(conflict_candidates)} conflicts")
        
        return {
            "has_overlap": has_overlap,
            "overlapping_cards": overlapping_cards,
            "merge_candidates": merge_candidates,
            "conflict_candidates": conflict_candidates
        }
    
    def merge_content(
        self,
        existing_card: Dict,
        new_content: Dict,
        source_info: Dict
    ) -> Dict:
        """
        Merge new content into existing card.
        
        Args:
            existing_card: Existing card to merge into
            new_content: New content to merge
            source_info: Source information for attribution
            
        Returns:
            {
                "merged_content": str,
                "merged_title": str,
                "sources": list[dict],
                "merge_summary": str
            }
        """
        logger.info(f"Merging content into card {existing_card.get('id')}")
        
        # Get existing content
        existing_title = existing_card.get("title", "")
        existing_content = existing_card.get("content", "")
        existing_sources = existing_card.get("sources", [])
        
        # Get new content
        new_title = new_content.get("title", "")
        new_description = new_content.get("description", "")
        
        # Merge titles (keep existing if similar, otherwise combine)
        title_similarity = self._calculate_similarity(existing_title, new_title)
        if title_similarity > 0.8:
            merged_title = existing_title  # Keep existing
        else:
            merged_title = f"{existing_title} / {new_title}"
        
        # Merge content intelligently
        merged_content = self._merge_text_content(
            existing_content,
            new_description,
            existing_sources,
            source_info
        )
        
        # Update sources list
        new_source_entry = {
            "url": source_info.get("url", ""),
            "type": source_info.get("type", "url"),
            "extracted_at": source_info.get("extracted_at", datetime.now().isoformat()),
            "contribution": self._calculate_contribution(existing_content, new_description)
        }
        
        merged_sources = existing_sources + [new_source_entry]
        
        # Recalculate contribution percentages
        merged_sources = self._recalculate_contributions(merged_sources)
        
        merge_summary = f"Merged content from {source_info.get('url', 'new source')}"
        
        return {
            "merged_content": merged_content,
            "merged_title": merged_title,
            "sources": merged_sources,
            "merge_summary": merge_summary
        }
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two texts using TF-IDF.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        if not text1 or not text2:
            return 0.0
        
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            
            vectorizer = TfidfVectorizer()
            tfidf_matrix = vectorizer.fit_transform([text1, text2])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            return float(similarity)
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            # Fallback to simple word overlap
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())
            if not words1 or not words2:
                return 0.0
            overlap = len(words1 & words2)
            total = len(words1 | words2)
            return overlap / total if total > 0 else 0.0
    
    def _determine_overlap_type(self, similarity: float) -> str:
        """
        Determine type of overlap based on similarity score.
        
        Args:
            similarity: Similarity score
            
        Returns:
            Overlap type: "duplicate", "merge", or "conflict"
        """
        if similarity >= self.DUPLICATE_THRESHOLD:
            return "duplicate"
        elif similarity >= self.MERGE_THRESHOLD:
            return "merge"
        else:
            return "conflict"
    
    def _has_conflicting_info(self, text1: str, text2: str) -> bool:
        """
        Check if two texts have conflicting information.
        
        Looks for contradictory statements like:
        - "X is the most..." vs "Y is the most..."
        - "X is better than Y" vs "Y is better than X"
        - Different numerical values for same metric
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            True if conflict detected
        """
        # Simple heuristic: if texts are similar but have different key terms
        # This is a simplified version - could be enhanced with NLP
        
        # Look for superlatives and comparatives
        superlatives = ["most", "best", "worst", "fastest", "slowest", "largest", "smallest"]
        comparatives = ["better", "worse", "faster", "slower", "more", "less"]
        
        text1_lower = text1.lower()
        text2_lower = text2.lower()
        
        # Check if both texts use superlatives/comparatives
        has_superlative_1 = any(word in text1_lower for word in superlatives)
        has_superlative_2 = any(word in text2_lower for word in superlatives)
        
        has_comparative_1 = any(word in text1_lower for word in comparatives)
        has_comparative_2 = any(word in text2_lower for word in comparatives)
        
        # If both have superlatives/comparatives, likely conflicting
        if (has_superlative_1 and has_superlative_2) or (has_comparative_1 and has_comparative_2):
            return True
        
        return False
    
    def _merge_text_content(
        self,
        existing_content: str,
        new_content: str,
        existing_sources: List[Dict],
        new_source: Dict
    ) -> str:
        """
        Intelligently merge text content from two sources.
        
        Args:
            existing_content: Existing card content
            new_content: New content to merge
            existing_sources: Existing source list
            new_source: New source info
            
        Returns:
            Merged content string
        """
        # If existing content is empty, just use new content
        if not existing_content:
            return new_content
        
        # If new content is empty, keep existing
        if not new_content:
            return existing_content
        
        # Check similarity
        similarity = self._calculate_similarity(existing_content, new_content)
        
        if similarity > 0.9:
            # Very similar - keep existing, maybe add note
            return existing_content
        elif similarity > 0.7:
            # Similar but complementary - combine
            return f"{existing_content}\n\n**Additional information from {new_source.get('url', 'another source')}:**\n{new_content}"
        else:
            # Different enough - add as separate section
            return f"{existing_content}\n\n---\n\n**From {new_source.get('url', 'another source')}:**\n{new_content}"
    
    def _calculate_contribution(self, existing_content: str, new_content: str) -> str:
        """
        Calculate contribution percentage of new content.
        
        Args:
            existing_content: Existing content
            new_content: New content
            
        Returns:
            Contribution percentage as string (e.g., "40%")
        """
        if not existing_content:
            return "100%"
        
        existing_len = len(existing_content)
        new_len = len(new_content)
        total_len = existing_len + new_len
        
        if total_len == 0:
            return "0%"
        
        contribution = (new_len / total_len) * 100
        return f"{int(contribution)}%"
    
    def _recalculate_contributions(self, sources: List[Dict]) -> List[Dict]:
        """
        Recalculate contribution percentages for all sources.
        
        Args:
            sources: List of source dictionaries
            
        Returns:
            Updated sources list with recalculated contributions
        """
        if not sources:
            return []
        
        # Simple equal distribution for now
        # Could be enhanced to track actual content length from each source
        contribution_each = 100 / len(sources)
        
        for source in sources:
            source["contribution"] = f"{int(contribution_each)}%"
        
        return sources
    
    def create_conflict_marker(
        self,
        card1_id: str,
        card2_id: str,
        conflict_type: str,
        description: str
    ) -> Dict:
        """
        Create a conflict marker for two cards.
        
        Args:
            card1_id: First card ID
            card2_id: Second card ID
            conflict_type: Type of conflict
            description: Description of the conflict
            
        Returns:
            Conflict marker dictionary
        """
        return {
            "card_ids": [card1_id, card2_id],
            "conflict_type": conflict_type,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "resolved": False
        }
    
    def get_merge_preview(
        self,
        card1: Dict,
        card2: Dict
    ) -> Dict:
        """
        Generate a preview of what merged content would look like.
        
        Args:
            card1: First card
            card2: Second card
            
        Returns:
            Preview dictionary with merged content
        """
        # Create temporary source info for card2
        source_info = {
            "url": card2.get("source_url", "unknown"),
            "type": card2.get("source_type", "url"),
            "extracted_at": card2.get("extracted_at", datetime.now().isoformat())
        }
        
        # Create temporary new content from card2
        new_content = {
            "title": card2.get("title", ""),
            "description": card2.get("content", "")
        }
        
        # Generate merge
        merged = self.merge_content(card1, new_content, source_info)
        
        return {
            "preview_title": merged["merged_title"],
            "preview_content": merged["merged_content"],
            "sources": merged["sources"],
            "original_card1": {
                "title": card1.get("title"),
                "content": card1.get("content")
            },
            "original_card2": {
                "title": card2.get("title"),
                "content": card2.get("content")
            }
        }
