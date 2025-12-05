"""
Knowledge Graph Agent - Canvas Organization and Relationships

Specialized agent for graph operations, card relationships,
and canvas organization.
"""

import logging
from strands import Agent, tool

# Import graph tools
from tools.canvas_tools import (
    find_similar_cards,
    categorize_content,
    detect_conflicts,
    merge_cards,
    get_merge_preview,
    grow_card_content
)
from tools.graph_tools import (
    suggest_card_placement,
    create_intelligent_connections
)

logger = logging.getLogger(__name__)

# Import centralized prompts
from prompts import PromptTemplates


@tool
def knowledge_graph_agent(user_query: str, canvas_id: str):
    """
    Specialized agent for graph operations and canvas organization.
    
    Use this agent when the user wants to:
    - Find similar or related cards
    - Detect duplicates or conflicts
    - Organize the canvas
    - Auto-categorize content
    - Grow/expand cards with key concepts
    - Suggest optimal card placement
    - Create intelligent connections between cards
    - Merge duplicate cards
    
    Args:
        user_query: The user's graph operation request
        canvas_id: Canvas ID to operate on
        
    Returns:
        Graph operation results as string
    """
    from .model_provider import get_nvidia_nim_model
    
    logger.info(f"Knowledge graph agent processing: {user_query[:50]}...")
    
    # Get model instance
    model = get_nvidia_nim_model()
    
    # Assign graph intelligence tools to this agent
    tools = [
        # Similarity and search
        find_similar_cards,
        
        # Intelligent placement and connections
        suggest_card_placement,
        create_intelligent_connections,
        
        # Content organization
        categorize_content,
        grow_card_content,
        
        # Conflict detection and resolution
        detect_conflicts,
        get_merge_preview,
        merge_cards
    ]
    
    # Create agent with graph tools
    agent = Agent(
        system_prompt=PromptTemplates.knowledge_graph_system_prompt(),
        model=model,
        tools=tools
    )
    
    # Add context
    query_with_context = f"Canvas ID: {canvas_id}\n\nGraph Operation: {user_query}"
    
    # Get response
    response = agent(query_with_context)
    
    logger.info("Knowledge graph agent completed")
    return str(response)
