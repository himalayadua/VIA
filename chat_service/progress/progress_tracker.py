"""
Progress Tracker

Tracks progress of long-running operations and emits real-time updates via SSE.
Integrates with checkpoint system for recovery.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from events import canvas_events

logger = logging.getLogger(__name__)


class ProgressTracker:
    """
    Tracks progress of long-running operations.
    
    Features:
    - Real-time progress updates via SSE
    - Automatic checkpoint saving
    - Time estimation
    - Cancellation support
    """
    
    def __init__(
        self,
        operation_id: Optional[str] = None,
        operation_type: str = "generic",
        total_steps: int = 1,
        canvas_id: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """
        Initialize progress tracker.
        
        Args:
            operation_id: Unique operation ID (generated if not provided)
            operation_type: Type of operation (e.g., "url_extraction", "grow_card")
            total_steps: Total number of steps in operation
            canvas_id: Canvas ID for context
            session_id: Session ID for SSE routing
        """
        self.operation_id = operation_id or str(uuid.uuid4())
        self.operation_type = operation_type
        self.total_steps = max(1, total_steps)
        self.canvas_id = canvas_id
        self.session_id = session_id
        
        # Progress state
        self.current_step = 0
        self.current_step_name = ""
        self.progress = 0.0
        self.message = ""
        
        # Tracking data
        self.cards_created: List[str] = []
        self.start_time = datetime.now()
        self.last_checkpoint_time = datetime.now()
        self.last_update_time = datetime.now()
        
        # Cancellation
        self.is_cancelled = False
        self.can_cancel = True
        
        # Checkpoint settings
        self.checkpoint_interval_seconds = 30
        self.checkpoint_interval_cards = 10
        
        logger.info(f"ProgressTracker initialized: {self.operation_id} ({self.operation_type})")
    
    def update_progress(
        self,
        step_name: str,
        progress: float,
        message: str = "",
        cards_created: Optional[List[str]] = None
    ):
        """
        Update progress and emit SSE event.
        
        Args:
            step_name: Name of current step (e.g., "fetching", "parsing")
            progress: Progress value 0.0 to 1.0
            message: Optional progress message
            cards_created: Optional list of card IDs created in this step
        """
        if self.is_cancelled:
            logger.warning(f"Operation {self.operation_id} is cancelled, ignoring update")
            return
        
        # Update state
        self.current_step += 1
        self.current_step_name = step_name
        self.progress = max(0.0, min(1.0, progress))
        self.message = message
        self.last_update_time = datetime.now()
        
        # Track cards created
        if cards_created:
            self.cards_created.extend(cards_created)
        
        # Calculate estimated time
        estimated_time = self._estimate_time_remaining()
        
        # Emit progress event
        self._emit_progress_event(estimated_time)
        
        logger.debug(
            f"Progress update: {self.operation_id} - "
            f"{step_name} ({int(progress * 100)}%) - {message}"
        )
    
    def add_cards_created(self, card_ids: List[str]):
        """
        Add cards to the created list.
        
        Args:
            card_ids: List of card IDs that were created
        """
        self.cards_created.extend(card_ids)
        logger.debug(f"Added {len(card_ids)} cards to tracker. Total: {len(self.cards_created)}")
    
    def complete(self, final_message: str = "Operation completed successfully"):
        """
        Mark operation as complete.
        
        Args:
            final_message: Final completion message
        """
        self.progress = 1.0
        self.message = final_message
        self.current_step_name = "complete"
        
        # Emit final progress event
        self._emit_progress_event(estimated_time=0)
        
        # Emit completion event
        canvas_events.emit("operation_complete", {
            "operation_id": self.operation_id,
            "operation_type": self.operation_type,
            "canvas_id": self.canvas_id,
            "session_id": self.session_id,
            "cards_created": len(self.cards_created),
            "duration_seconds": (datetime.now() - self.start_time).total_seconds()
        })
        
        logger.info(
            f"Operation completed: {self.operation_id} - "
            f"{len(self.cards_created)} cards created in "
            f"{(datetime.now() - self.start_time).total_seconds():.1f}s"
        )
    
    def fail(self, error_message: str):
        """
        Mark operation as failed.
        
        Args:
            error_message: Error message
        """
        self.message = f"Error: {error_message}"
        
        # Emit error event
        canvas_events.emit("operation_failed", {
            "operation_id": self.operation_id,
            "operation_type": self.operation_type,
            "canvas_id": self.canvas_id,
            "session_id": self.session_id,
            "error": error_message,
            "cards_created": len(self.cards_created)
        })
        
        logger.error(f"Operation failed: {self.operation_id} - {error_message}")
    
    def cancel(self):
        """Mark operation as cancelled."""
        self.is_cancelled = True
        self.message = "Operation cancelled by user"
        
        # Emit cancellation event
        canvas_events.emit("operation_cancelled", {
            "operation_id": self.operation_id,
            "operation_type": self.operation_type,
            "canvas_id": self.canvas_id,
            "session_id": self.session_id,
            "cards_created": len(self.cards_created)
        })
        
        logger.info(f"Operation cancelled: {self.operation_id}")
    
    def should_save_checkpoint(self) -> bool:
        """
        Check if checkpoint should be saved.
        
        Returns:
            True if checkpoint should be saved
        """
        # Save every N seconds
        time_since_checkpoint = (datetime.now() - self.last_checkpoint_time).total_seconds()
        if time_since_checkpoint >= self.checkpoint_interval_seconds:
            return True
        
        # Save every N cards
        cards_since_checkpoint = len(self.cards_created) % self.checkpoint_interval_cards
        if cards_since_checkpoint == 0 and len(self.cards_created) > 0:
            return True
        
        return False
    
    def get_checkpoint_data(self) -> Dict[str, Any]:
        """
        Get current state for checkpoint.
        
        Returns:
            Dictionary with checkpoint data
        """
        return {
            "operation_id": self.operation_id,
            "operation_type": self.operation_type,
            "canvas_id": self.canvas_id,
            "session_id": self.session_id,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "progress": self.progress,
            "current_step_name": self.current_step_name,
            "message": self.message,
            "cards_created": self.cards_created,
            "start_time": self.start_time.isoformat(),
            "last_update_time": self.last_update_time.isoformat()
        }
    
    def _estimate_time_remaining(self) -> Optional[int]:
        """
        Estimate time remaining in seconds.
        
        Returns:
            Estimated seconds remaining, or None if cannot estimate
        """
        if self.progress <= 0:
            return None
        
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        if elapsed < 1:
            return None
        
        # Estimate based on progress
        estimated_total = elapsed / self.progress
        remaining = estimated_total - elapsed
        
        return max(0, int(remaining))
    
    def _emit_progress_event(self, estimated_time: Optional[int] = None):
        """
        Emit progress event via canvas events.
        
        Args:
            estimated_time: Estimated time remaining in seconds
        """
        event_data = {
            "operation_id": self.operation_id,
            "operation_type": self.operation_type,
            "step": self.current_step_name,
            "progress": self.progress,
            "message": self.message,
            "cards_created": len(self.cards_created),
            "can_cancel": self.can_cancel,
            "canvas_id": self.canvas_id,
            "session_id": self.session_id
        }
        
        if estimated_time is not None:
            event_data["estimated_time"] = estimated_time
        
        canvas_events.emit("progress_update", event_data)
