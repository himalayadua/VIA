"""Neo4j-based graph backend implementation.

Provides persistent graph storage using Neo4j database.
Suitable for large-scale graphs (100k+ nodes) with complex queries.

Note: Requires neo4j-driver package and running Neo4j instance.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

from .base import GraphBackend

logger = logging.getLogger(__name__)

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logger.warning("neo4j-driver not installed. Neo4j backend unavailable.")


class Neo4jBackend(GraphBackend):
    """Neo4j-based graph backend.
    
    Requires:
    - neo4j-driver package: pip install neo4j
    - Running Neo4j instance
    """
    
    def __init__(self):
        if not NEO4J_AVAILABLE:
            raise ImportError("neo4j-driver package required for Neo4j backend")
        
        self.driver = None
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize Neo4j backend.
        
        Args:
            config: Configuration with Neo4j connection details:
                - uri: Neo4j URI (e.g., "bolt://localhost:7687")
                - username: Neo4j username
                - password: Neo4j password
                - database: Database name (optional, default "neo4j")
        """
        uri = config.get('uri', 'bolt://localhost:7687')
        username = config.get('username', 'neo4j')
        password = config.get('password', 'password')
        
        try:
            self.driver = GraphDatabase.driver(uri, auth=(username, password))
            
            # Test connection
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                result.single()
            
            # Create indexes for performance
            self._create_indexes()
            
            logger.info(f"Initialized Neo4j backend at {uri}")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    def _create_indexes(self) -> None:
        """Create necessary indexes for performance."""
        indexes = [
            "CREATE INDEX node_id_index IF NOT EXISTS FOR (n:Node) ON (n.node_id)",
            "CREATE INDEX category_index IF NOT EXISTS FOR (n:Node) ON (n.category)",
            "CREATE INDEX similarity_index IF NOT EXISTS FOR ()-[r:SIMILAR]-() ON (r.similarity_score)"
        ]
        
        with self.driver.session() as session:
            for index_query in indexes:
                try:
                    session.run(index_query)
                except Exception as e:
                    logger.debug(f"Index creation info: {e}")
    
    def add_node(self, node_id: str, **attributes) -> None:
        """Add a node to the graph."""
        serialized_attrs = self._serialize_attributes(attributes)
        serialized_attrs['node_id'] = node_id
        
        query = """
        MERGE (n:Node {node_id: $node_id})
        SET n += $attributes
        """
        
        with self.driver.session() as session:
            session.run(query, node_id=node_id, attributes=serialized_attrs)
        
        logger.debug(f"Added node {node_id} to Neo4j")
    
    def update_node(self, node_id: str, **attributes) -> None:
        """Update node attributes."""
        serialized_attrs = self._serialize_attributes(attributes)
        
        query = """
        MATCH (n:Node {node_id: $node_id})
        SET n += $attributes
        """
        
        with self.driver.session() as session:
            session.run(query, node_id=node_id, attributes=serialized_attrs)
    
    def remove_node(self, node_id: str) -> None:
        """Remove a node and all its edges."""
        query = """
        MATCH (n:Node {node_id: $node_id})
        DETACH DELETE n
        """
        
        with self.driver.session() as session:
            session.run(query, node_id=node_id)
    
    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get node attributes."""
        query = """
        MATCH (n:Node {node_id: $node_id})
        RETURN properties(n) as props
        """
        
        with self.driver.session() as session:
            result = session.run(query, node_id=node_id)
            record = result.single()
            
            if record:
                return self._deserialize_attributes(record['props'])
            return None
    
    def add_edge(self, source_id: str, target_id: str, edge_type: str, **attributes) -> None:
        """Add an edge between two nodes."""
        serialized_attrs = self._serialize_attributes(attributes)
        
        # Use dynamic relationship type
        query = f"""
        MATCH (source:Node {{node_id: $source_id}})
        MATCH (target:Node {{node_id: $target_id}})
        MERGE (source)-[r:{edge_type.upper().replace('-', '_')}]->(target)
        SET r += $attributes
        """
        
        with self.driver.session() as session:
            session.run(query, source_id=source_id, target_id=target_id, attributes=serialized_attrs)
    
    def remove_edge(self, source_id: str, target_id: str, edge_type: str = None) -> None:
        """Remove edge(s) between nodes."""
        if edge_type:
            query = f"""
            MATCH (source:Node {{node_id: $source_id}})-[r:{edge_type.upper().replace('-', '_')}]->(target:Node {{node_id: $target_id}})
            DELETE r
            """
        else:
            query = """
            MATCH (source:Node {node_id: $source_id})-[r]->(target:Node {node_id: $target_id})
            DELETE r
            """
        
        with self.driver.session() as session:
            session.run(query, source_id=source_id, target_id=target_id)
    
    def get_neighbors(self, node_id: str, edge_type: str = None, direction: str = "both") -> List[str]:
        """Get neighboring nodes."""
        if edge_type:
            rel_pattern = f"[r:{edge_type.upper().replace('-', '_')}]"
        else:
            rel_pattern = "[r]"
        
        if direction == "out":
            pattern = f"(n:Node {{node_id: $node_id}})-{rel_pattern}->(neighbor:Node)"
        elif direction == "in":
            pattern = f"(neighbor:Node)-{rel_pattern}->(n:Node {{node_id: $node_id}})"
        else:  # both
            pattern = f"(n:Node {{node_id: $node_id}})-{rel_pattern}-(neighbor:Node)"
        
        query = f"""
        MATCH {pattern}
        RETURN DISTINCT neighbor.node_id as neighbor_id
        """
        
        with self.driver.session() as session:
            result = session.run(query, node_id=node_id)
            return [record['neighbor_id'] for record in result]
    
    def find_similar_nodes(self, node_id: str, limit: int = 10, min_similarity: float = 0.0) -> List[Tuple[str, float]]:
        """Find nodes similar to the given node."""
        query = """
        MATCH (n:Node {node_id: $node_id})-[r:SIMILAR]-(similar:Node)
        WHERE r.similarity_score >= $min_similarity
        RETURN similar.node_id as similar_id, r.similarity_score as similarity
        ORDER BY r.similarity_score DESC
        LIMIT $limit
        """
        
        with self.driver.session() as session:
            result = session.run(query, node_id=node_id, min_similarity=min_similarity, limit=limit)
            return [(record['similar_id'], record['similarity']) for record in result]
    
    def get_nodes_by_category(self, category: str) -> List[str]:
        """Get all nodes in a category."""
        query = """
        MATCH (n:Node {category: $category})
        RETURN n.node_id as node_id
        """
        
        with self.driver.session() as session:
            result = session.run(query, category=category)
            return [record['node_id'] for record in result]
    
    def get_orphaned_nodes(self) -> List[str]:
        """Get nodes with no connections."""
        query = """
        MATCH (n:Node)
        WHERE NOT (n)--() 
        RETURN n.node_id as node_id
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            return [record['node_id'] for record in result]
    
    def get_weak_connections(self, threshold: float = 0.3) -> List[Tuple[str, str, float]]:
        """Get connections with low similarity scores."""
        query = """
        MATCH (source:Node)-[r:SIMILAR]->(target:Node)
        WHERE r.similarity_score < $threshold
        RETURN source.node_id as source_id, target.node_id as target_id, r.similarity_score as similarity
        """
        
        with self.driver.session() as session:
            result = session.run(query, threshold=threshold)
            return [(record['source_id'], record['target_id'], record['similarity']) for record in result]
    
    def calculate_similarity(self, node1_id: str, node2_id: str) -> float:
        """Calculate similarity between two nodes.
        
        Note: Neo4j backend stores pre-computed similarities.
        This method looks up existing similarity edges.
        """
        query = """
        MATCH (n1:Node {node_id: $node1_id})-[r:SIMILAR]-(n2:Node {node_id: $node2_id})
        RETURN r.similarity_score as similarity
        """
        
        with self.driver.session() as session:
            result = session.run(query, node1_id=node1_id, node2_id=node2_id)
            record = result.single()
            return record['similarity'] if record else 0.0
    
    def batch_calculate_similarities(self, node_id: str, target_nodes: List[str]) -> Dict[str, float]:
        """Calculate similarities between one node and multiple targets."""
        query = """
        MATCH (n:Node {node_id: $node_id})-[r:SIMILAR]-(target:Node)
        WHERE target.node_id IN $target_nodes
        RETURN target.node_id as target_id, r.similarity_score as similarity
        """
        
        with self.driver.session() as session:
            result = session.run(query, node_id=node_id, target_nodes=target_nodes)
            similarities = {record['target_id']: record['similarity'] for record in result}
            
            # Fill in missing nodes with 0.0
            for target_id in target_nodes:
                if target_id not in similarities:
                    similarities[target_id] = 0.0
            
            return similarities
    
    def get_all_nodes(self) -> List[str]:
        """Get all node IDs in the graph."""
        query = "MATCH (n:Node) RETURN n.node_id as node_id"
        
        with self.driver.session() as session:
            result = session.run(query)
            return [record['node_id'] for record in result]
    
    def get_node_count(self) -> int:
        """Get total number of nodes."""
        query = "MATCH (n:Node) RETURN count(n) as count"
        
        with self.driver.session() as session:
            result = session.run(query)
            return result.single()['count']
    
    def get_edge_count(self) -> int:
        """Get total number of edges."""
        query = "MATCH ()-[r]->() RETURN count(r) as count"
        
        with self.driver.session() as session:
            result = session.run(query)
            return result.single()['count']
    
    def save(self) -> None:
        """Persist the graph to storage.
        
        Note: Neo4j automatically persists data, so this is a no-op.
        """
        pass
    
    def load(self) -> None:
        """Load the graph from storage.
        
        Note: Neo4j data is always available, so this is a no-op.
        """
        pass
    
    def clear(self) -> None:
        """Clear all nodes and edges.
        
        WARNING: This will delete all data in the Neo4j database!
        """
        query = "MATCH (n) DETACH DELETE n"
        
        with self.driver.session() as session:
            session.run(query)
        
        logger.warning("Cleared all data from Neo4j database")
    
    def _serialize_attributes(self, attributes: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize attributes for Neo4j storage."""
        serialized = {}
        
        for key, value in attributes.items():
            if isinstance(value, np.ndarray):
                serialized[key] = value.tolist()
            elif isinstance(value, (np.integer, np.floating)):
                serialized[key] = value.item()
            else:
                serialized[key] = value
        
        return serialized
    
    def _deserialize_attributes(self, attributes: Dict[str, Any]) -> Dict[str, Any]:
        """Deserialize attributes from Neo4j storage."""
        deserialized = {}
        
        for key, value in attributes.items():
            if key == 'embedding' and isinstance(value, list):
                deserialized[key] = np.array(value)
            else:
                deserialized[key] = value
        
        return deserialized
    
    def __del__(self):
        """Clean up Neo4j driver connection."""
        if self.driver:
            self.driver.close()
