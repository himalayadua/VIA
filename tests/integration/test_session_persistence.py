"""
Integration Test: Session Persistence

Tests session persistence across page reloads:
1. Create session
2. Send messages
3. Simulate page reload
4. Verify session restoration
"""
import pytest
import requests
import json
import time
import psycopg2
from psycopg2.extras import RealDictCursor

# Test configuration
EXPRESS_API_URL = "http://localhost:3000/api/chat"
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'via_canvas_test',
    'user': 'viacanvas',
    'password': 'viacanvas_dev'
}


class TestSessionPersistence:
    """Integration tests for session persistence"""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown"""
        self.canvas_id = "test_canvas_" + str(int(time.time()))
        self.session_id = None
        
        yield
        
        self.cleanup_test_data()
    
    def cleanup_test_data(self):
        """Clean up test data"""
        try:
            if self.session_id:
                conn = psycopg2.connect(**DB_CONFIG)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM chat_messages WHERE session_id = %s", (self.session_id,))
                cursor.execute("DELETE FROM chat_sessions WHERE id = %s", (self.session_id,))
                conn.commit()
                cursor.close()
                conn.close()
        except Exception as e:
            print(f"Cleanup error: {e}")
    
    def test_session_creation_and_restoration(self):
        """Test creating session and restoring it"""
        # Step 1: Create session
        create_response = requests.post(
            f"{EXPRESS_API_URL}/session",
            json={"canvas_id": self.canvas_id}
        )
        
        assert create_response.status_code == 200
        session_data = create_response.json()
        self.session_id = session_data['session_id']
        
        # Step 2: Send messages
        msg_response = requests.post(
            f"{EXPRESS_API_URL}/stream",
            json={
                "message": "First message",
                "session_id": self.session_id,
                "canvas_id": self.canvas_id
            },
            stream=True,
            timeout=30
        )
        
        # Consume stream
        for _ in msg_response.iter_content(chunk_size=1024):
            pass
        
        time.sleep(1)
        
        # Step 3: Simulate page reload - get history
        history_response = requests.get(
            f"{EXPRESS_API_URL}/history/{self.session_id}"
        )
        
        # Assert: History is restored
        assert history_response.status_code == 200
        history = history_response.json()
        assert len(history['messages']) >= 1
        assert history['session_id'] == self.session_id
    
    def test_session_persistence_across_multiple_messages(self):
        """Test session persists across multiple messages"""
        # Send first message
        response1 = requests.post(
            f"{EXPRESS_API_URL}/stream",
            json={
                "message": "Message 1",
                "canvas_id": self.canvas_id
            },
            stream=True,
            timeout=30
        )
        
        self.session_id = response1.headers.get('x-session-id')
        for _ in response1.iter_content(chunk_size=1024):
            pass
        
        # Send second message with same session
        response2 = requests.post(
            f"{EXPRESS_API_URL}/stream",
            json={
                "message": "Message 2",
                "session_id": self.session_id,
                "canvas_id": self.canvas_id
            },
            stream=True,
            timeout=30
        )
        
        for _ in response2.iter_content(chunk_size=1024):
            pass
        
        # Send third message
        response3 = requests.post(
            f"{EXPRESS_API_URL}/stream",
            json={
                "message": "Message 3",
                "session_id": self.session_id,
                "canvas_id": self.canvas_id
            },
            stream=True,
            timeout=30
        )
        
        for _ in response3.iter_content(chunk_size=1024):
            pass
        
        time.sleep(1)
        
        # Get history
        history_response = requests.get(
            f"{EXPRESS_API_URL}/history/{self.session_id}"
        )
        
        history = history_response.json()
        user_messages = [m for m in history['messages'] if m['role'] == 'user']
        
        # Should have all 3 user messages
        assert len(user_messages) >= 3
    
    def test_session_id_header_propagation(self):
        """Test session ID is properly propagated via headers"""
        # Send message
        response = requests.post(
            f"{EXPRESS_API_URL}/stream",
            json={
                "message": "Test message",
                "canvas_id": self.canvas_id
            },
            stream=True,
            timeout=30
        )
        
        # Get session ID from header
        session_id_from_header = response.headers.get('x-session-id')
        assert session_id_from_header is not None
        
        self.session_id = session_id_from_header
        
        # Consume stream
        for _ in response.iter_content(chunk_size=1024):
            pass
        
        # Send another message with session ID in header
        response2 = requests.post(
            f"{EXPRESS_API_URL}/stream",
            headers={'X-Session-ID': session_id_from_header},
            json={
                "message": "Second message",
                "canvas_id": self.canvas_id
            },
            stream=True,
            timeout=30
        )
        
        # Should return same session ID
        session_id_from_header2 = response2.headers.get('x-session-id')
        assert session_id_from_header2 == session_id_from_header
    
    def test_session_cleanup(self):
        """Test inactive session cleanup"""
        # Create session
        response = requests.post(
            f"{EXPRESS_API_URL}/stream",
            json={
                "message": "Test message",
                "canvas_id": self.canvas_id
            },
            stream=True,
            timeout=30
        )
        
        self.session_id = response.headers.get('x-session-id')
        
        for _ in response.iter_content(chunk_size=1024):
            pass
        
        # Manually update last_activity to be old
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE chat_sessions SET last_activity = NOW() - INTERVAL '25 hours' WHERE id = %s",
            (self.session_id,)
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        # Trigger cleanup
        cleanup_response = requests.post(
            f"{EXPRESS_API_URL}/cleanup",
            json={"max_age_hours": 24}
        )
        
        assert cleanup_response.status_code == 200
        cleanup_data = cleanup_response.json()
        assert cleanup_data['deleted_count'] >= 1
        
        # Session should be deleted
        self.session_id = None  # Don't try to cleanup in teardown


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
