"""
Session Manager for Via Canvas AI Service

Manages chat sessions and conversation history for Strands agent.
Implements the Strands session interface for compatibility.
"""

import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Session manager for Strands agent
    
    Manages in-memory session state and implements the Strands session interface.
    Actual message persistence is handled by Express.js backend in PostgreSQL.
    """
    
    def __init__(self):
        self.sessions: Dict[str, dict] = {}
        logger.info("SessionManager initialized")
    
    def get_or_create_session(
        self, 
        session_id: Optional[str] = None, 
        canvas_id: Optional[str] = None
    ) -> str:
        """
        Get or create session - returns session_id
        
        Args:
            session_id: Optional existing session ID
            canvas_id: Optional canvas ID to associate with session
            
        Returns:
            Session ID (existing or newly created)
        """
        if session_id and session_id in self.sessions:
            # Update last activity
            self.sessions[session_id]['last_activity'] = datetime.now()
            logger.debug(f"Retrieved existing session: {session_id}")
            return session_id
        
        # Create new session
        new_session_id = self.generate_session_id()
        self.sessions[new_session_id] = {
            'id': new_session_id,
            'canvas_id': canvas_id,
            'messages': [],
            'created_at': datetime.now(),
            'last_activity': datetime.now()
        }
        
        logger.info(f"Created new session: {new_session_id} (canvas: {canvas_id or 'none'})")
        return new_session_id
    
    def add_message(self, session_id: str, role: str, content: str):
        """
        Add message to session history
        
        Args:
            session_id: Session ID
            role: Message role (user, assistant, system)
            content: Message content
        """
        if session_id in self.sessions:
            self.sessions[session_id]['messages'].append({
                'role': role,
                'content': content,
                'timestamp': datetime.now()
            })
            self.sessions[session_id]['last_activity'] = datetime.now()
            logger.debug(f"Added {role} message to session {session_id}")
        else:
            logger.warning(f"Attempted to add message to non-existent session: {session_id}")
    
    def get_messages(self, session_id: str) -> List[dict]:
        """
        Get session messages
        
        Args:
            session_id: Session ID
            
        Returns:
            List of messages
        """
        return self.sessions.get(session_id, {}).get('messages', [])
    
    def clear_session(self, session_id: str):
        """
        Clear session from memory
        
        Args:
            session_id: Session ID to clear
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Cleared session: {session_id}")
        else:
            logger.warning(f"Attempted to clear non-existent session: {session_id}")
    
    def cleanup_inactive_sessions(self, max_age_hours: int = 24):
        """
        Remove inactive sessions
        
        Args:
            max_age_hours: Maximum age in hours before session is considered inactive
        """
        now = datetime.now()
        to_remove = []
        
        for session_id, session in self.sessions.items():
            age = now - session['last_activity']
            if age > timedelta(hours=max_age_hours):
                to_remove.append(session_id)
        
        for session_id in to_remove:
            del self.sessions[session_id]
        
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} inactive sessions")
        
        return len(to_remove)
    
    def generate_session_id(self) -> str:
        """
        Generate unique session ID (UUID format for PostgreSQL compatibility)
        
        Returns:
            Unique session ID in UUID format
        """
        return str(uuid.uuid4())
    
    def get_session_count(self) -> int:
        """
        Get total number of active sessions
        
        Returns:
            Number of active sessions
        """
        return len(self.sessions)
    
    def get_session_info(self, session_id: str) -> Optional[dict]:
        """
        Get session information
        
        Args:
            session_id: Session ID
            
        Returns:
            Session info dict or None if not found
        """
        return self.sessions.get(session_id)
    
    # Strands Agent interface methods
    @property
    def messages(self):
        """
        Get messages for current session (Strands interface)
        
        Note: This is a placeholder for Strands compatibility.
        Actual message history is managed per-session.
        """
        return []
    
    def get_model_config(self) -> dict:
        """
        Get model configuration (Strands interface)
        
        Returns:
            Model configuration dict
        """
        from config import settings
        
        return {
            "model_id": settings.nvidia_nim_model,
            "temperature": settings.nvidia_nim_temperature,
            "max_tokens": settings.nvidia_nim_max_tokens
        }
    
    def get_active_system_prompt(self) -> str:
        """
        Get active system prompt (Strands interface)
        
        Returns:
            System prompt string
        """
        return """You are Via Canvas Assistant, an AI helper for the Via Canvas mind-mapping application.

You have access to tools that let you search and analyze the user's canvas content:
- search_canvas_content: Search node content by text query
- get_canvas_titles: Get all node titles from the canvas
- get_canvas_tags: Extract unique tags from node content
- find_similar_nodes: Find semantically similar nodes

Use these tools to provide helpful, context-aware responses about the user's canvas.
Be concise and focus on helping users understand and organize their ideas."""
    
    def get_tool_config(self) -> dict:
        """
        Get tool configuration (Strands interface)
        
        Returns:
            Tool configuration dict
        """
        return {"tools": []}
    
    def has_config_changes(self) -> bool:
        """
        Check if configuration has changed (Strands interface)
        
        Returns:
            False (no dynamic config changes in our implementation)
        """
        return False
    
    def reset_config_change_flags(self):
        """
        Reset configuration change flags (Strands interface)
        """
        pass
    
    def register_hooks(self, hook_registry):
        """
        Register hooks with Strands agent (Strands interface)
        
        This method is required by Strands framework for hook registration.
        We don't use hooks in our implementation, so this is a no-op.
        
        Args:
            hook_registry: Strands hook registry
        """
        # No hooks to register in our implementation
        logger.debug("register_hooks called (no-op)")
        pass


# Global session manager instance
_session_manager_instance = None


def get_session_manager() -> SessionManager:
    """
    Get the global session manager instance
    
    Returns:
        SessionManager instance
    """
    global _session_manager_instance
    if _session_manager_instance is None:
        _session_manager_instance = SessionManager()
    return _session_manager_instance
