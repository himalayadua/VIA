"""
Background Intelligence Agent - Automatic Actions

Runs automatic actions in response to canvas events.
Subscribes to card creation/update events and performs intelligent analysis.

Uses async event handlers for true background processing without blocking
the main card creation/update operations.
"""

import logging
import asyncio
from strands import Agent
from typing import Dict
from .model_provider import get_nvidia_nim_model
from events import canvas_events, CanvasEvents

# Import background tools
from tools.background_tools import (
    generate_learning_questions,
    extract_action_items,
    detect_deadlines,
    extract_entities,
    suggest_merge_duplicates,
    detect_contradictions
)

logger = logging.getLogger(__name__)

# Import centralized prompts
from prompts import PromptTemplates


class BackgroundIntelligenceAgent:
    """
    Background agent that automatically enhances canvas content.
    
    Subscribes to canvas events and runs automatic actions like:
    - Generating learning questions
    - Extracting todos and deadlines
    - Identifying entities
    - Detecting duplicates and contradictions
    """
    
    def __init__(self):
        """Initialize background intelligence agent"""
        self.model = get_nvidia_nim_model()
        
        # Assign background intelligence tools
        tools = [
            generate_learning_questions,
            extract_action_items,
            detect_deadlines,
            extract_entities,
            suggest_merge_duplicates,
            detect_contradictions
        ]
        
        # Create agent with background tools
        self.agent = Agent(
            system_prompt=PromptTemplates.background_intelligence_system_prompt(),
            model=self.model,
            tools=tools
        )
        
        # Subscribe to canvas events
        self._subscribe_to_events()
        
        logger.info("✅ BackgroundIntelligenceAgent initialized with 6 tools and subscribed to events")
    
    def _subscribe_to_events(self):
        """Subscribe to canvas events with async handlers"""
        canvas_events.on(CanvasEvents.CARD_CREATED, self.on_card_created)
        canvas_events.on(CanvasEvents.CARD_UPDATED, self.on_card_updated)
        logger.info("Subscribed to card_created and card_updated events (async handlers)")
    
    async def on_card_created(self, event_data: Dict):
        """
        Handle card creation event asynchronously (fire-and-forget).
        
        This runs in the background without blocking the main operation.
        
        Args:
            event_data: Event data containing card_id, canvas_id, content
        """
        try:
            card_id = event_data.get('card_id')
            canvas_id = event_data.get('canvas_id')
            content = event_data.get('content', '')
            
            logger.info(f"🔄 Background agent queued processing for card: {card_id}")
            
            # Build analysis query
            query = f"""Analyze this new card and perform relevant automatic actions:

Card ID: {card_id}
Canvas ID: {canvas_id}
Content: {content}

Decide which automatic actions would be most valuable:
- Should we generate learning questions?
- Are there action items to extract?
- Any deadlines to detect?
- Important entities to extract?
- Potential duplicates to flag?
- Any contradictions with existing content?

Be selective - only add truly valuable enhancements."""
            
            # Process with agent asynchronously using stream_async
            # This allows the agent to work in the background without blocking
            async for event in self.agent.stream_async(query):
                # Process events but don't block the main thread
                if event.get("complete"):
                    logger.info(f"✅ Background processing completed for card {card_id}")
                    break
            
        except Exception as e:
            logger.error(f"❌ Error in background card processing: {e}", exc_info=True)
    
    async def on_card_updated(self, event_data: Dict):
        """
        Handle card update event asynchronously.
        
        Args:
            event_data: Event data containing card_id, canvas_id, content
        """
        try:
            card_id = event_data.get('card_id')
            
            logger.info(f"🔄 Background agent queued processing for updated card: {card_id}")
            
            # For updates, we might want different logic
            # For now, treat similar to creation but with lower priority
            await self.on_card_created(event_data)
            
        except Exception as e:
            logger.error(f"❌ Error in background card update processing: {e}", exc_info=True)
    
    def unsubscribe(self):
        """Unsubscribe from all events (useful for cleanup)"""
        canvas_events.off(CanvasEvents.CARD_CREATED, self.on_card_created)
        canvas_events.off(CanvasEvents.CARD_UPDATED, self.on_card_updated)
        logger.info("Unsubscribed from canvas events")
