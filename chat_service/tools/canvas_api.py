"""
Canvas API Helper Functions

Helper functions to interact with the Express.js Canvas API from Python tools.
These functions make HTTP requests to create/read/update canvas cards and connections.
"""

import logging
import requests
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Express API base URL
CANVAS_API_BASE = "http://localhost:3000/api"


def create_card(
    canvas_id: str,
    title: str,
    content: str,
    card_type: str = "rich_text",
    position_x: float = 0,
    position_y: float = 0,
    parent_id: Optional[str] = None,
    tags: Optional[List[str]] = None,
    width: int = 300,
    height: int = 150,
    card_data: Optional[Dict] = None,
    source_url: Optional[str] = None,
    source_type: str = "manual",
    sources: Optional[List[Dict]] = None,
    has_conflict: bool = False
) -> Dict:
    """
    Create a new card on the canvas via Express API with source attribution.
    
    Args:
        canvas_id: Canvas ID where card will be created
        title: Card title
        content: Card content (markdown for rich_text)
        card_type: Type of card (rich_text, link, video, todo, reminder)
        position_x: X coordinate on canvas
        position_y: Y coordinate on canvas
        parent_id: Optional parent card ID
        tags: Optional list of tags
        width: Card width in pixels
        height: Card height in pixels
        card_data: Optional additional card-specific data
        source_url: Optional source URL where content came from
        source_type: Type of source (url, ai_generated, manual)
        sources: Optional list of sources for merged content
        has_conflict: Flag indicating conflicting information
        
    Returns:
        Created card object with id, title, content, etc.
        
    Raises:
        requests.RequestException: If API request fails
    """
    try:
        payload = {
            "canvas_id": canvas_id,
            "title": title,
            "content": content,
            "card_type": card_type,
            "position_x": position_x,
            "position_y": position_y,
            "width": width,
            "height": height,
            "tags": tags or [],
            "type": card_type,  # Use card_type for ReactFlow node type
            "source_type": source_type,
            "has_conflict": has_conflict
        }
        
        if parent_id:
            payload["parent_id"] = parent_id
        
        if card_data:
            payload["card_data"] = card_data
        
        if source_url:
            payload["source_url"] = source_url
        
        if sources:
            payload["sources"] = sources
        
        response = requests.post(
            f"{CANVAS_API_BASE}/nodes",
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        
        card = response.json()
        logger.info(f"Created card: {card.get('id')} - {title} (source: {source_type})")
        
        # Auto-index card in knowledge base (non-blocking)
        try:
            from knowledge_base.auto_indexer import auto_index_card_sync
            auto_index_card_sync(
                card_id=card.get('id'),
                content=content,
                canvas_id=canvas_id,
                card_type=card_type,
                metadata={
                    "title": title,
                    "source_type": source_type,
                    "source_url": source_url,
                    "tags": tags or []
                }
            )
        except Exception as e:
            # Don't fail card creation if indexing fails
            logger.warning(f"Auto-indexing failed for card {card.get('id')}: {e}")
        
        return card
        
    except requests.RequestException as e:
        logger.error(f"Failed to create card '{title}': {e}")
        raise


def get_card(card_id: str) -> Dict:
    """
    Fetch a card by ID via Express API.
    
    Args:
        card_id: Card ID to fetch
        
    Returns:
        Card object
        
    Raises:
        requests.RequestException: If API request fails
    """
    try:
        response = requests.get(
            f"{CANVAS_API_BASE}/nodes/{card_id}",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
        
    except requests.RequestException as e:
        logger.error(f"Failed to fetch card {card_id}: {e}")
        raise


def get_canvas_cards(canvas_id: str) -> List[Dict]:
    """
    Fetch all cards on a canvas via Express API.
    
    Args:
        canvas_id: Canvas ID
        
    Returns:
        List of card objects
        
    Raises:
        requests.RequestException: If API request fails
    """
    try:
        response = requests.get(
            f"{CANVAS_API_BASE}/nodes",
            params={"canvas_id": canvas_id},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
        
    except requests.RequestException as e:
        logger.error(f"Failed to fetch cards for canvas {canvas_id}: {e}")
        raise


def update_card(
    card_id: str,
    title: Optional[str] = None,
    content: Optional[str] = None,
    tags: Optional[List[str]] = None,
    position_x: Optional[float] = None,
    position_y: Optional[float] = None,
    card_data: Optional[Dict] = None
) -> Dict:
    """
    Update a card via Express API.
    
    Args:
        card_id: Card ID to update
        title: Optional new title
        content: Optional new content
        tags: Optional new tags
        position_x: Optional new X position
        position_y: Optional new Y position
        card_data: Optional new card data
        
    Returns:
        Updated card object
        
    Raises:
        requests.RequestException: If API request fails
    """
    try:
        payload = {}
        
        if title is not None:
            payload["title"] = title
        if content is not None:
            payload["content"] = content
        if tags is not None:
            payload["tags"] = tags
        if position_x is not None:
            payload["position_x"] = position_x
        if position_y is not None:
            payload["position_y"] = position_y
        if card_data is not None:
            payload["card_data"] = card_data
        
        response = requests.put(
            f"{CANVAS_API_BASE}/nodes/{card_id}",
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        
        card = response.json()
        logger.info(f"Updated card: {card_id}")
        return card
        
    except requests.RequestException as e:
        logger.error(f"Failed to update card {card_id}: {e}")
        raise


def create_connection(
    canvas_id: str,
    source_id: str,
    target_id: str,
    connection_type: str = "default",
    animated: bool = False
) -> Dict:
    """
    Create a connection between two cards via Express API.
    
    Args:
        canvas_id: Canvas ID
        source_id: Source card ID
        target_id: Target card ID
        connection_type: Type of connection (default, parent-child, related, reference)
        animated: Whether connection should be animated
        
    Returns:
        Created connection object
        
    Raises:
        requests.RequestException: If API request fails
    """
    try:
        payload = {
            "canvas_id": canvas_id,
            "source_id": source_id,
            "target_id": target_id,
            "type": connection_type,
            "animated": animated
        }
        
        response = requests.post(
            f"{CANVAS_API_BASE}/connections",
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        
        connection = response.json()
        logger.info(f"Created connection: {source_id} -> {target_id}")
        return connection
        
    except requests.RequestException as e:
        logger.error(f"Failed to create connection {source_id} -> {target_id}: {e}")
        raise


def get_canvas_connections(canvas_id: str) -> List[Dict]:
    """
    Fetch all connections on a canvas via Express API.
    
    Args:
        canvas_id: Canvas ID
        
    Returns:
        List of connection objects
        
    Raises:
        requests.RequestException: If API request fails
    """
    try:
        response = requests.get(
            f"{CANVAS_API_BASE}/connections",
            params={"canvas_id": canvas_id},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
        
    except requests.RequestException as e:
        logger.error(f"Failed to fetch connections for canvas {canvas_id}: {e}")
        raise


def calculate_child_position(
    parent_x: float,
    parent_y: float,
    child_index: int,
    total_children: int,
    radius: float = 280
) -> tuple[float, float]:
    """
    Calculate position for a child card in circular arrangement around parent.
    
    Args:
        parent_x: Parent card X position
        parent_y: Parent card Y position
        child_index: Index of this child (0-based)
        total_children: Total number of children
        radius: Distance from parent (default 280px)
        
    Returns:
        Tuple of (x, y) coordinates for child card
    """
    import math
    
    # Convert to float in case they're strings from database
    parent_x = float(parent_x)
    parent_y = float(parent_y)
    radius = float(radius)
    
    # Calculate angle for this child
    angle = (2 * math.pi * child_index) / total_children
    
    # Calculate position
    x = parent_x + math.cos(angle) * radius
    y = parent_y + math.sin(angle) * radius
    
    return (x, y)
