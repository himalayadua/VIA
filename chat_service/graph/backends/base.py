"""
Graph Backend Interface

Abstract base class that defines the interface for graph storage backends.
This allows easy switching between NetworkX, Neo4j, or other graph databases
without changing any application code.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any
import logging

logger = logging.getLogger(__name__)


class GraphBackend(ABC):
    """
    Abstract base class for graph storage backends.
    
    All graph backends (NetworkX, Neo4j, etc.) must implement this interface.
    This ensures that switching backends requires only a configuration change,
    not code changes.
    """
    
    @abstractmethod
    def add_node(
        self,
        node_id: str,
        node_type: str,
        content: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Add a node to the graph.
        
        Args:
            node_id: Unique identifier for the node
            node_type: Type of node (e.g., "card", "category")
            content: Text content of the node
            metadata: Additional metadata (title, tags, etc.)
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def update_node(
        self,
        node_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update an existing node.
        
        Args:
            node_id: Node to update
            content: New content (if provided)
            metadata: New metadata to merge (if provided)
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def remove_node(self, node_id: str) -> bool:
        """
        Remove a node from the graph.
        
        Args:
            node_id: Node to remove
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """
        Get node data.
        
        Args:
            node_id: Node to retrieve
            
        Returns:
            Node data dict or None if not found
        """
        pass
    
    @abstractmethod
    def add_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: str,
        similarity: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add an edge between two nodes.
        
        Args:
            source_id: Source node ID
            target_id: Target node ID
            edge_type: Type of relationship (e.g., "parent-child", "similar")
            similarity: Similarity score (0.0 to 1.0)
            metadata: Additional edge metadata
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def remove_edge(self, source_id: str, target_id: str) -> bool:
        """
        Remove an edge between two nodes.
        
        Args:
            source_id: Source node ID
            target_id: Target node ID
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_edges(
        self,
        node_id: str,
        direction: str = "both"
    ) -> List[Dict[str, Any]]:
        """
        Get edges connected to a node.
        
        Args:
            node_id: Node to get edges for
            direction: "in", "out", or "both"
            
        Returns:
            List of edge dicts with source, target, type, similarity
        """
        pass
    
    @abstractmethod
    def find_similar_nodes(
        self,
        node_id: str,
        limit: int = 10,
        min_similarity: float = 0.3
    ) -> List[Tuple[str, float]]:
        """
        Find nodes similar to the given node.
        
        Args:
            node_id: Node to find similar nodes for
            limit: Maximum number of results
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of (node_id, similarity_score) tuples, sorted by similarity
        """
        pass
    
    @abstractmethod
    def get_all_nodes(
        self,
        node_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all nodes, optionally filtered by type.
        
        Args:
            node_type: Optional type filter
            
        Returns:
            List of node dicts
        """
        pass
    
    @abstractmethod
    def get_node_count(self) -> int:
        """
        Get total number of nodes in the graph.
        
        Returns:
            Node count
        """
        pass
    
    @abstractmethod
    def get_edge_count(self) -> int:
        """
        Get total number of edges in the graph.
        
        Returns:
            Edge count
        """
        pass
    
    @abstractmethod
    def clear(self) -> bool:
        """
        Clear all nodes and edges from the graph.
        
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    def save(self) -> bool:
        """
        Persist the graph to storage.
        
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    def load(self) -> bool:
        """
        Load the graph from storage.
        
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """
        Get graph statistics.
        
        Returns:
            Dict with stats like node_count, edge_count, avg_degree, etc.
        """
        pass
    
    # Optional: Advanced graph operations
    
    def find_path(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 5
    ) -> Optional[List[str]]:
        """
        Find shortest path between two nodes.
        
        Args:
            source_id: Start node
            target_id: End node
            max_depth: Maximum path length
            
        Returns:
            List of node IDs forming the path, or None if no path exists
        """
        # Default implementation: not supported
        logger.warning(f"{self.__class__.__name__} does not implement find_path")
        return None
    
    def get_neighbors(
        self,
        node_id: str,
        depth: int = 1
    ) -> List[str]:
        """
        Get neighbors of a node up to a certain depth.
        
        Args:
            node_id: Node to get neighbors for
            depth: How many hops away (default 1 = direct neighbors)
            
        Returns:
            List of neighbor node IDs
        """
        # Default implementation: not supported
        logger.warning(f"{self.__class__.__name__} does not implement get_neighbors")
        return []
    
    def get_subgraph(
        self,
        node_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Extract a subgraph containing specified nodes and their connections.
        
        Args:
            node_ids: Nodes to include in subgraph
            
        Returns:
            Dict with nodes and edges
        """
        # Default implementation: not supported
        logger.warning(f"{self.__class__.__name__} does not implement get_subgraph")
        return {"nodes": [], "edges": []}
