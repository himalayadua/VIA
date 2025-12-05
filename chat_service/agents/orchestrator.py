"""
Orchestrator Agent - Main Router

Routes user requests to specialized agents using the "Agents as Tools" pattern.
Maintains conversation context and coordinates multi-step operations.
"""

import logging
from strands import Agent
from typing import AsyncGenerator, Optional
from .model_provider import get_nvidia_nim_model
from .chat_agent import chat_agent
from .content_extraction_agent import content_extraction_agent
from .knowledge_graph_agent import knowledge_graph_agent
from .learning_assistant_agent import learning_assistant_agent

logger = logging.getLogger(__name__)

# Import centralized prompts
from prompts import PromptTemplates


class CanvasOrchestrator:
    """
    Main orchestrator that routes requests to specialized agents.
    
    Uses Strands "Agents as Tools" pattern where each specialist agent
    is registered as a callable tool.
    """
    
    def __init__(self, session_manager=None):
        """
        Initialize orchestrator with specialized agents.
        
        Args:
            session_manager: Optional session manager for conversation history
        """
        self.session_manager = session_manager
        self.model = get_nvidia_nim_model()
        
        # Create orchestrator with specialized agents as tools
        self.agent = Agent(
            system_prompt=PromptTemplates.orchestrator_system_prompt(),
            model=self.model,
            tools=[
                content_extraction_agent,
                knowledge_graph_agent,
                learning_assistant_agent,
                chat_agent
            ],
            session_manager=session_manager
        )
        
        logger.info("✅ CanvasOrchestrator initialized with 4 specialist agents")
    
    async def stream_async(
        self,
        message: str,
        session_id: Optional[str] = None,
        canvas_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream responses from orchestrator.
        
        Args:
            message: User message
            session_id: Optional session ID for conversation history
            canvas_id: Optional canvas ID for context
            
        Yields:
            Response chunks as strings
        """
        logger.info(f"Orchestrator streaming for session: {session_id}, canvas: {canvas_id}")
        
        # Add canvas context to message
        if canvas_id:
            context_message = f"Canvas ID: {canvas_id}\n\nUser Query: {message}"
        else:
            context_message = message
        
        try:
            # Stream from agent
            async for chunk in self.agent.stream_async(context_message):
                yield chunk
        except Exception as e:
            logger.error(f"Error in orchestrator stream: {e}", exc_info=True)
            yield f"Error: {str(e)}"
    
    def __call__(self, message: str, canvas_id: Optional[str] = None) -> str:
        """
        Synchronous call for non-streaming requests.
        
        Args:
            message: User message
            canvas_id: Optional canvas ID for context
            
        Returns:
            Response as string
        """
        logger.info(f"Orchestrator processing message for canvas: {canvas_id}")
        
        # Add canvas context
        if canvas_id:
            context_message = f"Canvas ID: {canvas_id}\n\nUser Query: {message}"
        else:
            context_message = message
        
        try:
            response = self.agent(context_message)
            return str(response)
        except Exception as e:
            logger.error(f"Error in orchestrator: {e}", exc_info=True)
            return f"Error processing request: {str(e)}"
