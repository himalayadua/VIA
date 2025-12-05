"""Dynamic Category System - Main Interface.

Replaces the hardcoded CategoryTaxonomy with a dynamic, LLM-driven system.
Integrates CategoryRetriever, CategoryClassifier, and CategoryProfileManager.
"""

import logging
from typing import Dict, List, Optional, Tuple
import numpy as np

from .category_profile import CategoryProfile, CategoryProfileStore
from .category_retriever import CategoryRetriever
from .category_classifier import CategoryClassifier
from .category_profile_manager import CategoryProfileManager
from .embedding_provider import get_embedding_provider
from .llm_provider import get_llm_provider

logger = logging.getLogger(__name__)


class DynamicCategorySystem:
    """Main interface for dynamic category management.
    
    Replaces CategoryTaxonomy with a system that:
    1. Learns categories from user's content
    2. Uses two-stage retrieval (fast + LLM)
    3. Evolves profiles as cards are added
    4. Adapts to any domain
    """
    
    def __init__(
        self,
        persist_path: str = "data/category_profiles.json",
        model=None,
        enable_llm: bool = True
    ):
        """Initialize dynamic category system.
        
        Args:
            persist_path: Path to persist category profiles
            model: LLM model for classification (optional, will use default if None)
            enable_llm: Whether to use LLM (can disable for testing)
        """
        # Initialize providers
        self.embedding_provider = get_embedding_provider()
        self.llm_provider = model if model else (get_llm_provider() if enable_llm else None)
        
        # Initialize components
        self.profile_store = CategoryProfileStore(persist_path=persist_path)
        self.retriever = CategoryRetriever(self.profile_store)
        self.classifier = CategoryClassifier(
            self.profile_store,
            self.retriever,
            model=self.llm_provider
        )
        self.profile_manager = CategoryProfileManager(
            self.profile_store,
            self.retriever
        )
        
        self.enable_llm = enable_llm
        
        # Initialize with seed categories if empty
        if len(self.profile_store.profiles) == 0:
            self._initialize_with_seeds()
        
        logger.info(f"Initialized DynamicCategorySystem with {len(self.profile_store.profiles)} profiles")
    
    def suggest_category(
        self,
        content: str,
        title: str = "",
        embedding: Optional[np.ndarray] = None,
        keywords: Optional[List[str]] = None
    ) -> str:
        """Suggest category for a card.
        
        This is the main entry point, compatible with old CategoryTaxonomy API.
        
        Args:
            content: Card content
            title: Card title
            embedding: Pre-computed embedding (optional)
            keywords: Pre-extracted keywords (optional)
            
        Returns:
            Category name
        """
        # Extract keywords if not provided
        if keywords is None:
            keywords = self._extract_keywords(content, title)
        
        # Generate embedding if not provided
        if embedding is None:
            embedding = self._generate_embedding(content)
        
        # Classify using two-stage system
        result = self.classifier.classify(
            card_content=content,
            card_title=title,
            card_embedding=embedding,
            card_keywords=keywords,
            top_k_candidates=10
        )
        
        # Handle result
        if result['action'] == 'match':
            category_name = result['category_name']
            logger.info(f"Matched to category: {category_name} (confidence: {result['confidence']:.2f})")
            return category_name
        
        elif result['action'] == 'create_new':
            # Create new category
            new_cat = result['new_category']
            profile = self.profile_manager.create_profile(
                name=new_cat['name'],
                description=new_cat['description'],
                initial_cards=[{
                    'content': content,
                    'title': title,
                    'embedding': embedding,
                    'keywords': keywords
                }],
                parent_id=new_cat.get('parent_id')
            )
            logger.info(f"Created new category: {profile.name}")
            return profile.name
        
        else:  # uncategorized
            logger.info("No suitable category found, returning Uncategorized")
            return "Uncategorized"
    
    def add_card(self, card_id: str, category: str) -> None:
        """Add a card to a category.
        
        Compatible with old CategoryTaxonomy API.
        
        Args:
            card_id: Card identifier
            category: Category name
        """
        # Find profile by name
        profile = self.profile_store.get_by_name(category)
        
        if not profile:
            logger.warning(f"Category '{category}' not found, skipping add_card")
            return
        
        # Note: We don't have the full card data here, so we can't update the profile
        # This would need to be called from a higher level with full card data
        logger.debug(f"Added card {card_id} to category {category}")
    
    def update_card_category(
        self,
        card_id: str,
        new_category: str,
        card_data: Optional[Dict] = None,
        is_user_correction: bool = False
    ) -> None:
        """Update a card's category.
        
        Args:
            card_id: Card identifier
            new_category: New category name
            card_data: Full card data (content, embedding, keywords)
            is_user_correction: Whether this was a user correction
        """
        profile = self.profile_store.get_by_name(new_category)
        
        if not profile:
            logger.warning(f"Category '{new_category}' not found")
            return
        
        # Update profile with card if we have the data
        if card_data:
            self.profile_manager.update_profile_with_card(
                profile_id=profile.id,
                card=card_data,
                is_user_correction=is_user_correction
            )
        
        logger.debug(f"Updated card {card_id} to category {new_category}")
    
    def get_all_categories(self) -> List[str]:
        """Get all category names.
        
        Compatible with old CategoryTaxonomy API.
        
        Returns:
            List of category names
        """
        return [profile.name for profile in self.profile_store.get_all()]
    
    def get_cards_in_category(self, category: str) -> List[str]:
        """Get all cards in a category.
        
        Note: This requires integration with KnowledgeGraphState.
        For now, returns empty list.
        
        Args:
            category: Category name
            
        Returns:
            List of card IDs
        """
        # TODO: Integrate with KnowledgeGraphState to get actual cards
        return []
    
    def get_statistics(self) -> Dict:
        """Get system statistics.
        
        Returns:
            Statistics dictionary
        """
        profile_stats = self.profile_store.get_statistics()
        retriever_stats = self.retriever.get_statistics()
        
        return {
            **profile_stats,
            **retriever_stats,
            'llm_enabled': self.enable_llm
        }
    
    def _initialize_with_seeds(self) -> None:
        """Initialize with seed categories.
        
        Creates a small set of general-purpose seed categories
        to bootstrap the system.
        """
        logger.info("Initializing with seed categories")
        
        seeds = [
            {
                "name": "Programming",
                "description": "Software development, coding, and programming languages",
                "keywords": ["code", "programming", "software", "function", "class", "method"],
            },
            {
                "name": "Documentation",
                "description": "Technical documentation, guides, and references",
                "keywords": ["documentation", "guide", "reference", "tutorial", "how-to"],
            },
            {
                "name": "Research",
                "description": "Academic research, papers, and studies",
                "keywords": ["research", "study", "paper", "academic", "experiment"],
            },
        ]
        
        for seed in seeds:
            # Create profile with zero embedding (will be updated as cards are added)
            profile = CategoryProfile(
                id=f"cat_seed_{seed['name'].lower()}",
                name=seed['name'],
                description=seed['description'],
                centroid_embedding=np.zeros(768),  # Placeholder
                keywords=seed['keywords'],
                keyword_scores={kw: 1.0 for kw in seed['keywords']},
                snippets=[],
                card_count=0,
                confidence=0.3  # Low confidence for seeds
            )
            
            self.profile_store.add(profile)
            self.retriever.add_profile(profile)
        
        self.profile_store.save()
        
        logger.info(f"Created {len(seeds)} seed categories")
    
    def _extract_keywords(self, content: str, title: str) -> List[str]:
        """Extract keywords from content.
        
        Args:
            content: Card content
            title: Card title
            
        Returns:
            List of keywords
        """
        # Simple keyword extraction (can be improved with NLP)
        text = f"{title} {content}".lower()
        
        # Remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        
        # Split and filter
        words = text.split()
        keywords = [w for w in words if len(w) > 3 and w not in stop_words]
        
        # Return unique keywords (up to 20)
        return list(dict.fromkeys(keywords))[:20]
    
    def _generate_embedding(self, content: str) -> np.ndarray:
        """Generate embedding for content using NVIDIA API.
        
        Args:
            content: Text content
            
        Returns:
            Embedding vector
        """
        return self.embedding_provider.get_embedding(content)
    
    def save(self) -> None:
        """Save all profiles to disk."""
        self.profile_store.save()
    
    def clear(self) -> None:
        """Clear all profiles (for testing)."""
        self.profile_store.profiles.clear()
        self.retriever = CategoryRetriever(self.profile_store)
        logger.warning("Cleared all category profiles")
