"""
Connection Manager

Intelligent connection creation system that analyzes semantic relationships
and creates appropriate connections between cards.
"""

import logging
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Intelligent connection management system.
    
    Analyzes semantic relationships between cards and creates
    appropriate connections with proper types and strengths.
    """
    
    # Configuration constants
    PARENT_CHILD_THRESHOLD = 0.7  # Similarity for parent-child relationship
    RELATED_THRESHOLD = 0.5  # Similarity for related relationship
    REFERENCE_THRESHOLD = 0.3  # Similarity for reference relationship
    STRONG_CONNECTION = 0.7  # Threshold for strong connection
    MEDIUM_CONNECTION = 0.5  # Threshold for medium connection
    
    def __init__(self):
        """Initialize connection manager."""
        logger.info("ConnectionManager initialized")
    
    def analyze_relationships(
        self,
        new_card: Dict,
        existing_cards: List[Dict],
        canvas_id: str
    ) -> List[Dict]:
        """
        Analyze semantic relationships between new card and existing cards.
        
        Args:
            new_card: New card dict with content
            existing_cards: List of existing cards
            canvas_id: Canvas ID
            
        Returns:
            List of relationship dicts with card_id, similarity, and type
        """
        try:
            # Import here to avoid circular dependency
            from tools.canvas_tools import find_similar_cards
            
            new_card_content = new_card.get("content", "")
            
            if not new_card_content:
                logger.warning("New card has no content, cannot analyze relationships")
                return []
            
            logger.info(f"Analyzing relationships for new card on canvas {canvas_id}")
            
            # Find similar cards
            result = find_similar_cards(
                content=new_card_content,
                canvas_id=canvas_id,
                limit=10,
                min_similarity=self.REFERENCE_THRESHOLD
            )
            
            if not result.get("success") or not result.get("similar_cards"):
                logger.info("No similar cards found for relationships")
                return []
            
            # Categorize relationships by similarity
            relationships = []
            for similar_card in result["similar_cards"]:
                card_id = similar_card["id"]
                similarity = similar_card["similarity_score"]
                
                # Determine relationship type
                rel_type = self.determine_connection_type(similarity)
                
                relationships.append({
                    "card_id": card_id,
                    "similarity": similarity,
                    "type": rel_type,
                    "strength": self.calculate_connection_strength(similarity)
                })
            
            logger.info(f"Found {len(relationships)} relationships")
            return relationships
            
        except Exception as e:
            logger.error(f"Error analyzing relationships: {e}", exc_info=True)
            return []
    
    def determine_connection_type(self, similarity_score: float) -> str:
        """
        Determine connection type based on similarity score.
        
        Args:
            similarity_score: Similarity score between 0 and 1
            
        Returns:
            Connection type: "parent-child", "related", or "reference"
        """
        if similarity_score >= self.PARENT_CHILD_THRESHOLD:
            return "parent-child"
        elif similarity_score >= self.RELATED_THRESHOLD:
            return "related"
        else:
            return "reference"
    
    def calculate_connection_strength(self, similarity_score: float) -> str:
        """
        Calculate connection strength based on similarity score.
        
        Args:
            similarity_score: Similarity score between 0 and 1
            
        Returns:
            Connection strength: "strong", "medium", or "weak"
        """
        if similarity_score >= self.STRONG_CONNECTION:
            return "strong"
        elif similarity_score >= self.MEDIUM_CONNECTION:
            return "medium"
        else:
            return "weak"
    
    def avoid_redundant_connections(
        self,
        new_connections: List[Dict],
        existing_connections: List[Dict]
    ) -> List[Dict]:
        """
        Filter out redundant connections.
        
        Prevents creating connections that would be redundant given
        existing connections (e.g., if A→B and B→C exist, don't create A→C
        unless directly related with high similarity).
        
        Args:
            new_connections: List of proposed new connections
            existing_connections: List of existing connections
            
        Returns:
            Filtered list of non-redundant connections
        """
        # Build adjacency map of existing connections
        adjacency = {}
        for conn in existing_connections:
            source = conn.get("source_id")
            target = conn.get("target_id")
            
            if source not in adjacency:
                adjacency[source] = set()
            adjacency[source].add(target)
        
        # Filter new connections
        filtered = []
        for conn in new_connections:
            source = conn.get("source_id")
            target = conn.get("target_id")
            similarity = conn.get("similarity", 0)
            
            # Check if connection already exists
            if source in adjacency and target in adjacency[source]:
                logger.debug(f"Skipping duplicate connection: {source} → {target}")
                continue
            
            # Check for transitive redundancy
            # Only skip if similarity is low (< 0.7)
            if similarity < 0.7 and self._is_transitive_connection(source, target, adjacency):
                logger.debug(f"Skipping transitive connection: {source} → {target}")
                continue
            
            filtered.append(conn)
        
        logger.info(f"Filtered {len(new_connections) - len(filtered)} redundant connections")
        return filtered
    
    def create_connections(
        self,
        new_card_id: str,
        relationships: List[Dict],
        canvas_id: str,
        existing_connections: Optional[List[Dict]] = None
    ) -> List[Dict]:
        """
        Create connections between new card and related cards.
        
        Args:
            new_card_id: ID of the new card
            relationships: List of relationship dicts from analyze_relationships
            canvas_id: Canvas ID
            existing_connections: Optional list of existing connections
            
        Returns:
            List of created connection dicts
        """
        try:
            # Import here to avoid circular dependency
            from tools.canvas_api import create_connection
            
            if not relationships:
                logger.info("No relationships to create connections for")
                return []
            
            # Prepare new connections
            new_connections = []
            for rel in relationships:
                new_connections.append({
                    "source_id": new_card_id,
                    "target_id": rel["card_id"],
                    "type": rel["type"],
                    "strength": rel["strength"],
                    "similarity": rel["similarity"]
                })
            
            # Filter redundant connections if existing connections provided
            if existing_connections:
                new_connections = self.avoid_redundant_connections(
                    new_connections,
                    existing_connections
                )
            
            # Create connections in database
            created_connections = []
            for conn in new_connections:
                try:
                    created = create_connection(
                        canvas_id=canvas_id,
                        source_id=conn["source_id"],
                        target_id=conn["target_id"],
                        connection_type=conn["type"]
                    )
                    
                    # Add metadata
                    created["strength"] = conn["strength"]
                    created["similarity"] = conn["similarity"]
                    
                    created_connections.append(created)
                    
                    logger.debug(
                        f"Created {conn['type']} connection: "
                        f"{conn['source_id']} → {conn['target_id']} "
                        f"(strength: {conn['strength']}, similarity: {conn['similarity']:.2f})"
                    )
                    
                except Exception as e:
                    logger.error(f"Error creating connection: {e}")
                    continue
            
            logger.info(f"Created {len(created_connections)} connections")
            return created_connections
            
        except Exception as e:
            logger.error(f"Error creating connections: {e}", exc_info=True)
            return []
    
    def get_connection_summary(self, connections: List[Dict]) -> str:
        """
        Generate human-readable summary of created connections.
        
        Args:
            connections: List of connection dicts
            
        Returns:
            Summary string
        """
        if not connections:
            return "No connections created"
        
        # Count by type
        type_counts = {}
        for conn in connections:
            conn_type = conn.get("type", "unknown")
            type_counts[conn_type] = type_counts.get(conn_type, 0) + 1
        
        # Build summary
        parts = []
        for conn_type, count in type_counts.items():
            parts.append(f"{count} {conn_type}")
        
        return f"Created {len(connections)} connections: {', '.join(parts)}"
    
    def _is_transitive_connection(
        self,
        source: str,
        target: str,
        adjacency: Dict[str, set]
    ) -> bool:
        """
        Check if a connection would be transitive (redundant).
        
        A connection A→C is transitive if there exists A→B and B→C.
        
        Args:
            source: Source card ID
            target: Target card ID
            adjacency: Adjacency map of existing connections
            
        Returns:
            True if connection is transitive, False otherwise
        """
        if source not in adjacency:
            return False
        
        # Check if there's an intermediate node
        for intermediate in adjacency[source]:
            if intermediate in adjacency and target in adjacency[intermediate]:
                return True
        
        return False
