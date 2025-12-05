"""Knowledge Graph State Management System.

Provides persistent, fast, and self-correcting knowledge graph operations.
Maintains semantic embeddings, similarities, and category taxonomy.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from .backends.factory import create_graph_backend
from .backends.base import GraphBackend

logger = logging.getLogger(__name__)


class KnowledgeGraphState:
    """Main knowledge graph state management class.
    
    Provides high-level operations for managing the knowledge graph:
    - Adding/updating/removing cards
    - Finding similarities and suggestions
    - Category management
    - Self-correction capabilities
    """
    
    def __init__(self, backend_type: str = 'networkx', config: Dict[str, Any] = None):
        """Initialize knowledge graph state.
        
        Args:
            backend_type: Graph backend type ('networkx' or 'neo4j')
            config: Backend-specific configuration
        """
        self.backend: GraphBackend = create_graph_backend(backend_type, config or {})
        self.change_history = []  # Track changes for self-correction
        
        logger.info(f"Initialized KnowledgeGraphState with {backend_type} backend")
    
    def add_card(self, card_id: str, content: str, title: str = "", 
                 metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Add a new card to the knowledge graph.
        
        Args:
            card_id: Unique card identifier
            content: Card content for embedding generation
            title: Card title
            metadata: Additional metadata
            
        Returns:
            Dictionary with suggestions:
            {
                "parent_id": str | None,
                "category": str,
                "similar_cards": List[Tuple[str, float]],
                "suggested_connections": List[Dict]
            }
        """
        logger.info(f"Adding card {card_id} to knowledge graph")
        
        # Prepare node attributes
        attributes = {
            'content': content,
            'title': title,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        if metadata:
            attributes.update(metadata)
        
        # Add node to graph (this will generate embedding)
        self.backend.add_node(card_id, **attributes)
        
        # Find similar cards
        similar_cards = self.backend.find_similar_nodes(
            card_id, limit=10, min_similarity=0.1
        )
        
        # Suggest parent based on highest similarity
        parent_id = None
        if similar_cards:
            parent_id = similar_cards[0][0]  # Most similar card
            
            # Create parent-child relationship if similarity is high enough
            if similar_cards[0][1] > 0.5:
                self.backend.add_edge(parent_id, card_id, 'parent-child', 
                                    similarity_score=similar_cards[0][1])
        
        # Create similarity edges for top matches
        for similar_id, similarity in similar_cards[:5]:
            if similarity > 0.3:  # Only create edges for meaningful similarities
                self.backend.add_edge(card_id, similar_id, 'similar', 
                                    similarity_score=similarity)
        
        # Generate suggested connections
        suggested_connections = self._generate_connection_suggestions(card_id, similar_cards)
        
        # Record change for history
        self.change_history.append({
            'action': 'add_card',
            'card_id': card_id,
            'timestamp': datetime.now().isoformat(),
            'parent_id': parent_id,
            'similar_count': len(similar_cards)
        })
        
        # Auto-save periodically
        if len(self.change_history) % 10 == 0:
            self.backend.save()
        
        result = {
            'parent_id': parent_id,
            'similar_cards': similar_cards[:5],
            'suggested_connections': suggested_connections
        }
        
        logger.info(f"Added card {card_id}: parent={parent_id}, similar={len(similar_cards)}")
        return result
    
    def update_card(self, card_id: str, content: str = None, title: str = None, 
                   metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Update an existing card in the knowledge graph.
        
        Args:
            card_id: Card to update
            content: New content (optional)
            title: New title (optional)
            metadata: Additional metadata to update
            
        Returns:
            Updated suggestions similar to add_card
        """
        logger.info(f"Updating card {card_id}")
        
        # Get current node data
        current_node = self.backend.get_node(card_id)
        if not current_node:
            raise ValueError(f"Card {card_id} not found")
        
        # Prepare updates
        updates = {'updated_at': datetime.now().isoformat()}
        
        if content is not None:
            updates['content'] = content
        if title is not None:
            updates['title'] = title
        if metadata:
            updates.update(metadata)
        
        # Update node (this will regenerate embedding if content changed)
        self.backend.update_node(card_id, **updates)
        
        # If content changed, recalculate relationships
        if content is not None:
            # Remove old similarity edges
            old_similar = self.backend.get_neighbors(card_id, edge_type='similar')
            for similar_id in old_similar:
                self.backend.remove_edge(card_id, similar_id, 'similar')
                self.backend.remove_edge(similar_id, card_id, 'similar')
            
            # Find new similar cards
            similar_cards = self.backend.find_similar_nodes(
                card_id, limit=10, min_similarity=0.1
            )
            
            # Create new similarity edges
            for similar_id, similarity in similar_cards[:5]:
                if similarity > 0.3:
                    self.backend.add_edge(card_id, similar_id, 'similar', 
                                        similarity_score=similarity)
        
        # Record change
        self.change_history.append({
            'action': 'update_card',
            'card_id': card_id,
            'timestamp': datetime.now().isoformat(),
            'content_changed': content is not None
        })
        
        return self.get_card_suggestions(card_id)
    
    def remove_card(self, card_id: str) -> None:
        """Remove a card from the knowledge graph.
        
        Args:
            card_id: Card to remove
        """
        logger.info(f"Removing card {card_id}")
        
        # Remove from graph (this also removes all edges)
        self.backend.remove_node(card_id)
        
        # Record change
        self.change_history.append({
            'action': 'remove_card',
            'card_id': card_id,
            'timestamp': datetime.now().isoformat()
        })
    
    def get_card_suggestions(self, card_id: str) -> Dict[str, Any]:
        """Get suggestions for a card (similar cards, parent, etc.).
        
        Args:
            card_id: Card to get suggestions for
            
        Returns:
            Dictionary with suggestions
        """
        similar_cards = self.backend.find_similar_nodes(
            card_id, limit=10, min_similarity=0.1
        )
        
        # Get current parent
        parents = self.backend.get_neighbors(card_id, edge_type='parent-child', direction='in')
        current_parent = parents[0] if parents else None
        
        return {
            'current_parent': current_parent,
            'similar_cards': similar_cards[:5],
            'suggested_connections': self._generate_connection_suggestions(card_id, similar_cards)
        }
    
    def find_similar_cards(self, card_id: str, limit: int = 5, 
                          min_similarity: float = 0.3) -> List[Tuple[str, float]]:
        """Find cards similar to the given card.
        
        Args:
            card_id: Reference card
            limit: Maximum results
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of (card_id, similarity_score) tuples
        """
        return self.backend.find_similar_nodes(card_id, limit, min_similarity)
    
    def detect_issues(self) -> Dict[str, List]:
        """Detect various graph quality issues.
        
        Returns:
            Dictionary with different types of issues:
            {
                "orphaned_cards": List[str],
                "weak_connections": List[Tuple[str, str, float]],
                "duplicate_content": List[Tuple[str, str, float]]
            }
        """
        logger.info("Detecting graph quality issues")
        
        issues = {
            'orphaned_cards': self.backend.get_orphaned_nodes(),
            'weak_connections': self.backend.get_weak_connections(threshold=0.2),
            'duplicate_content': []
        }
        
        # Find potential duplicates (very high similarity)
        all_nodes = self.backend.get_all_nodes()
        for node_id in all_nodes:
            similar = self.backend.find_similar_nodes(node_id, limit=5, min_similarity=0.9)
            for similar_id, similarity in similar:
                if similarity > 0.95:  # Very high similarity suggests duplicates
                    issues['duplicate_content'].append((node_id, similar_id, similarity))
        
        logger.info(f"Found issues: {len(issues['orphaned_cards'])} orphaned, "
                   f"{len(issues['weak_connections'])} weak connections, "
                   f"{len(issues['duplicate_content'])} potential duplicates")
        
        return issues
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get knowledge graph statistics.
        
        Returns:
            Dictionary with graph statistics
        """
        return {
            'node_count': self.backend.get_node_count(),
            'edge_count': self.backend.get_edge_count(),
            'change_count': len(self.change_history),
            'last_change': self.change_history[-1] if self.change_history else None
        }
    
    def save(self) -> None:
        """Persist the knowledge graph state."""
        self.backend.save()
        logger.info("Saved knowledge graph state")
    
    def clear(self) -> None:
        """Clear all graph data."""
        self.backend.clear()
        self.change_history.clear()
        logger.warning("Cleared knowledge graph state")
    
    def _generate_connection_suggestions(
        self, 
        card_id: str, 
        similar_cards: List[Tuple[str, float]]
    ) -> List[Dict]:
        """Generate suggested connections based on similarity.
        
        Args:
            card_id: Card to generate suggestions for
            similar_cards: List of (card_id, similarity) tuples
            
        Returns:
            List of connection suggestion dicts
        """
        suggestions = []
        
        for similar_id, similarity in similar_cards[:3]:
            # Determine connection type based on similarity
            if similarity > 0.7:
                conn_type = "parent-child"
                reason = "Very high content similarity"
            elif similarity > 0.5:
                conn_type = "related"
                reason = "High content similarity"
            else:
                conn_type = "reference"
                reason = "Moderate content similarity"
            
            suggestions.append({
                'target_id': similar_id,
                'connection_type': conn_type,
                'similarity': similarity,
                'reason': reason
            })
        
        return suggestions
