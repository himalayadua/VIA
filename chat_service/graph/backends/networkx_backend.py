"""
NetworkX Backend

In-memory graph storage using NetworkX with pickle persistence.
Fast for small-medium graphs (< 10k nodes).
"""

import os
import pickle
import logging
from typing import Dict, List, Optional, Tuple, Any
import networkx as nx

from .base import GraphBackend

logger = logging.getLogger(__name__)


class NetworkXBackend(GraphBackend):
    """
    NetworkX-based graph backend with pickle persistence.
    
    Pros:
    - Pure Python, no external dependencies
    - Fast for small-medium graphs
    - Easy to implement and debug
    
    Cons:
    - In-memory only (loads on startup)
    - Not suitable for very large graphs (> 10k nodes)
    """
    
    def __init__(self, persist_path: str = "data/knowledge_graph.pkl"):
        """
        Initialize NetworkX backend.
        
        Args:
            persist_path: Path to pickle file for persistence
        """
        self.persist_path = persist_path
        self.graph = nx.DiGraph()  # Directed graph
        self._ensure_data_dir()
        self.load()
        logger.info(f"NetworkX backend initialized (nodes: {self.get_node_count()})")
    
    def _ensure_data_dir(self):
        """Ensure data directory exists."""
        os.makedirs(os.path.dirname(self.persist_path), exist_ok=True)
    
    # ========================================================================
    # Core Operations
    # ========================================================================
    
    def add_node(
        self,
        node_id: str,
        node_type: str,
        content: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """Add a node to the graph."""
        try:
            self.graph.add_node(
                node_id,
                node_type=node_type,
                content=content,
                **metadata
            )
            logger.debug(f"Added node: {node_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding node {node_id}: {e}")
            return False
    
    def update_node(
        self,
        node_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update an existing node."""
        try:
            if node_id not in self.graph:
                logger.warning(f"Node {node_id} not found for update")
                return False
            
            if content is not None:
                self.graph.nodes[node_id]["content"] = content
            
            if metadata:
                self.graph.nodes[node_id].update(metadata)
            
            logger.debug(f"Updated node: {node_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating node {node_id}: {e}")
            return False
    
    def remove_node(self, node_id: str) -> bool:
        """Remove a node from the graph."""
        try:
            if node_id in self.graph:
                self.graph.remove_node(node_id)
                logger.debug(f"Removed node: {node_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error removing node {node_id}: {e}")
            return False
    
    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get node data."""
        try:
            if node_id in self.graph:
                data = dict(self.graph.nodes[node_id])
                data["id"] = node_id
                return data
            return None
        except Exception as e:
            logger.error(f"Error getting node {node_id}: {e}")
            return None
    
    # ========================================================================
    # Edge Operations
    # ========================================================================
    
    def add_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: str,
        similarity: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Add an edge between two nodes."""
        try:
            # Ensure both nodes exist
            if source_id not in self.graph or target_id not in self.graph:
                logger.warning(f"Cannot add edge: nodes {source_id} or {target_id} not found")
                return False
            
            edge_data = {
                "edge_type": edge_type,
                "similarity": similarity
            }
            if metadata:
                edge_data.update(metadata)
            
            self.graph.add_edge(source_id, target_id, **edge_data)
            logger.debug(f"Added edge: {source_id} → {target_id} ({edge_type})")
            return True
        except Exception as e:
            logger.error(f"Error adding edge {source_id} → {target_id}: {e}")
            return False
    
    def remove_edge(self, source_id: str, target_id: str) -> bool:
        """Remove an edge between two nodes."""
        try:
            if self.graph.has_edge(source_id, target_id):
                self.graph.remove_edge(source_id, target_id)
                logger.debug(f"Removed edge: {source_id} → {target_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error removing edge {source_id} → {target_id}: {e}")
            return False
    
    def get_edges(
        self,
        node_id: str,
        direction: str = "both"
    ) -> List[Dict[str, Any]]:
        """Get edges connected to a node."""
        try:
            if node_id not in self.graph:
                return []
            
            edges = []
            
            if direction in ["out", "both"]:
                # Outgoing edges
                for target in self.graph.successors(node_id):
                    edge_data = dict(self.graph[node_id][target])
                    edges.append({
                        "source": node_id,
                        "target": target,
                        "direction": "out",
                        **edge_data
                    })
            
            if direction in ["in", "both"]:
                # Incoming edges
                for source in self.graph.predecessors(node_id):
                    edge_data = dict(self.graph[source][node_id])
                    edges.append({
                        "source": source,
                        "target": node_id,
                        "direction": "in",
                        **edge_data
                    })
            
            return edges
        except Exception as e:
            logger.error(f"Error getting edges for {node_id}: {e}")
            return []
    
    # ========================================================================
    # Similarity Operations
    # ========================================================================
    
    def find_similar_nodes(
        self,
        node_id: str,
        limit: int = 10,
        min_similarity: float = 0.3
    ) -> List[Tuple[str, float]]:
        """
        Find nodes similar to the given node.
        
        Uses pre-computed similarity scores stored in edges.
        """
        try:
            if node_id not in self.graph:
                return []
            
            # Get all edges with similarity scores
            similar = []
            
            # Check outgoing edges
            for target in self.graph.successors(node_id):
                edge_data = self.graph[node_id][target]
                similarity = edge_data.get("similarity", 0.0)
                if similarity >= min_similarity:
                    similar.append((target, similarity))
            
            # Check incoming edges
            for source in self.graph.predecessors(node_id):
                edge_data = self.graph[source][node_id]
                similarity = edge_data.get("similarity", 0.0)
                if similarity >= min_similarity:
                    similar.append((source, similarity))
            
            # Sort by similarity (highest first)
            similar.sort(key=lambda x: x[1], reverse=True)
            
            return similar[:limit]
        except Exception as e:
            logger.error(f"Error finding similar nodes for {node_id}: {e}")
            return []
    
    # ========================================================================
    # Query Operations
    # ========================================================================
    
    def get_all_nodes(
        self,
        node_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all nodes, optionally filtered by type."""
        try:
            nodes = []
            for node_id, data in self.graph.nodes(data=True):
                if node_type is None or data.get("node_type") == node_type:
                    node_data = dict(data)
                    node_data["id"] = node_id
                    nodes.append(node_data)
            return nodes
        except Exception as e:
            logger.error(f"Error getting all nodes: {e}")
            return []
    
    def get_node_count(self) -> int:
        """Get total number of nodes."""
        return self.graph.number_of_nodes()
    
    def get_edge_count(self) -> int:
        """Get total number of edges."""
        return self.graph.number_of_edges()
    
    def clear(self) -> bool:
        """Clear all nodes and edges."""
        try:
            self.graph.clear()
            logger.info("Graph cleared")
            return True
        except Exception as e:
            logger.error(f"Error clearing graph: {e}")
            return False
    
    # ========================================================================
    # Persistence
    # ========================================================================
    
    def save(self) -> bool:
        """Persist the graph to disk using pickle."""
        try:
            self._ensure_data_dir()
            with open(self.persist_path, 'wb') as f:
                pickle.dump(self.graph, f, protocol=pickle.HIGHEST_PROTOCOL)
            logger.debug(f"Graph saved to {self.persist_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving graph: {e}")
            return False
    
    def load(self) -> bool:
        """Load the graph from disk."""
        try:
            if os.path.exists(self.persist_path):
                with open(self.persist_path, 'rb') as f:
                    self.graph = pickle.load(f)
                logger.info(f"Graph loaded from {self.persist_path} ({self.get_node_count()} nodes)")
                return True
            else:
                logger.info("No existing graph file found, starting with empty graph")
                return True
        except Exception as e:
            logger.error(f"Error loading graph: {e}")
            self.graph = nx.DiGraph()  # Reset to empty graph
            return False
    
    # ========================================================================
    # Statistics
    # ========================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get graph statistics."""
        try:
            node_count = self.get_node_count()
            edge_count = self.get_edge_count()
            
            stats = {
                "node_count": node_count,
                "edge_count": edge_count,
                "avg_degree": edge_count / node_count if node_count > 0 else 0,
                "is_connected": nx.is_weakly_connected(self.graph) if node_count > 0 else False,
                "backend": "NetworkX"
            }
            
            # Node type distribution
            type_counts = {}
            for _, data in self.graph.nodes(data=True):
                node_type = data.get("node_type", "unknown")
                type_counts[node_type] = type_counts.get(node_type, 0) + 1
            stats["node_types"] = type_counts
            
            return stats
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"error": str(e)}
    
    # ========================================================================
    # Advanced Operations (NetworkX-specific)
    # ========================================================================
    
    def find_path(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 5
    ) -> Optional[List[str]]:
        """Find shortest path between two nodes."""
        try:
            if source_id not in self.graph or target_id not in self.graph:
                return None
            
            path = nx.shortest_path(
                self.graph,
                source=source_id,
                target=target_id
            )
            
            if len(path) <= max_depth + 1:
                return path
            return None
        except nx.NetworkXNoPath:
            return None
        except Exception as e:
            logger.error(f"Error finding path: {e}")
            return None
    
    def get_neighbors(
        self,
        node_id: str,
        depth: int = 1
    ) -> List[str]:
        """Get neighbors up to a certain depth."""
        try:
            if node_id not in self.graph:
                return []
            
            neighbors = set()
            current_level = {node_id}
            
            for _ in range(depth):
                next_level = set()
                for node in current_level:
                    # Add successors and predecessors
                    next_level.update(self.graph.successors(node))
                    next_level.update(self.graph.predecessors(node))
                
                neighbors.update(next_level)
                current_level = next_level
            
            # Remove the original node
            neighbors.discard(node_id)
            
            return list(neighbors)
        except Exception as e:
            logger.error(f"Error getting neighbors for {node_id}: {e}")
            return []
    
    def get_subgraph(
        self,
        node_ids: List[str]
    ) -> Dict[str, Any]:
        """Extract a subgraph containing specified nodes."""
        try:
            # Filter to nodes that exist
            valid_nodes = [nid for nid in node_ids if nid in self.graph]
            
            if not valid_nodes:
                return {"nodes": [], "edges": []}
            
            # Create subgraph
            subgraph = self.graph.subgraph(valid_nodes)
            
            # Extract nodes
            nodes = []
            for node_id, data in subgraph.nodes(data=True):
                node_data = dict(data)
                node_data["id"] = node_id
                nodes.append(node_data)
            
            # Extract edges
            edges = []
            for source, target, data in subgraph.edges(data=True):
                edge_data = dict(data)
                edge_data["source"] = source
                edge_data["target"] = target
                edges.append(edge_data)
            
            return {
                "nodes": nodes,
                "edges": edges,
                "node_count": len(nodes),
                "edge_count": len(edges)
            }
        except Exception as e:
            logger.error(f"Error getting subgraph: {e}")
            return {"nodes": [], "edges": []}
