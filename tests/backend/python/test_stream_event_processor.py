"""
Unit tests for StreamEventProcessor
Tests SSE event formatting, multimodal message creation, and image extraction.
"""
import pytest
from unittest.mock import Mock, patch, mock_open
import json
import base64

# Import the StreamEventProcessor class
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../chat_service'))

from stream_event_processor import StreamEventProcessor


class TestStreamEventProcessor:
    """Test cases for StreamEventProcessor class"""
    
    def setup_method(self):
        """Set up test fixtures before each test method"""
        self.processor = StreamEventProcessor()
    
    def test_format_sse_init_event(self):
        """Test formatting SSE init event"""
        # Arrange
        event_data = {"type": "init"}
        
        # Act
        sse_event = self.processor.format_sse(event_data)
        
        # Assert
        assert sse_event.startswith("event: init\n")
        assert "data: " in sse_event
        assert sse_event.endswith("\n\n")
        # Parse the data part
        lines = sse_event.split("\n")
        data_line = [line for line in lines if line.startswith("data: ")][0]
        data_json = data_line.replace("data: ", "")
        parsed_data = json.loads(data_json)
        assert parsed_data["type"] == "init"
    
    def test_format_sse_response_event(self):
        """Test formatting SSE response event with text chunk"""
        # Arrange
        event_data = {"type": "response", "data": "Hello, I can help you"}
        
        # Act
        sse_event = self.processor.format_sse(event_data)
        
        # Assert
        assert sse_event.startswith("event: response\n")
        lines = sse_event.split("\n")
        data_line = [line for line in lines if line.startswith("data: ")][0]
        data_json = data_line.replace("data: ", "")
        parsed_data = json.loads(data_json)
        assert parsed_data["type"] == "response"
        assert parsed_data["data"] == "Hello, I can help you"
    
    def test_format_sse_tool_use_event(self):
        """Test formatting SSE tool_use event"""
        # Arrange
        event_data = {
            "type": "tool_use",
            "toolUseId": "tool_123",
            "name": "search_canvas_content",
            "input": {"query": "project", "canvas_id": "canvas_123"}
        }
        
        # Act
        sse_event = self.processor.format_sse(event_data)
        
        # Assert
        assert sse_event.startswith("event: tool_use\n")
        lines = sse_event.split("\n")
        data_line = [line for line in lines if line.startswith("data: ")][0]
        data_json = data_line.replace("data: ", "")
        parsed_data = json.loads(data_json)
        assert parsed_data["type"] == "tool_use"
        assert parsed_data["toolUseId"] == "tool_123"
        assert parsed_data["name"] == "search_canvas_content"
        assert parsed_data["input"]["query"] == "project"
    
    def test_format_sse_tool_result_event(self):
        """Test formatting SSE tool_result event"""
        # Arrange
        tool_result = {"found": 3, "nodes": [{"title": "Project A"}]}
        event_data = {
            "type": "tool_result",
            "toolUseId": "tool_123",
            "result": json.dumps(tool_result)
        }
        
        # Act
        sse_event = self.processor.format_sse(event_data)
        
        # Assert
        assert sse_event.startswith("event: tool_result\n")
        lines = sse_event.split("\n")
        data_line = [line for line in lines if line.startswith("data: ")][0]
        data_json = data_line.replace("data: ", "")
        parsed_data = json.loads(data_json)
        assert parsed_data["type"] == "tool_result"
        assert parsed_data["toolUseId"] == "tool_123"
    
    def test_format_sse_reasoning_event(self):
        """Test formatting SSE reasoning event"""
        # Arrange
        event_data = {
            "type": "reasoning",
            "text": "I need to search for nodes in the canvas."
        }
        
        # Act
        sse_event = self.processor.format_sse(event_data)
        
        # Assert
        assert sse_event.startswith("event: reasoning\n")
        lines = sse_event.split("\n")
        data_line = [line for line in lines if line.startswith("data: ")][0]
        data_json = data_line.replace("data: ", "")
        parsed_data = json.loads(data_json)
        assert parsed_data["type"] == "reasoning"
        assert "search for nodes" in parsed_data["text"]
    
    def test_format_sse_complete_event(self):
        """Test formatting SSE complete event"""
        # Arrange
        event_data = {
            "type": "complete",
            "result": "Task completed",
            "images": []
        }
        
        # Act
        sse_event = self.processor.format_sse(event_data)
        
        # Assert
        assert sse_event.startswith("event: complete\n")
        lines = sse_event.split("\n")
        data_line = [line for line in lines if line.startswith("data: ")][0]
        data_json = data_line.replace("data: ", "")
        parsed_data = json.loads(data_json)
        assert parsed_data["type"] == "complete"
    
    def test_format_sse_error_event(self):
        """Test formatting SSE error event"""
        # Arrange
        event_data = {
            "type": "error",
            "message": "Something went wrong"
        }
        
        # Act
        sse_event = self.processor.format_sse(event_data)
        
        # Assert
        assert sse_event.startswith("event: error\n")
        lines = sse_event.split("\n")
        data_line = [line for line in lines if line.startswith("data: ")][0]
        data_json = data_line.replace("data: ", "")
        parsed_data = json.loads(data_json)
        assert parsed_data["type"] == "error"
        assert parsed_data["message"] == "Something went wrong"
    
    def test_create_multimodal_message_text_only(self):
        """Test creating message with text only"""
        # Arrange
        text = "What's in this canvas?"
        
        # Act
        result = self.processor.create_multimodal_message(text, None)
        
        # Assert
        assert result == text
    
    @patch("builtins.open", new_callable=mock_open, read_data=b"fake_image_data")
    def test_create_multimodal_message_with_image(self, mock_file):
        """Test creating multimodal message with image file"""
        # Arrange
        text = "Analyze this image"
        files = ["/tmp/test.png"]
        
        # Act
        result = self.processor.create_multimodal_message(text, files)
        
        # Assert
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0] == {"text": text}
        assert "image" in result[1]
    
    @patch("builtins.open", new_callable=mock_open, read_data=b"fake_pdf_data")
    def test_create_multimodal_message_with_pdf(self, mock_file):
        """Test creating multimodal message with PDF file"""
        # Arrange
        text = "Summarize this document"
        files = ["/tmp/document.pdf"]
        
        # Act
        result = self.processor.create_multimodal_message(text, files)
        
        # Assert
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0] == {"text": text}
        assert "document" in result[1]
    
    def test_get_mime_type_image(self):
        """Test getting MIME type for image files"""
        # Act
        mime_type = self.processor.get_mime_type("test.png")
        
        # Assert
        assert mime_type == "image/png"
    
    def test_get_mime_type_pdf(self):
        """Test getting MIME type for PDF files"""
        # Act
        mime_type = self.processor.get_mime_type("document.pdf")
        
        # Assert
        assert mime_type == "application/pdf"
    
    def test_get_mime_type_unknown(self):
        """Test getting MIME type for unknown files"""
        # Act
        mime_type = self.processor.get_mime_type("file.xyz")
        
        # Assert
        assert mime_type == "application/octet-stream"
    
    def test_extract_images_with_images(self):
        """Test extracting images from result"""
        # Arrange
        result = {
            "images": [
                {"url": "data:image/png;base64,abc123", "alt": "Chart"},
                {"url": "data:image/jpeg;base64,def456", "alt": "Graph"}
            ]
        }
        
        # Act
        images = self.processor.extract_images(result)
        
        # Assert
        assert len(images) == 2
        assert images[0]["alt"] == "Chart"
        assert images[1]["alt"] == "Graph"
    
    def test_extract_images_no_images(self):
        """Test extracting images when none exist"""
        # Arrange
        result = {"data": "some text"}
        
        # Act
        images = self.processor.extract_images(result)
        
        # Assert
        assert len(images) == 0
    
    def test_handle_special_characters_in_sse(self):
        """Test handling special characters in SSE events"""
        # Arrange
        event_data = {
            "type": "response",
            "data": "Text with special chars: àáâã, quotes: \"hello\""
        }
        
        # Act
        sse_event = self.processor.format_sse(event_data)
        
        # Assert
        # Should not raise JSON serialization errors
        lines = sse_event.split("\n")
        data_line = [line for line in lines if line.startswith("data: ")][0]
        data_json = data_line.replace("data: ", "")
        parsed_data = json.loads(data_json)  # Should not raise
        assert parsed_data["data"] == event_data["data"]
    
    def test_get_current_timestamp(self):
        """Test getting current timestamp"""
        # Act
        timestamp = self.processor.get_current_timestamp()
        
        # Assert
        assert isinstance(timestamp, str)
        assert "T" in timestamp  # ISO format includes T
        assert len(timestamp) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
