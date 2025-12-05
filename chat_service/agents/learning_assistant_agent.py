"""
Learning Assistant Agent - Educational Features

Specialized agent for educational features and knowledge enhancement.
Handles knowledge gaps, simplification, examples, and learning paths.
"""

import logging
from strands import Agent, tool

logger = logging.getLogger(__name__)

# Import centralized prompts
from prompts import PromptTemplates

# Import all learning tools
from tools.learning_tools import (
    # Phase 1: Core Learning Tools
    simplify_explanation,
    find_real_examples,
    analyze_knowledge_gaps,
    create_action_plan,
    talk_to_canvas,
    
    # Phase 2: Research & Critical Thinking Tools
    find_academic_sources,
    find_counterpoints,
    update_information,
    find_surprising_connections,
    comprehensive_learn
)

# Import deep research tool
from tools.deep_research_tool import deep_research


@tool
def learning_assistant_agent(user_query: str, canvas_id: str):
    """
    Specialized agent for educational features and learning enhancement.
    
    Use this agent when the user wants to:
    - Simplify complex concepts (ELI5)
    - Find real-world examples and applications
    - Analyze knowledge gaps (prerequisites and advanced topics)
    - Create action plans from knowledge
    - Have conversational knowledge queries
    - Find academic sources and research papers
    - Find counter-arguments and alternative perspectives
    - Update outdated information
    - Discover surprising connections between topics
    - Create comprehensive learning clusters
    - Conduct deep research with multi-stage analysis (NEW)
    
    Args:
        user_query: The user's learning request
        canvas_id: Canvas ID for context
        
    Returns:
        Learning assistance results as string
    """
    from .model_provider import get_nvidia_nim_model
    
    logger.info(f"Learning assistant agent processing: {user_query[:50]}...")
    
    # Get model instance
    model = get_nvidia_nim_model()
    
    # All learning tools (11 total)
    tools = [
        # Phase 1: Core Learning Tools (5 tools)
        simplify_explanation,      # ELI5 simplification with analogies
        find_real_examples,        # Real-world applications and use cases
        analyze_knowledge_gaps,    # Find missing prerequisites/advanced topics
        create_action_plan,        # Convert knowledge to implementation steps
        talk_to_canvas,            # Conversational knowledge queries
        
        # Phase 2: Research & Critical Thinking Tools (6 tools)
        find_academic_sources,     # Academic papers (hybrid LLM + arXiv)
        find_counterpoints,        # Counter-arguments and alternatives
        update_information,        # Refresh outdated content
        find_surprising_connections,  # Discover non-obvious connections
        comprehensive_learn,       # Complete learning workflow
        deep_research              # Multi-stage deep research (NEW)
    ]
    
    # Create agent with all learning tools
    agent = Agent(
        system_prompt=PromptTemplates.learning_assistant_system_prompt(),
        model=model,
        tools=tools
    )
    
    # Add context
    query_with_context = f"Canvas ID: {canvas_id}\n\nLearning Request: {user_query}"
    
    # Get response
    response = agent(query_with_context)
    
    logger.info("Learning assistant agent completed")
    return str(response)
