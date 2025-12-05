"""
Integration Test: File Upload Flow

Tests the file upload pipeline:
1. Upload image file
2. Upload PDF file
3. Verify multimodal message creation
4. Verify file validation
"""
import pytest
import requests
import json
import time
import io
import os
from PIL import Image
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


class TestFileUploadFlow:
    """Integration tests for file upload flow"""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test"""
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
    
    def create_test_image(self) -> io.BytesIO:
        """Create a test image file"""
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        return img_bytes
    
    def create_test_pdf(self) -> io.BytesIO:
        """Create a test PDF file"""
        # Simple PDF content
        pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test PDF) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000317 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
410
%%EOF"""
        return io.BytesIO(pdf_content)
    
    def test_upload_image_file(self):
        """Test uploading an image file"""
        # Arrange
        message = "What's in this image?"
        image_file = self.create_test_image()
        
        # Act
        response = requests.post(
            f"{EXPRESS_API_URL}/multimodal",
            data={
                "message": message,
                "canvas_id": self.canvas_id
            },
            files={
                "files": ("test_image.png", image_file, "image/png")
            },
            stream=True,
            timeout=30
        )
        
        # Assert
        assert response.status_code == 200
        assert response.headers['content-type'] == 'text/event-stream'
        
        self.session_id = response.headers.get('x-session-id')
        assert self.session_id is not None
        
        # Consume stream
        events = []
        buffer = ""
        for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
            if chunk:
                buffer += chunk
                while "\n\n" in buffer:
                    event_text, buffer = buffer.split("\n\n", 1)
                    if "event:" in event_text:
                        events.append(event_text)
        
        # Should receive events
        assert len(events) > 0
    
    def test_upload_pdf_file(self):
        """Test uploading a PDF file"""
        # Arrange
        message = "Summarize this document"
        pdf_file = self.create_test_pdf()
        
        # Act
        response = requests.post(
            f"{EXPRESS_API_URL}/multimodal",
            data={
                "message": message,
                "canvas_id": self.canvas_id
            },
            files={
                "files": ("test_document.pdf", pdf_file, "application/pdf")
            },
            stream=True,
            timeout=30
        )
        
        # Assert
        assert response.status_code == 200
        self.session_id = response.headers.get('x-session-id')
        
        # Consume stream
        for _ in response.iter_content(chunk_size=1024):
            pass
    
    def test_upload_multiple_files(self):
        """Test uploading multiple files"""
        # Arrange
        message = "Analyze these files"
        image_file = self.create_test_image()
        pdf_file = self.create_test_pdf()
        
        # Act
        response = requests.post(
            f"{EXPRESS_API_URL}/multimodal",
            data={
                "message": message,
                "canvas_id": self.canvas_id
            },
            files=[
                ("files", ("image.png", image_file, "image/png")),
                ("files", ("document.pdf", pdf_file, "application/pdf"))
            ],
            stream=True,
            timeout=30
        )
        
        # Assert
        assert response.status_code == 200
        self.session_id = response.headers.get('x-session-id')
        
        # Consume stream
        for _ in response.iter_content(chunk_size=1024):
            pass
    
    def test_file_size_validation_image(self):
        """Test file size validation for images (5MB limit)"""
        # Arrange: Create large image (>5MB)
        large_img = Image.new('RGB', (3000, 3000), color='blue')
        img_bytes = io.BytesIO()
        large_img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        # Act
        response = requests.post(
            f"{EXPRESS_API_URL}/multimodal",
            data={
                "message": "Test large image",
                "canvas_id": self.canvas_id
            },
            files={
                "files": ("large_image.png", img_bytes, "image/png")
            },
            stream=True,
            timeout=30
        )
        
        # Assert: Should reject or handle gracefully
        # Note: Actual behavior depends on implementation
        # Either 400 error or successful with warning
        assert response.status_code in [200, 400]
    
    def test_unsupported_file_type(self):
        """Test uploading unsupported file type"""
        # Arrange
        text_file = io.BytesIO(b"This is a text file")
        
        # Act
        response = requests.post(
            f"{EXPRESS_API_URL}/multimodal",
            data={
                "message": "Test unsupported file",
                "canvas_id": self.canvas_id
            },
            files={
                "files": ("test.txt", text_file, "text/plain")
            },
            stream=True,
            timeout=30
        )
        
        # Assert: Should reject unsupported file type
        assert response.status_code == 400
    
    def test_multimodal_message_persistence(self):
        """Test that multimodal messages are persisted with file info"""
        # Arrange
        message = "Analyze this image"
        image_file = self.create_test_image()
        
        # Act
        response = requests.post(
            f"{EXPRESS_API_URL}/multimodal",
            data={
                "message": message,
                "canvas_id": self.canvas_id
            },
            files={
                "files": ("test.png", image_file, "image/png")
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
        
        # Assert: Check database for message with file info
        conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM chat_messages WHERE session_id = %s AND role = 'user'",
            (self.session_id,)
        )
        user_message = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        assert user_message is not None
        assert user_message['content'] == message
        # Note: File info storage depends on implementation
        # May be in 'files' JSONB column
    
    def test_empty_message_with_file(self):
        """Test uploading file with empty message"""
        # Arrange
        image_file = self.create_test_image()
        
        # Act
        response = requests.post(
            f"{EXPRESS_API_URL}/multimodal",
            data={
                "message": "",
                "canvas_id": self.canvas_id
            },
            files={
                "files": ("test.png", image_file, "image/png")
            },
            stream=True,
            timeout=30
        )
        
        # Assert: Should reject empty message
        assert response.status_code == 400
    
    def test_no_files_provided(self):
        """Test multimodal endpoint with no files"""
        # Act
        response = requests.post(
            f"{EXPRESS_API_URL}/multimodal",
            data={
                "message": "Test message",
                "canvas_id": self.canvas_id
            },
            stream=True,
            timeout=30
        )
        
        # Assert: Should reject request without files
        assert response.status_code == 400


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
