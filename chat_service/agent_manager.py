"""
Agent Manager for Via Canvas AI Service

Manages the orchestrator and background intelligence agent.
Updated to use the new multi-agent architecture.
"""

import logging
from typing import AsyncGenerator, Optional, List
from session_manager import SessionManager
from agents.orchestrator import CanvasOrchestrator
from agents.background_intelligence_agent import BackgroundIntelligenceAgent
from config import settings

logger = logging.getLogger(__name__)


class AgentManager:
    """
    Manages the orchestrator and background intelligence agent.
    
    Uses the new multi-agent architecture with specialized agents.
    """
    
    def __init__(self, session_manager: SessionManager):
        """
        Initialize AgentManager with orchestrator and background agent.
        
        Args:
            session_manager: SessionManager instance for conversation history
        """
        if not session_manager:
            raise ValueError("session_manager is required for AgentManager")
        
        self.session_manager = session_manager
        self.orchestrator = None
        self.background_agent = None
        
        logger.info("AgentManager initializing...")
        
        # Create agents
        self.create_agents()
    
    def create_agents(self):
        """
        Create orchestrator and background intelligence agent.
        
        Initializes the multi-agent system with:
        - Orchestrator for routing user requests
        - Background Intelligence Agent for automatic actions
        """
        try:
            logger.info("Creating multi-agent system...")
            
            # Validate API key
            if not settings.nvidia_nim_api_key:
                logger.error("NVIDIA_NIM_API_KEY not set! Agent creation failed.")
                self.orchestrator = None
                self.background_agent = None
                return
            
            # Create orchestrator
            logger.info("Creating CanvasOrchestrator...")
            self.orchestrator = CanvasOrchestrator(session_manager=self.session_manager)
            
            # Create background intelligence agent
            logger.info("Creating BackgroundIntelligenceAgent...")
            self.background_agent = BackgroundIntelligenceAgent()
            
            logger.info("✅ Multi-agent system created successfully")
            logger.info(f"   Model: {settings.nvidia_nim_model}")
            logger.info(f"   Temperature: {settings.nvidia_nim_temperature}")
            logger.info(f"   Max tokens: {settings.nvidia_nim_max_tokens}")
            logger.info(f"   Orchestrator: Active with 4 specialist agents")
            logger.info(f"   Background Agent: Active and listening for events")
            
        except Exception as e:
            logger.error(f"❌ Error creating agents: {e}", exc_info=True)
            self.orchestrator = None
            self.background_agent = None
    
    async def stream_async(
        self,
        message: str,
        session_id: Optional[str] = None,
        canvas_id: Optional[str] = None,
        files: Optional[List[str]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream responses from orchestrator
        
        Args:
            message: User message
            session_id: Optional session ID
            canvas_id: Optional canvas ID for context
            files: Optional list of file paths
            
        Yields:
            SSE formatted event strings
        """
        if not self.orchestrator:
            error_event = self.format_sse({
                "type": "error",
                "message": "Orchestrator not available. Please check NVIDIA_NIM_API_KEY configuration."
            })
            yield error_event
            return
        
        try:
            logger.info(f"Streaming response for session: {session_id}, canvas: {canvas_id}")
            
            # Import stream processor
            from stream_event_processor import StreamEventProcessor
            stream_processor = StreamEventProcessor()
            
            # Process stream with orchestrator
            async for event in stream_processor.process_stream(
                self.orchestrator.agent,  # Use orchestrator's agent
                message,
                files=files,
                session_id=session_id,
                canvas_id=canvas_id
            ):
                yield event
                
        except Exception as e:
            logger.error(f"Stream error: {e}", exc_info=True)
            error_event = self.format_sse({
                "type": "error",
                "message": f"Stream error: {str(e)}"
            })
            yield error_event
    
    def format_sse(self, event: dict) -> str:
        """
        Format event as Server-Sent Event
        
        Args:
            event: Event dictionary
            
        Returns:
            SSE formatted string
        """
        import json
        event_type = event.get('type', 'message')
        return f"event: {event_type}\ndata: {json.dumps(event)}\n\n"
    
    def is_available(self) -> bool:
        """
        Check if orchestrator is available
        
        Returns:
            True if orchestrator is ready, False otherwise
        """
        return self.orchestrator is not None
    
    def recreate_agents(self):
        """
        Recreate agents with fresh configuration
        
        Useful for reloading configuration or recovering from errors.
        """
        logger.info("Recreating agents...")
        
        # Cleanup background agent
        if self.background_agent:
            self.background_agent.unsubscribe()
        
        self.orchestrator = None
        self.background_agent = None
        self.create_agents()


# Global agent manager instance
_agent_manager_instance = None


def get_agent_manager(session_manager: SessionManager) -> AgentManager:
    """
    Get the global agent manager instance
    
    Args:
        session_manager: SessionManager instance
        
    Returns:
        AgentManager instance
    """
    global _agent_manager_instance
    if _agent_manager_instance is None:
        _agent_manager_instance = AgentManager(session_manager)
    return _agent_manager_instance
