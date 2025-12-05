"""Graph Sync Service.

Syncs PostgreSQL changes to Knowledge Graph State.
Listens to canvas events and keeps the graph up-to-date.
"""

import logging
from typing import Dict, Any

from .knowledge_graph_state import KnowledgeGraphState
from .dynamic_category_system import DynamicCategorySystem
from .llm_provider import get_llm_provider

logger = logging.getLogger(__name__)


class GraphSyncService:
    """Syncs PostgreSQL changes to Knowledge Graph State.
    
    Listens to:
    - card_created events
    - card_updated events
    - card_deleted events
    - connection_created events
    """
    
    def __init__(self, kg_state: KnowledgeGraphState, enable_llm: bool = True):
        """Initialize graph sync service.
        
        Args:
            kg_state: Knowledge graph state instance
            enable_llm: Whether to enable LLM for category classification
        """
        self.kg_state = kg_state
        
        # Initialize dynamic category system
        try:
            self.category_system = DynamicCategorySystem(
                persist_path="data/category_profiles.json",
                model=get_llm_provider() if enable_llm else None,
                enable_llm=enable_llm
            )
            logger.info("Initialized GraphSyncService with DynamicCategorySystem")
        except Exception as e:
            logger.error(f"Failed to initialize DynamicCategorySystem: {e}")
            # Fallback to basic categorization
            self.category_system = None
            logger.warning("Using fallback categorization")
    
    def setup_event_listeners(self, event_emitter) -> None:
        """Set up event listeners for canvas events.
        
        Args:
            event_emitter: Event emitter instance from events.py
        """
        event_emitter.on('card_created', self.on_card_created)
        event_emitter.on('card_updated', self.on_card_updated)
        event_emitter.on('card_deleted', self.on_card_deleted)
        event_emitter.on('connection_created', self.on_connection_created)
        
        logger.info("Set up event listeners for graph sync")
    
    def on_card_created(self, event: Dict[str, Any]) -> None:
        """Handle card_created event.
        
        Args:
            event: Event data with card_id, content, title, metadata
        """
        try:
            card_id = event.get('card_id')
            content = event.get('content', '')
            title = event.get('title', '')
            metadata = event.get('metadata', {})
            
            logger.info(f"Syncing new card {card_id} to knowledge graph")
            
            # Add to knowledge graph
            result = self.kg_state.add_card(
                card_id=card_id,
                content=content,
                title=title,
                metadata=metadata
            )
            
            # Auto-categorize using dynamic system
            if self.category_system:
                try:
                    category = self.category_system.suggest_category(content, title)
                    
                    # Update card with category in graph
                    self.kg_state.backend.update_node(card_id, category=category)
                    
                    # Update category system with card data
                    card_data = {
                        'content': content,
                        'title': title,
                        'embedding': self.category_system.embedding_provider.get_embedding(content),
                        'keywords': self.category_system._extract_keywords(content, title)
                    }
                    
                    self.category_system.update_card_category(
                        card_id=card_id,
                        new_category=category,
                        card_data=card_data,
                        is_user_correction=False
                    )
                    
                except Exception as e:
                    logger.error(f"Error in dynamic categorization: {e}")
                    category = "Uncategorized"
                    self.kg_state.backend.update_node(card_id, category=category)
            else:
                # Fallback categorization
                category = "Uncategorized"
                self.kg_state.backend.update_node(card_id, category=category)
            
            logger.info(f"Synced card {card_id}: parent={result.get('parent_id')}, "
                       f"category={category}, similar={len(result.get('similar_cards', []))}")
            
            # If parent suggested, emit event to create connection in PostgreSQL
            if result.get('parent_id'):
                self._suggest_connection(card_id, result['parent_id'], 'parent-child')
            
        except Exception as e:
            logger.error(f"Error syncing card_created event: {e}", exc_info=True)
    
    def on_card_updated(self, event: Dict[str, Any]) -> None:
        """Handle card_updated event.
        
        Args:
            event: Event data with card_id, new_content, new_title
        """
        try:
            card_id = event.get('card_id')
            new_content = event.get('new_content')
            new_title = event.get('new_title')
            metadata = event.get('metadata', {})
            
            logger.info(f"Syncing updated card {card_id} to knowledge graph")
            
            # Update in knowledge graph
            result = self.kg_state.update_card(
                card_id=card_id,
                content=new_content,
                title=new_title,
                metadata=metadata
            )
            
            # Re-categorize if content changed significantly
            if new_content and self.category_system:
                try:
                    current_node = self.kg_state.backend.get_node(card_id)
                    old_category = current_node.get('category') if current_node else None
                    
                    new_category = self.category_system.suggest_category(
                        new_content, 
                        new_title or ""
                    )
                    
                    if new_category != old_category:
                        self.kg_state.backend.update_node(card_id, category=new_category)
                        
                        # Update category system with new card data
                        card_data = {
                            'content': new_content,
                            'title': new_title or "",
                            'embedding': self.category_system.embedding_provider.get_embedding(new_content),
                            'keywords': self.category_system._extract_keywords(new_content, new_title or "")
                        }
                        
                        self.category_system.update_card_category(
                            card_id=card_id,
                            new_category=new_category,
                            card_data=card_data,
                            is_user_correction=False
                        )
                        
                        logger.info(f"Updated card {card_id} category: {old_category} → {new_category}")
                        
                except Exception as e:
                    logger.error(f"Error in re-categorization: {e}")
            
            logger.info(f"Synced card update {card_id}")
            
        except Exception as e:
            logger.error(f"Error syncing card_updated event: {e}", exc_info=True)
    
    def on_card_deleted(self, event: Dict[str, Any]) -> None:
        """Handle card_deleted event.
        
        Args:
            event: Event data with card_id
        """
        try:
            card_id = event.get('card_id')
            
            logger.info(f"Removing card {card_id} from knowledge graph")
            
            # Remove from category system (if available)
            if self.category_system:
                try:
                    # Note: DynamicCategorySystem doesn't track individual cards
                    # This is handled at the profile level
                    pass
                except Exception as e:
                    logger.error(f"Error removing card from category system: {e}")
            
            # Remove from knowledge graph
            self.kg_state.remove_card(card_id)
            
            logger.info(f"Removed card {card_id} from knowledge graph")
            
        except Exception as e:
            logger.error(f"Error syncing card_deleted event: {e}", exc_info=True)
    
    def on_connection_created(self, event: Dict[str, Any]) -> None:
        """Handle connection_created event.
        
        Args:
            event: Event data with source_id, target_id, connection_type
        """
        try:
            source_id = event.get('source_id')
            target_id = event.get('target_id')
            connection_type = event.get('connection_type', 'related')
            
            logger.info(f"Syncing connection {source_id} → {target_id} to knowledge graph")
            
            # Calculate similarity if not provided
            similarity = event.get('similarity_score')
            if similarity is None:
                similarity = self.kg_state.backend.calculate_similarity(source_id, target_id)
            
            # Add edge to knowledge graph
            self.kg_state.backend.add_edge(
                source_id=source_id,
                target_id=target_id,
                edge_type=connection_type,
                similarity_score=similarity
            )
            
            logger.info(f"Synced connection {source_id} → {target_id}")
            
        except Exception as e:
            logger.error(f"Error syncing connection_created event: {e}", exc_info=True)
    
    def sync_existing_cards(self, cards: list) -> None:
        """Sync existing cards from PostgreSQL to knowledge graph.
        
        Used for initial sync or rebuilding the graph.
        
        Args:
            cards: List of card dicts with id, content, title, metadata
        """
        logger.info(f"Syncing {len(cards)} existing cards to knowledge graph")
        
        for card in cards:
            try:
                self.on_card_created({
                    'card_id': card.get('id'),
                    'content': card.get('content', ''),
                    'title': card.get('title', ''),
                    'metadata': {
                        'card_type': card.get('card_type'),
                        'canvas_id': card.get('canvas_id'),
                    }
                })
            except Exception as e:
                logger.error(f"Error syncing card {card.get('id')}: {e}")
                continue
        
        # Save after bulk sync
        self.kg_state.save()
        
        logger.info(f"Completed syncing {len(cards)} cards")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get sync service statistics.
        
        Returns:
            Dictionary with statistics
        """
        kg_stats = self.kg_state.get_statistics()
        
        # Get category system stats
        category_stats = {}
        if self.category_system:
            try:
                category_stats = self.category_system.get_statistics()
            except Exception as e:
                logger.error(f"Error getting category stats: {e}")
                category_stats = {'error': str(e)}
        
        return {
            'knowledge_graph': kg_stats,
            'category_system': category_stats
        }
    
    def _suggest_connection(self, source_id: str, target_id: str, connection_type: str) -> None:
        """Suggest a connection to be created in PostgreSQL.
        
        This would emit an event or call an API to create the connection.
        For now, just log the suggestion.
        
        Args:
            source_id: Source card ID
            target_id: Target card ID
            connection_type: Type of connection
        """
        logger.info(f"Suggesting {connection_type} connection: {source_id} → {target_id}")
        # TODO: Emit event or call API to create connection in PostgreSQL
