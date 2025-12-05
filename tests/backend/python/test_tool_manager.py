"""
Unit tests for ToolManager
Tests all canvas tools: search_canvas_content, get_canvas_titles, 
get_canvas_tags, and find_similar_nodes.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import json

# Import the ToolManager class
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../chat_service'))

from tool_manager import ToolManager


class TestToolManager:
    """Test cases for ToolManager class"""
    
    def setup_method(self):
        """Set up test fixtures before each test method"""
        self.tool_manager = ToolManager()
        # Mock the database connection
        self.tool_manager.get_db_connection = Mock()
        self.mock_conn = Mock()
        self.mock_cursor = Mock()
        self.tool_manager.get_db_connection.return_value = self.mock_conn
        self.mock_conn.cursor.return_value = self.mock_cursor
    
    def test_search_canvas_content_with_results(self):
        """Test searching canvas content with matching results"""
        # Arrange
        query = "project planning"
        canvas_id = "canvas_123"
        mock_results = [
            {
                "id": "node_1",
                "content": "Project Planning Meeting",
                "position_x": 100,
                "position_y": 200,
                "type": "text",
                "created_at": None,
                "updated_at": None
            }
        ]
        self.mock_cursor.fetchall.return_value = mock_results
        
        # Act
        result = self.tool_manager.search_canvas_content(query, canvas_id)
        
        # Assert
        result_data = json.loads(result)
        assert result_data["found"] == 1
        assert len(result_data["nodes"]) == 1
        assert result_data["nodes"][0]["content"] == "Project Planning Meeting"
        assert result_data["query"] == query
    
    def test_search_canvas_content_no_results(self):
        """Test searching canvas content with no matching results"""
        # Arrange
        query = "nonexistent topic"
        canvas_id = "canvas_123"
        self.mock_cursor.fetchall.return_value = []
        
        # Act
        result = self.tool_manager.search_canvas_content(query, canvas_id)
        
        # Assert
        result_data = json.loads(result)
        assert result_data["found"] == 0
        assert result_data["nodes"] == []
    
    def test_search_canvas_content_database_error(self):
        """Test handling database errors in search"""
        # Arrange
        query = "test query"
        canvas_id = "canvas_123"
        self.mock_cursor.execute.side_effect = Exception("Database error")
        
        # Act
        result = self.tool_manager.search_canvas_content(query, canvas_id)
        
        # Assert
        result_data = json.loads(result)
        assert "error" in result_data
        assert "Database error" in result_data["error"]
        assert result_data["found"] == 0
    
    def test_get_canvas_titles_with_nodes(self):
        """Test getting canvas titles with existing nodes"""
        # Arrange
        canvas_id = "canvas_123"
        mock_titles = [
            {"id": "node_1", "content": "Meeting Notes\nSome details", "type": "text", "created_at": None},
            {"id": "node_2", "content": "Project Timeline", "type": "text", "created_at": None}
        ]
        self.mock_cursor.fetchall.return_value = mock_titles
        
        # Act
        result = self.tool_manager.get_canvas_titles(canvas_id)
        
        # Assert
        result_data = json.loads(result)
        assert result_data["count"] == 2
        assert len(result_data["titles"]) == 2
        assert result_data["titles"][0]["title"] == "Meeting Notes"
        assert result_data["titles"][1]["title"] == "Project Timeline"
    
    def test_get_canvas_titles_empty_canvas(self):
        """Test getting titles from empty canvas"""
        # Arrange
        canvas_id = "canvas_empty"
        self.mock_cursor.fetchall.return_value = []
        
        # Act
        result = self.tool_manager.get_canvas_titles(canvas_id)
        
        # Assert
        result_data = json.loads(result)
        assert result_data["count"] == 0
        assert result_data["titles"] == []
    
    def test_get_canvas_tags_with_hashtags(self):
        """Test extracting hashtags from canvas content"""
        # Arrange
        canvas_id = "canvas_123"
        mock_content = [
            {"content": "Meeting about #project #planning and #goals"},
            {"content": "Review #budget and #timeline for #project"},
            {"content": "No hashtags in this content"}
        ]
        self.mock_cursor.fetchall.return_value = mock_content
        
        # Act
        result = self.tool_manager.get_canvas_tags(canvas_id)
        
        # Assert
        result_data = json.loads(result)
        assert result_data["count"] > 0
        tags = result_data["tags"]
        assert "project" in tags
        assert "planning" in tags
        assert "goals" in tags
        assert "budget" in tags
        assert "timeline" in tags
    
    def test_get_canvas_tags_no_hashtags(self):
        """Test extracting tags when no hashtags exist"""
        # Arrange
        canvas_id = "canvas_123"
        mock_content = [
            {"content": "Regular content without hashtags"},
            {"content": "Another node with normal text"}
        ]
        self.mock_cursor.fetchall.return_value = mock_content
        
        # Act
        result = self.tool_manager.get_canvas_tags(canvas_id)
        
        # Assert
        result_data = json.loads(result)
        assert result_data["count"] == 0
        assert result_data["tags"] == []
    
    def test_find_similar_nodes_with_matches(self):
        """Test finding similar nodes with good matches"""
        # Arrange
        query = "project management"
        canvas_id = "canvas_123"
        mock_nodes = [
            {
                "id": "node_1",
                "content": "Project Management Best Practices",
                "position_x": 100,
                "position_y": 200,
                "type": "text",
                "created_at": None
            },
            {
                "id": "node_2",
                "content": "Team Management",
                "position_x": 300,
                "position_y": 400,
                "type": "text",
                "created_at": None
            }
        ]
        self.mock_cursor.fetchall.return_value = mock_nodes
        
        # Act
        result = self.tool_manager.find_similar_nodes(query, canvas_id, limit=5)
        
        # Assert
        result_data = json.loads(result)
        assert result_data["found"] > 0
        assert len(result_data["nodes"]) > 0
        # First result should have both keywords
        assert "project" in result_data["nodes"][0]["content"].lower()
    
    def test_find_similar_nodes_no_matches(self):
        """Test finding similar nodes with no good matches"""
        # Arrange
        query = "quantum physics"
        canvas_id = "canvas_123"
        mock_nodes = [
            {"id": "node_1", "content": "Meeting Notes", "position_x": 100, "position_y": 200, "type": "text", "created_at": None},
            {"id": "node_2", "content": "Budget Report", "position_x": 300, "position_y": 400, "type": "text", "created_at": None}
        ]
        self.mock_cursor.fetchall.return_value = mock_nodes
        
        # Act
        result = self.tool_manager.find_similar_nodes(query, canvas_id)
        
        # Assert
        result_data = json.loads(result)
        assert result_data["found"] == 0
        assert result_data["nodes"] == []
    
    def test_get_canvas_tools_returns_all_tools(self):
        """Test that get_canvas_tools returns all 4 tools"""
        # Act
        tools = self.tool_manager.get_canvas_tools()
        
        # Assert
        assert len(tools) == 4
        tool_names = [tool.__name__ for tool in tools]
        assert "search_canvas_content" in tool_names
        assert "get_canvas_titles" in tool_names
        assert "get_canvas_tags" in tool_names
        assert "find_similar_nodes" in tool_names
    
    def test_json_serialization(self):
        """Test that all tool results are valid JSON"""
        # Arrange
        canvas_id = "canvas_123"
        self.mock_cursor.fetchall.return_value = [
            {"id": "node_1", "content": "Test with special chars: àáâã", "type": "text", "created_at": None}
        ]
        
        # Act & Assert - Should not raise JSON serialization errors
        result1 = self.tool_manager.search_canvas_content("test", canvas_id)
        json.loads(result1)  # Should not raise
        
        result2 = self.tool_manager.get_canvas_titles(canvas_id)
        json.loads(result2)  # Should not raise
        
        result3 = self.tool_manager.get_canvas_tags(canvas_id)
        json.loads(result3)  # Should not raise
        
        result4 = self.tool_manager.find_similar_nodes("test", canvas_id)
        json.loads(result4)  # Should not raise
    
    def test_database_connection_error(self):
        """Test handling database connection errors"""
        # Arrange
        self.tool_manager.get_db_connection.side_effect = Exception("Connection failed")
        
        # Act
        result = self.tool_manager.search_canvas_content("test", "canvas_123")
        
        # Assert
        result_data = json.loads(result)
        assert "error" in result_data
        assert "Connection failed" in result_data["error"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
