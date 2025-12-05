"""Graph backend factory for easy switching between implementations.

Provides a unified way to create graph backends without code changes.
Supports NetworkX (default) and Neo4j backends.
"""

import logging
from typing import Dict, Any

from .base import GraphBackend
from .networkx_backend import NetworkXBackend

logger = logging.getLogger(__name__)

# Try to import Neo4j backend (optional)
try:
    from .neo4j_backend import Neo4jBackend
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logger.debug("Neo4j backend not available (neo4j-driver not installed)")


class GraphBackendFactory:
    """Factory for creating graph backends."""
    
    _backends = {
        'networkx': NetworkXBackend,
    }
    
    # Add Neo4j if available
    if NEO4J_AVAILABLE:
        _backends['neo4j'] = Neo4jBackend
    
    @classmethod
    def create_backend(cls, backend_type: str, config: Dict[str, Any] = None) -> GraphBackend:
        """Create a graph backend instance.
        
        Args:
            backend_type: Type of backend ('networkx' or 'neo4j')
            config: Backend-specific configuration
            
        Returns:
            Initialized graph backend
            
        Raises:
            ValueError: If backend type is not supported
            ImportError: If required dependencies are missing
        """
        if backend_type not in cls._backends:
            available = ', '.join(cls._backends.keys())
            raise ValueError(f"Unsupported backend type '{backend_type}'. Available: {available}")
        
        backend_class = cls._backends[backend_type]
        
        try:
            backend = backend_class()
            
            if config:
                backend.initialize(config)
            
            logger.info(f"Created {backend_type} graph backend")
            return backend
            
        except ImportError as e:
            logger.error(f"Failed to create {backend_type} backend: {e}")
            raise
        except Exception as e:
            logger.error(f"Error initializing {backend_type} backend: {e}")
            raise
    
    @classmethod
    def get_available_backends(cls) -> list:
        """Get list of available backend types.
        
        Returns:
            List of available backend type names
        """
        available = []
        
        for backend_type, backend_class in cls._backends.items():
            try:
                # Try to instantiate to check if dependencies are available
                backend_class()
                available.append(backend_type)
            except ImportError:
                logger.debug(f"Backend {backend_type} not available (missing dependencies)")
            except Exception:
                logger.debug(f"Backend {backend_type} not available (initialization error)")
        
        return available
    
    @classmethod
    def register_backend(cls, name: str, backend_class: type) -> None:
        """Register a custom backend implementation.
        
        Args:
            name: Backend name
            backend_class: Backend class (must inherit from GraphBackend)
        """
        if not issubclass(backend_class, GraphBackend):
            raise ValueError(f"Backend class must inherit from GraphBackend")
        
        cls._backends[name] = backend_class
        logger.info(f"Registered custom backend: {name}")


def create_graph_backend(backend_type: str = None, config: Dict[str, Any] = None) -> GraphBackend:
    """Convenience function to create a graph backend.
    
    Args:
        backend_type: Type of backend (defaults to 'networkx')
        config: Backend configuration
        
    Returns:
        Initialized graph backend
    """
    if backend_type is None:
        # Auto-select best available backend
        available = GraphBackendFactory.get_available_backends()
        
        if 'neo4j' in available:
            backend_type = 'neo4j'
            logger.info("Auto-selected Neo4j backend")
        elif 'networkx' in available:
            backend_type = 'networkx'
            logger.info("Auto-selected NetworkX backend")
        else:
            raise RuntimeError("No graph backends available")
    
    return GraphBackendFactory.create_backend(backend_type, config)
