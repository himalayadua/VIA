"""Knowledge Graph Management System.

Provides persistent, fast, and self-correcting knowledge graph operations.
"""

from .knowledge_graph_state import KnowledgeGraphState
from .category_taxonomy import CategoryTaxonomy  # Legacy (deprecated)
from .dynamic_category_system import DynamicCategorySystem  # New dynamic system
from .graph_sync import GraphSyncService
from .self_correction_job import SelfCorrectionJob
from .card_placer import CardPlacer
from .connection_manager import ConnectionManager
from .content_merger import ContentMerger
from .placement_feedback import PlacementFeedback

# Category system components (for advanced usage)
from .category_profile import CategoryProfile, CategoryProfileStore
from .category_retriever import CategoryRetriever
from .category_classifier import CategoryClassifier
from .category_profile_manager import CategoryProfileManager

__all__ = [
    'KnowledgeGraphState',
    'CategoryTaxonomy',  # Legacy
    'DynamicCategorySystem',  # New
    'GraphSyncService',
    'SelfCorrectionJob',
    'CardPlacer',
    'ConnectionManager',
    'ContentMerger',
    'PlacementFeedback',
    # Category system components
    'CategoryProfile',
    'CategoryProfileStore',
    'CategoryRetriever',
    'CategoryClassifier',
    'CategoryProfileManager',
]
