"""
Integration Test: Error Handling

Tests error handling scenarios:
1. Network errors
2. File upload errors
3. Tool execution errors
4. Invalid requests
"""
import pytest
import requests
import json
import time
import io
from PIL import Image

# Test configuration
EXPRESS_API_URL = "http://localhost:3000/api/chat"
INVALID_API_URL = "http://localhost:9999/api/chat"  # Non-existent service


class TestErrorHandling:
    """Integration tests for error handling"""
    
    def test_empty_message_error(self):
        """Test sending empty message"""
        # Act
        response = requests.post(
            f"{EXPRESS_API_URL}/stream",
            json={
                "message": "",
                "canvas_id": "test_canvas"
            },
            timeout=10
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data
    
    def test_missing_message_field(self):
        """Test request without message field"""
        # Act
        response = requests.post(
            f"{EXPRESS_API_URL}/stream",
            json={
                "canvas_id": "test_canvas"
            },
            timeout=10
        )
        
        # Assert
        assert response.status_code == 400
    
    def test_invalid_session_id(self):
        """Test using invalid session ID"""
        # Act
        response = requests.get(
            f"{EXPRESS_API_URL}/history/invalid_session_id_12345"
        )
        
        # Assert: Should return empty or error
        # Implementation may vary
        assert response.status_code in [200, 404]
    
    def test_delete_nonexistent_session(self):
        """Test deleting non-existent session"""
        # Act
        response = requests.delete(
            f"{EXPRESS_API_URL}/session/nonexistent_session_12345"
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert 'error' in data
    
    def test_file_upload_without_message(self):
        """Test file upload without message"""
        # Arrange
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        # Act
        response = requests.post(
            f"{EXPRESS_API_URL}/multimodal",
            data={
                "message": "",
                "canvas_id": "test_canvas"
            },
            files={
                "files": ("test.png", img_bytes, "image/png")
            },
            timeout=10
        )
        
        # Assert
        assert response.status_code == 400
    
    def test_file_upload_without_files(self):
        """Test multimodal endpoint without files"""
        # Act
        response = requests.post(
            f"{EXPRESS_API_URL}/multimodal",
            data={
                "message": "Test message",
                "canvas_id": "test_canvas"
            },
            timeout=10
        )
        
        # Assert
        assert response.status_code == 400
    
    def test_unsupported_file_type(self):
        """Test uploading unsupported file type"""
        # Arrange
        text_file = io.BytesIO(b"This is a text file")
        
        # Act
        response = requests.post(
            f"{EXPRESS_API_URL}/multimodal",
            data={
                "message": "Test message",
                "canvas_id": "test_canvas"
            },
            files={
                "files": ("test.txt", text_file, "text/plain")
            },
            timeout=10
        )
        
        # Assert
        assert response.status_code == 400
    
    def test_oversized_image_file(self):
        """Test uploading oversized image (>5MB)"""
        # Arrange: Create large image
        large_img = Image.new('RGB', (4000, 4000), color='blue')
        img_bytes = io.BytesIO()
        large_img.save(img_bytes, format='PNG', quality=100)
        img_bytes.seek(0)
        
        # Act
        response = requests.post(
            f"{EXPRESS_API_URL}/multimodal",
            data={
                "message": "Test large image",
                "canvas_id": "test_canvas"
            },
            files={
                "files": ("large.png", img_bytes, "image/png")
            },
            timeout=30
        )
        
        # Assert: Should reject or handle gracefully
        assert response.status_code in [200, 400]
    
    def test_malformed_json_request(self):
        """Test sending malformed JSON"""
        # Act
        response = requests.post(
            f"{EXPRESS_API_URL}/stream",
            data="{ invalid json }",
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        # Assert
        assert response.status_code == 400
    
    def test_missing_canvas_id(self):
        """Test request without canvas_id"""
        # Act: Send message without canvas_id
        response = requests.post(
            f"{EXPRESS_API_URL}/stream",
            json={
                "message": "Test message"
            },
            stream=True,
            timeout=30
        )
        
        # Assert: Should still work (canvas_id is optional)
        assert response.status_code == 200
        
        # Consume stream
        for _ in response.iter_content(chunk_size=1024):
            pass
    
    def test_concurrent_requests_same_session(self):
        """Test handling concurrent requests for same session"""
        # This tests race conditions in session management
        # Create session first
        create_response = requests.post(
            f"{EXPRESS_API_URL}/session",
            json={"canvas_id": "test_canvas"}
        )
        
        session_id = create_response.json()['session_id']
        
        # Send multiple concurrent requests
        import concurrent.futures
        
        def send_message(msg_num):
            response = requests.post(
                f"{EXPRESS_API_URL}/stream",
                json={
                    "message": f"Message {msg_num}",
                    "session_id": session_id,
                    "canvas_id": "test_canvas"
                },
                stream=True,
                timeout=30
            )
            # Consume stream
            for _ in response.iter_content(chunk_size=1024):
                pass
            return response.status_code
        
        # Send 3 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(send_message, i) for i in range(3)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # All should succeed
        assert all(status == 200 for status in results)
        
        # Cleanup
        requests.delete(f"{EXPRESS_API_URL}/session/{session_id}")
    
    def test_timeout_handling(self):
        """Test request timeout handling"""
        # Act: Send request with very short timeout
        try:
            response = requests.post(
                f"{EXPRESS_API_URL}/stream",
                json={
                    "message": "Test message",
                    "canvas_id": "test_canvas"
                },
                stream=True,
                timeout=0.001  # Very short timeout
            )
            # If we get here, request was faster than timeout
            for _ in response.iter_content(chunk_size=1024):
                pass
        except requests.exceptions.Timeout:
            # Expected - timeout occurred
            pass
    
    def test_invalid_http_method(self):
        """Test using wrong HTTP method"""
        # Act: Use GET instead of POST for stream endpoint
        response = requests.get(
            f"{EXPRESS_API_URL}/stream",
            timeout=10
        )
        
        # Assert
        assert response.status_code in [404, 405]  # Not Found or Method Not Allowed
    
    def test_error_event_in_stream(self):
        """Test that errors are properly sent as SSE events"""
        # This test depends on implementation
        # If Python service is down, Express should send error event
        pass  # Skip for now - requires stopping Python service


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
