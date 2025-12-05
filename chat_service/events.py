"""
Simple Event System for Via Canvas

Lightweight event emitter for canvas changes. Used primarily by the
Background Intelligence Agent to react to card creation/updates.

Supports both synchronous and asynchronous event handlers.
"""

import logging
import asyncio
from typing import Callable, Dict, List

logger = logging.getLogger(__name__)


class CanvasEventEmitter:
    """
    Lightweight event system for canvas changes.
    
    Supports basic pub/sub pattern for event-driven processing.
    Used by Background Intelligence Agent to react to canvas events.
    
    Supports both sync and async callbacks - async callbacks are
    executed as fire-and-forget tasks for true background processing.
    """
    
    def __init__(self):
        """Initialize event emitter with empty listeners"""
        self.listeners: Dict[str, List[Callable]] = {}
        logger.info("CanvasEventEmitter initialized")
    
    def on(self, event_type: str, callback: Callable):
        """
        Register event listener
        
        Args:
            event_type: Type of event to listen for (e.g., 'card_created')
            callback: Function to call when event is emitted (can be sync or async)
        """
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        
        self.listeners[event_type].append(callback)
        callback_type = "async" if asyncio.iscoroutinefunction(callback) else "sync"
        logger.info(f"Registered {callback_type} listener for event: {event_type}")
    
    def emit(self, event_type: str, data: dict):
        """
        Emit event to all registered listeners.
        
        Synchronous callbacks are called immediately.
        Asynchronous callbacks are scheduled as fire-and-forget tasks.
        
        Args:
            event_type: Type of event to emit
            data: Event data to pass to listeners
        """
        if event_type not in self.listeners:
            logger.debug(f"No listeners for event: {event_type}")
            return
        
        logger.info(f"Emitting event: {event_type} to {len(self.listeners[event_type])} listeners")
        
        for callback in self.listeners[event_type]:
            try:
                # Check if callback is async
                if asyncio.iscoroutinefunction(callback):
                    # Fire and forget - don't block on async callbacks
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            # Create task in existing loop
                            asyncio.create_task(callback(data))
                            logger.debug(f"Scheduled async callback for {event_type}")
                        else:
                            # No running loop, run in new loop
                            asyncio.run(callback(data))
                    except RuntimeError:
                        # No event loop, create one
                        asyncio.run(callback(data))
                else:
                    # Synchronous callback - call immediately
                    callback(data)
            except Exception as e:
                logger.error(f"Error in event listener for {event_type}: {e}", exc_info=True)
    
    def off(self, event_type: str, callback: Callable):
        """
        Remove event listener
        
        Args:
            event_type: Type of event
            callback: Callback function to remove
        """
        if event_type in self.listeners:
            try:
                self.listeners[event_type].remove(callback)
                logger.info(f"Removed listener for event: {event_type}")
            except ValueError:
                logger.warning(f"Callback not found for event: {event_type}")
    
    def clear(self, event_type: str = None):
        """
        Clear all listeners for an event type, or all listeners if no type specified
        
        Args:
            event_type: Optional event type to clear. If None, clears all.
        """
        if event_type:
            if event_type in self.listeners:
                self.listeners[event_type] = []
                logger.info(f"Cleared all listeners for event: {event_type}")
        else:
            self.listeners = {}
            logger.info("Cleared all event listeners")
    
    def listener_count(self, event_type: str) -> int:
        """
        Get number of listeners for an event type
        
        Args:
            event_type: Event type to check
            
        Returns:
            Number of registered listeners
        """
        return len(self.listeners.get(event_type, []))


# Global event emitter instance
canvas_events = CanvasEventEmitter()


# Event type constants
class CanvasEvents:
    """Constants for canvas event types"""
    CARD_CREATED = 'card_created'
    CARD_UPDATED = 'card_updated'
    CARD_DELETED = 'card_deleted'
    CANVAS_OPENED = 'canvas_opened'
    CONNECTION_CREATED = 'connection_created'
    CONNECTION_DELETED = 'connection_deleted'
    
    # Progress tracking events
    PROGRESS_UPDATE = 'progress_update'
    OPERATION_COMPLETE = 'operation_complete'
    OPERATION_FAILED = 'operation_failed'
    OPERATION_CANCELLED = 'operation_cancelled'
    INCOMPLETE_OPERATIONS_FOUND = 'incomplete_operations_found'
