"""
Unit tests for SessionManager
Tests session creation, message storage, and cleanup functionality.
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import json

# Import the SessionManager class
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../chat_service'))

from session_manager import SessionManager


class TestSessionManager:
    """Test cases for SessionManager class"""
    
    def setup_method(self):
        """Set up test fixtures before each test method"""
        self.session_manager = SessionManager()
    
    def test_get_or_create_session_new_session(self):
        """Test creating a new session when none exists"""
        # Arrange
        canvas_id = "canvas_123"
        
        # Act
        session_id = self.session_manager.get_or_create_session(None, canvas_id)
        
        # Assert
        assert session_id is not None
        assert session_id.startswith("session_")
        assert canvas_id in str(self.session_manager.get_session_info(session_id))
    
    def test_get_or_create_session_existing_session(self):
        """Test retrieving an existing session"""
        # Arrange
        canvas_id = "canvas_123"
        existing_session_id = self.session_manager.get_or_create_session(None, canvas_id)
        
        # Act
        session_id = self.session_manager.get_or_create_session(existing_session_id, canvas_id)
        
        # Assert
        assert session_id == existing_session_id
    
    def test_add_message_user(self):
        """Test adding a user message to session"""
        # Arrange
        session_id = self.session_manager.get_or_create_session(None, "canvas_123")
        role = "user"
        content = "What nodes do I have?"
        
        # Act
        self.session_manager.add_message(session_id, role, content)
        
        # Assert
        messages = self.session_manager.get_messages(session_id)
        assert len(messages) == 1
        assert messages[0]["role"] == role
        assert messages[0]["content"] == content
    
    def test_add_message_assistant(self):
        """Test adding an assistant message"""
        # Arrange
        session_id = self.session_manager.get_or_create_session(None, "canvas_123")
        role = "assistant"
        content = "I found 3 nodes in your canvas."
        
        # Act
        self.session_manager.add_message(session_id, role, content)
        
        # Assert
        messages = self.session_manager.get_messages(session_id)
        assert len(messages) == 1
        assert messages[0]["role"] == role
        assert messages[0]["content"] == content
        assert "timestamp" in messages[0]
    
    def test_get_session_messages(self):
        """Test retrieving messages for a session"""
        # Arrange
        session_id = self.session_manager.get_or_create_session(None, "canvas_123")
        self.session_manager.add_message(session_id, "user", "Hello")
        self.session_manager.add_message(session_id, "assistant", "Hi there!")
        
        # Act
        messages = self.session_manager.get_messages(session_id)
        
        # Assert
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"
    
    def test_cleanup_inactive_sessions(self):
        """Test cleaning up old inactive sessions"""
        # Arrange
        session_id = self.session_manager.get_or_create_session(None, "canvas_123")
        
        # Manually set last_activity to 25 hours ago
        self.session_manager.sessions[session_id]['last_activity'] = datetime.now() - timedelta(hours=25)
        
        # Act
        deleted_count = self.session_manager.cleanup_inactive_sessions(hours=24)
        
        # Assert
        assert deleted_count == 1
        assert session_id not in self.session_manager.sessions
    
    def test_clear_session(self):
        """Test clearing a session"""
        # Arrange
        session_id = self.session_manager.get_or_create_session(None, "canvas_123")
        self.session_manager.add_message(session_id, "user", "Test")
        
        # Act
        self.session_manager.clear_session(session_id)
        
        # Assert
        assert session_id not in self.session_manager.sessions
    
    def test_get_session_count(self):
        """Test getting total session count"""
        # Arrange
        self.session_manager.get_or_create_session(None, "canvas_1")
        self.session_manager.get_or_create_session(None, "canvas_2")
        
        # Act
        count = self.session_manager.get_session_count()
        
        # Assert
        assert count == 2
    
    def test_get_session_info(self):
        """Test getting session information"""
        # Arrange
        canvas_id = "canvas_123"
        session_id = self.session_manager.get_or_create_session(None, canvas_id)
        
        # Act
        info = self.session_manager.get_session_info(session_id)
        
        # Assert
        assert info is not None
        assert info["id"] == session_id
        assert info["canvas_id"] == canvas_id
        assert "created_at" in info
        assert "last_activity" in info
    
    def test_generate_session_id_uniqueness(self):
        """Test that generated session IDs are unique"""
        # Act
        id1 = self.session_manager.generate_session_id()
        id2 = self.session_manager.generate_session_id()
        
        # Assert
        assert id1 != id2
        assert id1.startswith("session_")
        assert id2.startswith("session_")
    
    def test_add_message_to_nonexistent_session(self):
        """Test adding message to non-existent session"""
        # Arrange
        fake_session_id = "session_nonexistent"
        
        # Act
        self.session_manager.add_message(fake_session_id, "user", "Test")
        
        # Assert
        messages = self.session_manager.get_messages(fake_session_id)
        assert len(messages) == 0
    
    def test_get_model_config(self):
        """Test getting model configuration"""
        # Act
        config = self.session_manager.get_model_config()
        
        # Assert
        assert "model_id" in config
        assert "temperature" in config
        assert "max_tokens" in config
    
    def test_get_active_system_prompt(self):
        """Test getting system prompt"""
        # Act
        prompt = self.session_manager.get_active_system_prompt()
        
        # Assert
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "Via Canvas Assistant" in prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
