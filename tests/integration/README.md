# Integration Tests for Chat Sidebar Feature

This directory contains integration tests that verify end-to-end functionality across multiple system components.

## Structure

```
tests/integration/
├── README.md
├── test_chat_flow.py           # End-to-end chat flow
├── test_file_upload.py         # File upload flow
├── test_tool_execution.py      # Tool execution flow
├── test_session_persistence.py # Session persistence
└── test_error_handling.py      # Error handling scenarios
```

## What Integration Tests Cover

Integration tests verify that multiple components work together correctly:

- **Frontend → Express.js → Python AI Service → Database**
- **File upload pipeline with multipart form data**
- **Tool execution with database queries**
- **Session management across services**
- **Error propagation and handling**

## Requirements

### Services Must Be Running

Integration tests require all services to be running:

```bash
# Terminal 1: PostgreSQL
docker-compose up postgres

# Terminal 2: Python AI Service
cd chat_service
source venv/bin/activate
uvicorn app:app --reload --port 8000

# Terminal 3: Express.js Backend
cd server
npm run dev

# Terminal 4: Frontend (optional, for full E2E)
npm run dev
```

### Test Database

Integration tests use a test database to avoid polluting production data:

```bash
# Set environment variable
export DB_NAME=via_canvas_test

# Run migrations
cd supabase
psql -U viacanvas -d via_canvas_test -f migrations/20251029000000_create_chat_schema.sql
```

## Running Integration Tests

### All Integration Tests
```bash
cd tests
python -m pytest integration/ -v
```

### Specific Test File
```bash
python -m pytest integration/test_chat_flow.py -v
```

### With Coverage
```bash
python -m pytest integration/ -v --cov=../chat_service --cov=../server/src
```

## Test Scenarios

### 24.1: End-to-End Chat Flow
- Send message via API
- Verify SSE streaming response
- Check message persistence in database
- Verify session management

### 24.2: File Upload Flow
- Upload image file
- Upload PDF file
- Verify multimodal message creation
- Check file validation

### 24.3: Tool Execution Flow
- Trigger canvas tool execution
- Verify tool results
- Check tool execution persistence
- Validate database queries

### 24.4: Session Persistence
- Create new session
- Send messages
- Simulate page reload
- Verify session restoration

### 24.5: Error Handling
- Test network errors
- Test file upload errors
- Test tool execution errors
- Verify error messages

## Notes

- Integration tests are slower than unit tests (require running services)
- Tests clean up after themselves (delete test data)
- Tests use real database connections (not mocked)
- Tests verify actual HTTP/SSE communication
- Some tests may require NVIDIA_NIM_API_KEY (can be mocked)

## Troubleshooting

### Tests Fail with "Connection Refused"
- Ensure all services are running
- Check service URLs in environment variables

### Tests Fail with "Database Error"
- Ensure test database exists
- Run migrations on test database
- Check database credentials

### Tests Timeout
- Increase timeout values in test configuration
- Check service logs for errors
- Verify NVIDIA NIM API key is valid

## Coverage

Integration tests provide ~75% coverage of user-facing flows:
- ✅ Message send/receive
- ✅ File uploads
- ✅ Tool execution
- ✅ Session management
- ✅ Error handling
