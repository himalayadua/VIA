"""
Integration Test: End-to-End Chat Flow

Tests the complete chat flow from frontend to backend:
1. Send message via API
2. Receive SSE streaming response
3. Verify message persistence in database
4. Verify session management
"""
import pytest
import requests
import json
import time
from typing import List, Dict
import psycopg2
from psycopg2.extras import RealDictCursor

# Test configuration
EXPRESS_API_URL = "http://localhost:3000/api/chat"
PYTHON_API_URL = "http://localhost:8000/chat"
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'via_canvas_test',
    'user': 'viacanvas',
    'password': 'viacanvas_dev'
}


class TestEndToEndChatFlow:
    """Integration tests for end-to-end chat flow"""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test"""
        # Setup: Create test canvas
        self.canvas_id = "test_canvas_" + str(int(time.time()))
        self.session_id = None
        self.test_messages = []
        
        yield
        
        # Teardown: Clean up test data
        self.cleanup_test_data()
    
    def cleanup_test_data(self):
        """Clean up test data from database"""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            # Delete test messages
            if self.session_id:
                cursor.execute(
                    "DELETE FROM chat_messages WHERE session_id = %s",
                    (self.session_id,)
                )
                cursor.execute(
                    "DELETE FROM chat_sessions WHERE id = %s",
                    (self.session_id,)
                )
            
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Cleanup error: {e}")
    
    def parse_sse_stream(self, response) -> List[Dict]:
        """Parse SSE stream from response"""
        events = []
        buffer = ""
        
        for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
            if chunk:
                buffer += chunk
                
                # Process complete events
                while "\n\n" in buffer:
                    event_text, buffer = buffer.split("\n\n", 1)
                    
                    # Parse event
                    event = {}
                    for line in event_text.split("\n"):
                        if line.startswith("event: "):
                            event['type'] = line[7:]
                        elif line.startswith("data: "):
                            try:
                                event['data'] = json.loads(line[6:])
                            except json.JSONDecodeError:
                                event['data'] = line[6:]
                    
                    if event:
                        events.append(event)
        
        return events
    
    def test_send_message_and_receive_response(self):
        """Test sending a message and receiving streaming response"""
        # Arrange
        message = "Hello, can you help me?"
        
        # Act: Send message via Express.js proxy
        response = requests.post(
            f"{EXPRESS_API_URL}/stream",
            json={
                "message": message,
                "canvas_id": self.canvas_id
            },
            stream=True,
            timeout=30
        )
        
        # Assert: Response is successful
        assert response.status_code == 200
        assert response.headers['content-type'] == 'text/event-stream'
        
        # Get session ID from headers
        self.session_id = response.headers.get('x-session-id')
        assert self.session_id is not None
        assert self.session_id.startswith('session_')
        
        # Parse SSE events
        events = self.parse_sse_stream(response)
        
        # Assert: Received expected events
        assert len(events) > 0
        
        # Check for init event
        init_events = [e for e in events if e.get('type') == 'init']
        assert len(init_events) > 0
        
        # Check for response events
        response_events = [e for e in events if e.get('type') == 'response']
        assert len(response_events) > 0
        
        # Check for complete event
        complete_events = [e for e in events if e.get('type') == 'complete']
        assert len(complete_events) > 0
    
    def test_message_persistence_in_database(self):
        """Test that messages are persisted to database"""
        # Arrange
        message = "What nodes do I have?"
        
        # Act: Send message
        response = requests.post(
            f"{EXPRESS_API_URL}/stream",
            json={
                "message": message,
                "canvas_id": self.canvas_id
            },
            stream=True,
            timeout=30
        )
        
        self.session_id = response.headers.get('x-session-id')
        
        # Consume stream
        for _ in response.iter_content(chunk_size=1024):
            pass
        
        # Wait for async save to complete
        time.sleep(1)
        
        # Assert: Check database for messages
        conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM chat_messages WHERE session_id = %s ORDER BY created_at",
            (self.session_id,)
        )
        messages = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Should have at least user message
        assert len(messages) >= 1
        
        # Check user message
        user_message = messages[0]
        assert user_message['role'] == 'user'
        assert user_message['content'] == message
        assert user_message['session_id'] == self.session_id
    
    def test_session_management(self):
        """Test session creation and reuse"""
        # Act 1: Send first message (creates session)
        response1 = requests.post(
            f"{EXPRESS_API_URL}/stream",
            json={
                "message": "First message",
                "canvas_id": self.canvas_id
            },
            stream=True,
            timeout=30
        )
        
        session_id_1 = response1.headers.get('x-session-id')
        self.session_id = session_id_1
        
        # Consume stream
        for _ in response1.iter_content(chunk_size=1024):
            pass
        
        # Act 2: Send second message with same session
        response2 = requests.post(
            f"{EXPRESS_API_URL}/stream",
            json={
                "message": "Second message",
                "session_id": session_id_1,
                "canvas_id": self.canvas_id
            },
            stream=True,
            timeout=30
        )
        
        session_id_2 = response2.headers.get('x-session-id')
        
        # Consume stream
        for _ in response2.iter_content(chunk_size=1024):
            pass
        
        # Assert: Same session ID is reused
        assert session_id_1 == session_id_2
        
        # Wait for async save
        time.sleep(1)
        
        # Assert: Both messages in same session
        conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT COUNT(*) as count FROM chat_messages WHERE session_id = %s AND role = 'user'",
            (session_id_1,)
        )
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        assert result['count'] >= 2
    
    def test_get_chat_history(self):
        """Test retrieving chat history via API"""
        # Arrange: Send a message first
        response = requests.post(
            f"{EXPRESS_API_URL}/stream",
            json={
                "message": "Test message for history",
                "canvas_id": self.canvas_id
            },
            stream=True,
            timeout=30
        )
        
        self.session_id = response.headers.get('x-session-id')
        
        # Consume stream
        for _ in response.iter_content(chunk_size=1024):
            pass
        
        # Wait for async save
        time.sleep(1)
        
        # Act: Get chat history
        history_response = requests.get(
            f"{EXPRESS_API_URL}/history/{self.session_id}"
        )
        
        # Assert
        assert history_response.status_code == 200
        history_data = history_response.json()
        
        assert 'messages' in history_data
        assert len(history_data['messages']) >= 1
        assert history_data['session_id'] == self.session_id
    
    def test_create_new_session_via_api(self):
        """Test creating a new session via API"""
        # Act
        response = requests.post(
            f"{EXPRESS_API_URL}/session",
            json={"canvas_id": self.canvas_id}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert 'session_id' in data
        assert data['session_id'].startswith('session_')
        assert data['canvas_id'] == self.canvas_id
        
        self.session_id = data['session_id']
    
    def test_clear_session_via_api(self):
        """Test clearing a session via API"""
        # Arrange: Create session and send message
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
        
        # Consume stream
        for _ in response.iter_content(chunk_size=1024):
            pass
        
        time.sleep(1)
        
        # Act: Clear session
        clear_response = requests.delete(
            f"{EXPRESS_API_URL}/session/{self.session_id}"
        )
        
        # Assert
        assert clear_response.status_code == 200
        data = clear_response.json()
        assert data['success'] is True
        
        # Verify session is deleted
        conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT COUNT(*) as count FROM chat_sessions WHERE id = %s",
            (self.session_id,)
        )
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        assert result['count'] == 0
        
        # Don't cleanup in teardown since we already deleted
        self.session_id = None
    
    def test_streaming_response_format(self):
        """Test that streaming response follows SSE format"""
        # Act
        response = requests.post(
            f"{EXPRESS_API_URL}/stream",
            json={
                "message": "Test streaming format",
                "canvas_id": self.canvas_id
            },
            stream=True,
            timeout=30
        )
        
        self.session_id = response.headers.get('x-session-id')
        
        # Parse events
        events = self.parse_sse_stream(response)
        
        # Assert: All events have required structure
        for event in events:
            assert 'type' in event
            assert event['type'] in ['init', 'response', 'reasoning', 'tool_use', 'tool_result', 'complete', 'error']
            
            if event['type'] == 'response':
                assert 'data' in event
                assert isinstance(event['data'], dict)
                assert 'data' in event['data']  # Response text


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
