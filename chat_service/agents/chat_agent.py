"""
Chat Agent - General Conversation and Canvas Queries

Handles general conversation and basic canvas queries.
This is the existing agent functionality, now wrapped as a tool.
"""

import logging
from strands import Agent, tool
from typing import Optional

logger = logging.getLogger(__name__)

# Import centralized prompts
from prompts import PromptTemplates


@tool
def chat_agent(user_query: str, canvas_id: Optional[str] = None):
    """
    General conversation and canvas query agent.
    
    Use this agent when the user:
    - Asks general questions about their canvas
    - Wants to search canvas content
    - Needs an overview of their canvas
    - Has casual conversation
    - No specialized agent is needed
    
    Args:
        user_query: The user's question or request
        canvas_id: Optional canvas ID for context
        
    Returns:
        Agent response as string
    """
    from tool_manager import ToolManager
    from .model_provider import get_nvidia_nim_model
    
    logger.info(f"Chat agent processing query: {user_query[:50]}...")
    
    # Get model instance
    model = get_nvidia_nim_model()
    
    # Get canvas tools
    tool_manager = ToolManager()
    canvas_tools = tool_manager.get_canvas_tools()
    
    # Create agent with canvas tools
    agent = Agent(
        system_prompt=PromptTemplates.chat_agent_system_prompt(),
        model=model,
        tools=canvas_tools
    )
    
    # Add canvas context if provided
    if canvas_id:
        query_with_context = f"Canvas ID: {canvas_id}\n\nUser Query: {user_query}"
    else:
        query_with_context = user_query
    
    # Get response
    response = agent(query_with_context)
    
    logger.info("Chat agent completed processing")
    return str(response)
