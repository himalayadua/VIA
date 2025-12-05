"""Category Profile Data Structure.

Lightweight representation of a category for efficient retrieval and LLM reasoning.
"""

import logging
from typing import Dict, List, Optional, Set
from datetime import datetime
from dataclasses import dataclass, field, asdict
import numpy as np
import json

logger = logging.getLogger(__name__)


@dataclass
class CategoryProfile:
    """Lightweight category profile for efficient storage and retrieval.
    
    This is NOT a full card - it's a compact representation optimized for:
    1. Fast retrieval (vector + keyword indexes)
    2. LLM reasoning (compact prompt context)
    3. Profile evolution (updates as cards are added)
    """
    
    # Identity
    id: str
    name: str
    description: str
    
    # Semantic representation
    centroid_embedding: np.ndarray
    keywords: List[str] = field(default_factory=list)
    keyword_scores: Dict[str, float] = field(default_factory=dict)
    
    # Context for LLM (compact!)
    snippets: List[str] = field(default_factory=list)  # Max 3, each 1-2 lines
    
    # Hierarchy
    parent_id: Optional[str] = None
    sibling_ids: List[str] = field(default_factory=list)
    child_ids: List[str] = field(default_factory=list)
    
    # Statistics
    card_count: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    confidence: float = 0.5  # How well-defined this category is
    
    # Learning
    user_corrections: int = 0  # Times user manually changed category
    auto_assignments: int = 0  # Times auto-assigned correctly
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        data = asdict(self)
        # Convert numpy array to list for JSON serialization
        data['centroid_embedding'] = self.centroid_embedding.tolist()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CategoryProfile':
        """Create from dictionary."""
        # Convert list back to numpy array
        if isinstance(data.get('centroid_embedding'), list):
            data['centroid_embedding'] = np.array(data['centroid_embedding'])
        return cls(**data)
    
    def to_compact_dict(self) -> Dict:
        """Convert to compact dict for LLM prompt (minimal info)."""
        return {
            'name': self.name,
            'description': self.description,
            'keywords': self.keywords[:10],  # Top 10 only
            'snippets': self.snippets,
            'card_count': self.card_count,
            'confidence': round(self.confidence, 2)
        }
    
    def update_statistics(self, is_user_correction: bool = False):
        """Update statistics after assignment."""
        self.last_updated = datetime.now().isoformat()
        
        if is_user_correction:
            self.user_corrections += 1
        else:
            self.auto_assignments += 1
        
        # Recalculate confidence
        total = self.user_corrections + self.auto_assignments
        if total > 0:
            self.confidence = self.auto_assignments / total
    
    def __repr__(self) -> str:
        return f"CategoryProfile(id={self.id}, name={self.name}, cards={self.card_count}, confidence={self.confidence:.2f})"


class CategoryProfileStore:
    """Storage and retrieval for category profiles."""
    
    def __init__(self, persist_path: str = "data/category_profiles.json"):
        """Initialize profile store.
        
        Args:
            persist_path: Path to persist profiles
        """
        self.persist_path = persist_path
        self.profiles: Dict[str, CategoryProfile] = {}
        self._load()
        
        logger.info(f"Initialized CategoryProfileStore with {len(self.profiles)} profiles")
    
    def add(self, profile: CategoryProfile) -> None:
        """Add a profile to the store."""
        self.profiles[profile.id] = profile
        logger.debug(f"Added profile: {profile.name}")
    
    def get(self, profile_id: str) -> Optional[CategoryProfile]:
        """Get a profile by ID."""
        return self.profiles.get(profile_id)
    
    def get_by_name(self, name: str) -> Optional[CategoryProfile]:
        """Get a profile by name."""
        for profile in self.profiles.values():
            if profile.name.lower() == name.lower():
                return profile
        return None
    
    def get_all(self) -> List[CategoryProfile]:
        """Get all profiles."""
        return list(self.profiles.values())
    
    def remove(self, profile_id: str) -> None:
        """Remove a profile."""
        if profile_id in self.profiles:
            del self.profiles[profile_id]
            logger.debug(f"Removed profile: {profile_id}")
    
    def update(self, profile: CategoryProfile) -> None:
        """Update an existing profile."""
        self.profiles[profile.id] = profile
        logger.debug(f"Updated profile: {profile.name}")
    
    def save(self) -> None:
        """Persist profiles to disk."""
        import os
        os.makedirs(os.path.dirname(self.persist_path), exist_ok=True)
        
        data = {
            profile_id: profile.to_dict()
            for profile_id, profile in self.profiles.items()
        }
        
        with open(self.persist_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved {len(self.profiles)} profiles to {self.persist_path}")
    
    def _load(self) -> None:
        """Load profiles from disk."""
        import os
        
        if not os.path.exists(self.persist_path):
            logger.info("No existing profiles found, starting fresh")
            return
        
        try:
            with open(self.persist_path, 'r') as f:
                data = json.load(f)
            
            for profile_id, profile_data in data.items():
                self.profiles[profile_id] = CategoryProfile.from_dict(profile_data)
            
            logger.info(f"Loaded {len(self.profiles)} profiles from {self.persist_path}")
        except Exception as e:
            logger.error(f"Error loading profiles: {e}")
    
    def get_statistics(self) -> Dict:
        """Get statistics about profiles."""
        if not self.profiles:
            return {
                'total_profiles': 0,
                'total_cards': 0,
                'avg_confidence': 0.0,
                'avg_cards_per_profile': 0.0
            }
        
        total_cards = sum(p.card_count for p in self.profiles.values())
        avg_confidence = sum(p.confidence for p in self.profiles.values()) / len(self.profiles)
        
        return {
            'total_profiles': len(self.profiles),
            'total_cards': total_cards,
            'avg_confidence': round(avg_confidence, 2),
            'avg_cards_per_profile': round(total_cards / len(self.profiles), 1)
        }
