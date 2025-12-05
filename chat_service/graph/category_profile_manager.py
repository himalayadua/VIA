"""Category Profile Manager - Profile Lifecycle Management.

Manages the complete lifecycle of category profiles:
1. Creation (from LLM suggestions or manual)
2. Updates (as cards are added)
3. Evolution (centroid, keywords, snippets)
4. Merging (similar categories)
5. Splitting (overly broad categories)
"""

import logging
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime
import numpy as np
from collections import Counter
import uuid

from .category_profile import CategoryProfile, CategoryProfileStore
from .category_retriever import CategoryRetriever

logger = logging.getLogger(__name__)


class CategoryProfileManager:
    """Manages category profile lifecycle and evolution."""
    
    def __init__(
        self,
        profile_store: CategoryProfileStore,
        retriever: Optional[CategoryRetriever] = None
    ):
        """Initialize profile manager.
        
        Args:
            profile_store: Category profile storage
            retriever: Category retriever (for index updates)
        """
        self.profile_store = profile_store
        self.retriever = retriever
        
        logger.info("Initialized CategoryProfileManager")
    
    def create_profile(
        self,
        name: str,
        description: str,
        initial_cards: List[Dict],
        parent_id: Optional[str] = None
    ) -> CategoryProfile:
        """Create a new category profile from initial cards.
        
        Args:
            name: Category name
            description: One-sentence description
            initial_cards: List of card dicts with content, embedding, keywords
            parent_id: Optional parent category ID
            
        Returns:
            Created CategoryProfile
        """
        logger.info(f"Creating new category profile: {name}")
        
        # Generate unique ID
        profile_id = f"cat_{uuid.uuid4().hex[:8]}"
        
        # Calculate centroid embedding from initial cards
        embeddings = [card['embedding'] for card in initial_cards if 'embedding' in card]
        if embeddings:
            centroid_embedding = np.mean(embeddings, axis=0)
        else:
            # Fallback: zero vector
            centroid_embedding = np.zeros(768)  # Assuming 768-dim embeddings
        
        # Extract keywords from initial cards
        keywords, keyword_scores = self._extract_keywords_from_cards(initial_cards)
        
        # Select representative snippets
        snippets = self._select_representative_snippets(initial_cards, max_snippets=3)
        
        # Create profile
        profile = CategoryProfile(
            id=profile_id,
            name=name,
            description=description,
            centroid_embedding=centroid_embedding,
            keywords=keywords,
            keyword_scores=keyword_scores,
            snippets=snippets,
            parent_id=parent_id,
            card_count=len(initial_cards),
            confidence=0.5  # Start with medium confidence
        )
        
        # Add to store
        self.profile_store.add(profile)
        
        # Add to retriever indexes
        if self.retriever:
            self.retriever.add_profile(profile)
        
        # Save
        self.profile_store.save()
        
        logger.info(f"Created profile {profile_id}: {name} with {len(initial_cards)} cards")
        
        return profile
    
    def update_profile_with_card(
        self,
        profile_id: str,
        card: Dict,
        is_user_correction: bool = False
    ) -> CategoryProfile:
        """Update profile when a new card is assigned to it.
        
        Args:
            profile_id: Profile to update
            card: Card dict with content, embedding, keywords
            is_user_correction: Whether this was a user correction
            
        Returns:
            Updated CategoryProfile
        """
        profile = self.profile_store.get(profile_id)
        if not profile:
            raise ValueError(f"Profile {profile_id} not found")
        
        logger.debug(f"Updating profile {profile.name} with new card")
        
        # Update centroid embedding (running average)
        if 'embedding' in card:
            profile.centroid_embedding = self._update_centroid(
                profile.centroid_embedding,
                card['embedding'],
                profile.card_count
            )
        
        # Update card count
        profile.card_count += 1
        
        # Update statistics
        profile.update_statistics(is_user_correction=is_user_correction)
        
        # Periodically update keywords and snippets (every 10 cards)
        if profile.card_count % 10 == 0:
            self._refresh_profile_content(profile)
        
        # Update in store
        self.profile_store.update(profile)
        
        # Update in retriever indexes
        if self.retriever:
            self.retriever.update_profile(profile)
        
        # Save periodically
        if profile.card_count % 5 == 0:
            self.profile_store.save()
        
        return profile
    
    def _update_centroid(
        self,
        current_centroid: np.ndarray,
        new_embedding: np.ndarray,
        current_count: int
    ) -> np.ndarray:
        """Update centroid embedding with running average.
        
        Args:
            current_centroid: Current centroid vector
            new_embedding: New card embedding
            current_count: Current number of cards
            
        Returns:
            Updated centroid
        """
        # Running average formula: new_avg = (old_avg * n + new_value) / (n + 1)
        return (current_centroid * current_count + new_embedding) / (current_count + 1)
    
    def _extract_keywords_from_cards(
        self,
        cards: List[Dict],
        top_k: int = 20
    ) -> Tuple[List[str], Dict[str, float]]:
        """Extract top keywords from cards using TF-IDF-like scoring.
        
        Args:
            cards: List of card dicts
            top_k: Number of top keywords to extract
            
        Returns:
            (keywords_list, keyword_scores_dict)
        """
        # Collect all keywords from cards
        all_keywords = []
        for card in cards:
            if 'keywords' in card:
                all_keywords.extend(card['keywords'])
        
        if not all_keywords:
            return [], {}
        
        # Count frequencies
        keyword_counts = Counter(all_keywords)
        
        # Calculate scores (simple frequency-based for now)
        total_keywords = len(all_keywords)
        keyword_scores = {
            keyword: count / total_keywords
            for keyword, count in keyword_counts.items()
        }
        
        # Get top-K
        top_keywords = sorted(
            keyword_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_k]
        
        keywords_list = [kw for kw, _ in top_keywords]
        scores_dict = dict(top_keywords)
        
        return keywords_list, scores_dict
    
    def _select_representative_snippets(
        self,
        cards: List[Dict],
        max_snippets: int = 3
    ) -> List[str]:
        """Select most representative snippets from cards.
        
        Args:
            cards: List of card dicts
            max_snippets: Maximum number of snippets
            
        Returns:
            List of snippet strings
        """
        snippets = []
        
        for card in cards[:max_snippets]:
            content = card.get('content', '')
            
            # Extract first 1-2 sentences (up to 150 chars)
            sentences = content.split('.')
            snippet = sentences[0][:150]
            
            if snippet:
                snippets.append(snippet.strip())
        
        return snippets
    
    def _refresh_profile_content(self, profile: CategoryProfile) -> None:
        """Refresh keywords and snippets from all cards in category.
        
        This is called periodically to keep profile content up-to-date.
        
        Args:
            profile: Profile to refresh
        """
        # TODO: Fetch all cards in this category from knowledge graph
        # For now, we'll skip this as it requires integration with KG state
        logger.debug(f"Refreshing profile content for {profile.name}")
        pass
    
    def merge_profiles(
        self,
        profile_id_1: str,
        profile_id_2: str,
        new_name: Optional[str] = None
    ) -> CategoryProfile:
        """Merge two similar categories into one.
        
        Args:
            profile_id_1: First profile ID
            profile_id_2: Second profile ID
            new_name: Optional new name (defaults to first profile's name)
            
        Returns:
            Merged CategoryProfile
        """
        profile1 = self.profile_store.get(profile_id_1)
        profile2 = self.profile_store.get(profile_id_2)
        
        if not profile1 or not profile2:
            raise ValueError("One or both profiles not found")
        
        logger.info(f"Merging profiles: {profile1.name} + {profile2.name}")
        
        # Merge embeddings (weighted average by card count)
        total_cards = profile1.card_count + profile2.card_count
        merged_embedding = (
            profile1.centroid_embedding * profile1.card_count +
            profile2.centroid_embedding * profile2.card_count
        ) / total_cards
        
        # Merge keywords
        merged_keywords = list(set(profile1.keywords + profile2.keywords))[:20]
        merged_keyword_scores = {**profile1.keyword_scores, **profile2.keyword_scores}
        
        # Merge snippets
        merged_snippets = (profile1.snippets + profile2.snippets)[:3]
        
        # Create merged profile
        merged_profile = CategoryProfile(
            id=profile1.id,  # Keep first profile's ID
            name=new_name or profile1.name,
            description=profile1.description,  # Keep first profile's description
            centroid_embedding=merged_embedding,
            keywords=merged_keywords,
            keyword_scores=merged_keyword_scores,
            snippets=merged_snippets,
            parent_id=profile1.parent_id,
            card_count=total_cards,
            confidence=(profile1.confidence + profile2.confidence) / 2,
            user_corrections=profile1.user_corrections + profile2.user_corrections,
            auto_assignments=profile1.auto_assignments + profile2.auto_assignments
        )
        
        # Update store
        self.profile_store.update(merged_profile)
        self.profile_store.remove(profile_id_2)
        
        # Update retriever
        if self.retriever:
            self.retriever.update_profile(merged_profile)
            self.retriever.remove_profile(profile_id_2)
        
        # Save
        self.profile_store.save()
        
        logger.info(f"Merged into profile {merged_profile.id}: {merged_profile.name}")
        
        return merged_profile
    
    def split_profile(
        self,
        profile_id: str,
        split_criteria: Dict
    ) -> List[CategoryProfile]:
        """Split an overly broad category into subcategories.
        
        Args:
            profile_id: Profile to split
            split_criteria: Criteria for splitting (e.g., keyword clusters)
            
        Returns:
            List of new CategoryProfiles
        """
        # TODO: Implement category splitting
        # This is complex and requires clustering cards within the category
        logger.warning("Category splitting not yet implemented")
        return []
    
    def delete_profile(self, profile_id: str) -> None:
        """Delete a category profile.
        
        Args:
            profile_id: Profile to delete
        """
        logger.info(f"Deleting profile {profile_id}")
        
        # Remove from retriever
        if self.retriever:
            self.retriever.remove_profile(profile_id)
        
        # Remove from store
        self.profile_store.remove(profile_id)
        
        # Save
        self.profile_store.save()
    
    def get_profile_statistics(self, profile_id: str) -> Dict:
        """Get statistics for a profile.
        
        Args:
            profile_id: Profile ID
            
        Returns:
            Statistics dictionary
        """
        profile = self.profile_store.get(profile_id)
        if not profile:
            return {}
        
        return {
            'name': profile.name,
            'card_count': profile.card_count,
            'confidence': profile.confidence,
            'user_corrections': profile.user_corrections,
            'auto_assignments': profile.auto_assignments,
            'accuracy': profile.confidence,
            'created_at': profile.created_at,
            'last_updated': profile.last_updated
        }
