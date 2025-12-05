"""
Via Canvas Multi-Agent System

Implements specialized agents using Strands "Agents as Tools" pattern.
"""

from .orchestrator import CanvasOrchestrator
from .chat_agent import chat_agent
from .content_extraction_agent import content_extraction_agent
from .knowledge_graph_agent import knowledge_graph_agent
from .learning_assistant_agent import learning_assistant_agent
from .background_intelligence_agent import BackgroundIntelligenceAgent

__all__ = [
    'CanvasOrchestrator',
    'chat_agent',
    'content_extraction_agent',
    'knowledge_graph_agent',
    'learning_assistant_agent',
    'BackgroundIntelligenceAgent',
]
