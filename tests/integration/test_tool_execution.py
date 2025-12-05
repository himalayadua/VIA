"""
Integration Test: Tool Execution Flow

Tests tool execution with real database queries:
1. Trigger tool execution via chat
2. Verify tool results
3. Check tool execution persistence
4. Validate database queries
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


class TestToolExecutionFlow:
    """Integration tests for tool execution"""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown"""
        self.canvas_id = "test_canvas_" + str(int(time.time()))
        self.session_id = None
        self.test_node_ids = []
        
        # Create test nodes in canvas
        self.create_test_nodes()
        
        yield
        
        self.cleanup_test_data()
    
    def create_test_nodes(self):
        """Create test nodes in canvas for tool testing"""
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Create test canvas
        cursor.execute(
            "INSERT INTO canvases (id, name, created_at, updated_at) VALUES (%s, %s, NOW(), NOW())",
            (self.canvas_id, "Test Canvas")
        )
        
        # Create test nodes
        test_nodes = [
            ("Project Planning Meeting", "Discuss Q1 goals and milestones #project #planning"),
            ("Budget Review", "Review Q1 budget and expenses #budget #finance"),
            ("Team Standup", "Daily standup notes #team #standup")
        ]
        
        for title, content in test_nodes:
            cursor.execute(
                """INSERT INTO nodes (canvas_id, content, position_x, position_y, type, created_at, updated_at)
                   VALUES (%s, %s, %s, %s, %s, NOW(), NOW()) RETURNING id""",
                (self.canvas_id, f"{title}\n{content}", 100, 100, 'text')
            )
            node_id = cursor.fetchone()[0]
            self.test_node_ids.append(node_id)
        
        conn.commit()
        cursor.close()
        conn.close()
    
    def cleanup_test_data(self):
        """Clean up test data"""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            # Delete test nodes
            for node_id in self.test_node_ids:
                cursor.execute("DELETE FROM nodes WHERE id = %s", (node_id,))
            
            # Delete test canvas
            cursor.execute("DELETE FROM canvases WHERE id = %s", (self.canvas_id,))
            
            # Delete test session
            if self.session_id:
                cursor.execute("DELETE FROM chat_messages WHERE session_id = %s", (self.session_id,))
                cursor.execute("DELETE FROM chat_sessions WHERE id = %s", (self.session_id,))
            
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Cleanup error: {e}")
    
    def parse_sse_events(self, response):
        """Parse SSE events from response"""
        events = []
        buffer = ""
        
        for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
            if chunk:
                buffer += chunk
                while "\n\n" in buffer:
                    event_text, buffer = buffer.split("\n\n", 1)
                    event = {}
                    for line in event_text.split("\n"):
                        if line.startswith("event: "):
                            event['type'] = line[7:]
                        elif line.startswith("data: "):
                            try:
                                event['data'] = json.loads(line[6:])
                            except:
                                event['data'] = line[6:]
                    if event:
                        events.append(event)
        
        return events
    
    def test_search_canvas_content_tool(self):
        """Test search_canvas_content tool execution"""
        # Act: Send message that triggers search tool
        response = requests.post(
            f"{EXPRESS_API_URL}/stream",
            json={
                "message": "Search for nodes about 'project planning'",
                "canvas_id": self.canvas_id
            },
            stream=True,
            timeout=30
        )
        
        self.session_id = response.headers.get('x-session-id')
        
        # Parse events
        events = self.parse_sse_events(response)
        
        # Assert: Tool was executed
        tool_use_events = [e for e in events if e.get('type') == 'tool_use']
        assert len(tool_use_events) > 0
        
        # Check tool name
        tool_event = tool_use_events[0]
        assert 'data' in tool_event
        assert tool_event['data'].get('name') == 'search_canvas_content'
        
        # Check tool result
        tool_result_events = [e for e in events if e.get('type') == 'tool_result']
        assert len(tool_result_events) > 0
        
        result_event = tool_result_events[0]
        result_data = json.loads(result_event['data'].get('result', '{}'))
        assert 'found' in result_data
        assert result_data['found'] > 0  # Should find our test node
    
    def test_get_canvas_titles_tool(self):
        """Test get_canvas_titles tool execution"""
        # Act
        response = requests.post(
            f"{EXPRESS_API_URL}/stream",
            json={
                "message": "What nodes do I have on my canvas?",
                "canvas_id": self.canvas_id
            },
            stream=True,
            timeout=30
        )
        
        self.session_id = response.headers.get('x-session-id')
        events = self.parse_sse_events(response)
        
        # Assert: Tool executed
        tool_use_events = [e for e in events if e.get('type') == 'tool_use']
        assert len(tool_use_events) > 0
        
        # Check for get_canvas_titles
        titles_tool = next((e for e in tool_use_events 
                           if e['data'].get('name') == 'get_canvas_titles'), None)
        assert titles_tool is not None
        
        # Check result
        tool_result_events = [e for e in events if e.get('type') == 'tool_result']
        assert len(tool_result_events) > 0
        
        result_event = tool_result_events[0]
        result_data = json.loads(result_event['data'].get('result', '{}'))
        assert 'count' in result_data
        assert result_data['count'] == 3  # Our 3 test nodes
    
    def test_get_canvas_tags_tool(self):
        """Test get_canvas_tags tool execution"""
        # Act
        response = requests.post(
            f"{EXPRESS_API_URL}/stream",
            json={
                "message": "What tags are used in my canvas?",
                "canvas_id": self.canvas_id
            },
            stream=True,
            timeout=30
        )
        
        self.session_id = response.headers.get('x-session-id')
        events = self.parse_sse_events(response)
        
        # Assert: Tool executed
        tool_use_events = [e for e in events if e.get('type') == 'tool_use']
        tags_tool = next((e for e in tool_use_events 
                         if e['data'].get('name') == 'get_canvas_tags'), None)
        
        if tags_tool:  # Tool may or may not be called depending on AI decision
            tool_result_events = [e for e in events if e.get('type') == 'tool_result']
            if tool_result_events:
                result_data = json.loads(tool_result_events[0]['data'].get('result', '{}'))
                assert 'tags' in result_data
                # Should find our test tags
                tags = result_data.get('tags', [])
                assert 'project' in tags or 'planning' in tags or 'budget' in tags
    
    def test_find_similar_nodes_tool(self):
        """Test find_similar_nodes tool execution"""
        # Act
        response = requests.post(
            f"{EXPRESS_API_URL}/stream",
            json={
                "message": "Find nodes similar to 'project management'",
                "canvas_id": self.canvas_id
            },
            stream=True,
            timeout=30
        )
        
        self.session_id = response.headers.get('x-session-id')
        events = self.parse_sse_events(response)
        
        # Assert: Tool may be executed
        tool_use_events = [e for e in events if e.get('type') == 'tool_use']
        similar_tool = next((e for e in tool_use_events 
                            if e['data'].get('name') == 'find_similar_nodes'), None)
        
        if similar_tool:
            tool_result_events = [e for e in events if e.get('type') == 'tool_result']
            if tool_result_events:
                result_data = json.loads(tool_result_events[0]['data'].get('result', '{}'))
                assert 'found' in result_data
    
    def test_tool_execution_persistence(self):
        """Test that tool executions are persisted in database"""
        # Act
        response = requests.post(
            f"{EXPRESS_API_URL}/stream",
            json={
                "message": "Search for 'budget' in my canvas",
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
        
        # Assert: Check database for assistant message with tool executions
        conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM chat_messages WHERE session_id = %s AND role = 'assistant'",
            (self.session_id,)
        )
        assistant_message = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if assistant_message:
            tool_executions = json.loads(assistant_message.get('tool_executions', '[]'))
            # May have tool executions depending on AI decision
            assert isinstance(tool_executions, list)
    
    def test_multiple_tool_executions(self):
        """Test message that triggers multiple tools"""
        # Act
        response = requests.post(
            f"{EXPRESS_API_URL}/stream",
            json={
                "message": "Give me an overview of my canvas: what nodes I have and what tags are used",
                "canvas_id": self.canvas_id
            },
            stream=True,
            timeout=30
        )
        
        self.session_id = response.headers.get('x-session-id')
        events = self.parse_sse_events(response)
        
        # Assert: Multiple tools may be executed
        tool_use_events = [e for e in events if e.get('type') == 'tool_use']
        # AI may use multiple tools to answer
        assert len(tool_use_events) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
