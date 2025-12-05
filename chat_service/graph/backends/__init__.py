"""Graph Backend Interfaces and Implementations.

Provides pluggable backend architecture for knowledge graph storage:
- NetworkX: In-memory graph with pickle persistence (default)
- Neo4j: Graph database for large-scale deployments (optional)
"""

from .base import GraphBackend
from .networkx_backend import NetworkXBackend
from .factory import GraphBackendFactory, create_graph_backend

# Try to import Neo4j backend (optional)
try:
    from .neo4j_backend import Neo4jBackend
    __all__ = [
        'GraphBackend',
        'NetworkXBackend',
        'Neo4jBackend',
        'GraphBackendFactory',
        'create_graph_backend',
    ]
except ImportError:
    __all__ = [
        'GraphBackend',
        'NetworkXBackend',
        'GraphBackendFactory',
        'create_graph_backend',
    ]
