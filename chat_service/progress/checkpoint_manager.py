"""
Checkpoint Manager

Manages operation checkpoints for recovery from interruptions.
Stores checkpoints in database and provides resume functionality.
"""

import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


class OperationState(Enum):
    """Operation state enum"""
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CheckpointManager:
    """
    Manages operation checkpoints for recovery.
    
    Features:
    - Save/load checkpoints to/from database
    - Detect incomplete operations
    - Resume from last checkpoint
    - Clean up completed checkpoints
    """
    
    def __init__(self, db_connection=None):
        """
        Initialize checkpoint manager.
        
        Args:
            db_connection: Database connection (optional, will use default if not provided)
        """
        self.db = db_connection
        logger.info("CheckpointManager initialized")
    
    def save_checkpoint(self, checkpoint_data: Dict[str, Any]) -> bool:
        """
        Save checkpoint to database.
        
        Args:
            checkpoint_data: Checkpoint data from ProgressTracker
            
        Returns:
            True if saved successfully
        """
        try:
            operation_id = checkpoint_data["operation_id"]
            
            # Prepare checkpoint record
            checkpoint_record = {
                "operation_id": operation_id,
                "operation_type": checkpoint_data["operation_type"],
                "canvas_id": checkpoint_data.get("canvas_id"),
                "session_id": checkpoint_data.get("session_id"),
                "current_step": checkpoint_data["current_step"],
                "total_steps": checkpoint_data["total_steps"],
                "progress": checkpoint_data["progress"],
                "state": json.dumps({
                    "step_name": checkpoint_data["current_step_name"],
                    "message": checkpoint_data["message"],
                    "cards_created": checkpoint_data["cards_created"],
                    "start_time": checkpoint_data["start_time"],
                    "last_update_time": checkpoint_data["last_update_time"]
                }),
                "cards_created": checkpoint_data["cards_created"],
                "updated_at": datetime.now().isoformat()
            }
            
            # Save to database (INSERT or UPDATE)
            self._upsert_checkpoint(checkpoint_record)
            
            logger.debug(f"Checkpoint saved: {operation_id} ({checkpoint_data['progress']:.0%})")
            return True
            
        except Exception as e:
            logger.error(f"Error saving checkpoint: {e}", exc_info=True)
            return False
    
    def load_checkpoint(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """
        Load checkpoint from database.
        
        Args:
            operation_id: Operation ID to load
            
        Returns:
            Checkpoint data or None if not found
        """
        try:
            checkpoint = self._get_checkpoint_from_db(operation_id)
            
            if not checkpoint:
                logger.debug(f"No checkpoint found for operation: {operation_id}")
                return None
            
            # Parse state JSON
            state = json.loads(checkpoint["state"])
            
            # Reconstruct checkpoint data
            checkpoint_data = {
                "operation_id": checkpoint["operation_id"],
                "operation_type": checkpoint["operation_type"],
                "canvas_id": checkpoint["canvas_id"],
                "session_id": checkpoint["session_id"],
                "current_step": checkpoint["current_step"],
                "total_steps": checkpoint["total_steps"],
                "progress": checkpoint["progress"],
                "current_step_name": state["step_name"],
                "message": state["message"],
                "cards_created": checkpoint["cards_created"],
                "start_time": state["start_time"],
                "last_update_time": state["last_update_time"]
            }
            
            logger.info(f"Checkpoint loaded: {operation_id}")
            return checkpoint_data
            
        except Exception as e:
            logger.error(f"Error loading checkpoint: {e}", exc_info=True)
            return None
    
    def get_incomplete_operations(
        self,
        canvas_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all incomplete operations.
        
        Args:
            canvas_id: Filter by canvas ID (optional)
            session_id: Filter by session ID (optional)
            
        Returns:
            List of incomplete operation checkpoints
        """
        try:
            checkpoints = self._query_incomplete_checkpoints(canvas_id, session_id)
            
            incomplete_ops = []
            for checkpoint in checkpoints:
                state = json.loads(checkpoint["state"])
                
                incomplete_ops.append({
                    "operation_id": checkpoint["operation_id"],
                    "operation_type": checkpoint["operation_type"],
                    "canvas_id": checkpoint["canvas_id"],
                    "progress": checkpoint["progress"],
                    "message": state["message"],
                    "cards_created": len(checkpoint["cards_created"]),
                    "last_update": checkpoint["updated_at"]
                })
            
            logger.info(f"Found {len(incomplete_ops)} incomplete operations")
            return incomplete_ops
            
        except Exception as e:
            logger.error(f"Error getting incomplete operations: {e}", exc_info=True)
            return []
    
    def delete_checkpoint(self, operation_id: str) -> bool:
        """
        Delete checkpoint from database.
        
        Args:
            operation_id: Operation ID to delete
            
        Returns:
            True if deleted successfully
        """
        try:
            self._delete_checkpoint_from_db(operation_id)
            logger.info(f"Checkpoint deleted: {operation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting checkpoint: {e}", exc_info=True)
            return False
    
    def cleanup_old_checkpoints(self, days: int = 7) -> int:
        """
        Clean up checkpoints older than specified days.
        
        Args:
            days: Delete checkpoints older than this many days
            
        Returns:
            Number of checkpoints deleted
        """
        try:
            deleted_count = self._delete_old_checkpoints(days)
            logger.info(f"Cleaned up {deleted_count} old checkpoints")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up checkpoints: {e}", exc_info=True)
            return 0
    
    # Database operations (to be implemented with actual DB connection)
    
    def _upsert_checkpoint(self, checkpoint_record: Dict[str, Any]):
        """
        Insert or update checkpoint in database.
        
        Args:
            checkpoint_record: Checkpoint record to save
        """
        # TODO: Implement actual database upsert
        # For now, store in memory (will be replaced with PostgreSQL)
        if not hasattr(self, '_checkpoints'):
            self._checkpoints = {}
        
        self._checkpoints[checkpoint_record["operation_id"]] = checkpoint_record
        logger.debug(f"Checkpoint stored in memory: {checkpoint_record['operation_id']}")
    
    def _get_checkpoint_from_db(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get checkpoint from database.
        
        Args:
            operation_id: Operation ID
            
        Returns:
            Checkpoint record or None
        """
        # TODO: Implement actual database query
        # For now, retrieve from memory
        if not hasattr(self, '_checkpoints'):
            return None
        
        return self._checkpoints.get(operation_id)
    
    def _query_incomplete_checkpoints(
        self,
        canvas_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query incomplete checkpoints from database.
        
        Args:
            canvas_id: Filter by canvas ID
            session_id: Filter by session ID
            
        Returns:
            List of checkpoint records
        """
        # TODO: Implement actual database query
        # For now, filter from memory
        if not hasattr(self, '_checkpoints'):
            return []
        
        checkpoints = []
        for checkpoint in self._checkpoints.values():
            # Filter by progress < 1.0 (incomplete)
            if checkpoint["progress"] >= 1.0:
                continue
            
            # Apply filters
            if canvas_id and checkpoint.get("canvas_id") != canvas_id:
                continue
            
            if session_id and checkpoint.get("session_id") != session_id:
                continue
            
            checkpoints.append(checkpoint)
        
        return checkpoints
    
    def _delete_checkpoint_from_db(self, operation_id: str):
        """
        Delete checkpoint from database.
        
        Args:
            operation_id: Operation ID to delete
        """
        # TODO: Implement actual database delete
        # For now, delete from memory
        if hasattr(self, '_checkpoints') and operation_id in self._checkpoints:
            del self._checkpoints[operation_id]
            logger.debug(f"Checkpoint deleted from memory: {operation_id}")
    
    def _delete_old_checkpoints(self, days: int) -> int:
        """
        Delete checkpoints older than specified days.
        
        Args:
            days: Age threshold in days
            
        Returns:
            Number of checkpoints deleted
        """
        # TODO: Implement actual database delete with date filter
        # For now, return 0
        return 0


# Global checkpoint manager instance
_checkpoint_manager = None


def get_checkpoint_manager() -> CheckpointManager:
    """
    Get global checkpoint manager instance.
    
    Returns:
        CheckpointManager instance
    """
    global _checkpoint_manager
    if _checkpoint_manager is None:
        _checkpoint_manager = CheckpointManager()
    return _checkpoint_manager
