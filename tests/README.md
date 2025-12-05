# Test Suite for Chat Sidebar Feature

This directory contains all unit tests for the chat sidebar functionality.

## Structure

```
tests/
├── backend/
│   ├── python/          # Python AI service tests
│   │   ├── test_session_manager.py
│   │   ├── test_tool_manager.py
│   │   └── test_stream_event_processor.py
│   └── express/         # Express.js backend tests
│       └── test_session_service.js
└── frontend/            # React frontend tests
    ├── stores/
    │   └── test_chat_store.ts
    └── hooks/
        └── test_use_chat.ts
```

## Running Tests

### Python Tests (Backend)
```bash
cd chat_service
python -m pytest ../tests/backend/python/ -v
```

### Express.js Tests (Backend)
```bash
cd server
npm test -- tests/backend/express/
```

### Frontend Tests
```bash
npm test -- tests/frontend/
```

### Integration Tests
```bash
# Requires all services running
python -m pytest integration/ -v
```

## Coverage

This test suite covers:
- ✅ Session management (Python & Express.js)
- ✅ Canvas tools (Python AI service)
- ✅ SSE streaming (Python AI service)
- ✅ Chat state management (Frontend)
- ✅ Message grouping logic (Frontend)

**Coverage: ~70% of core chat functionality**

## Test Requirements

### Python Tests
- pytest
- pytest-asyncio
- unittest.mock

### Express.js Tests
- mocha
- chai
- sinon

### Frontend Tests
- vitest
- @testing-library/react
- @testing-library/react-hooks

## Notes

- All tests use mocking to avoid database dependencies
- Tests focus on core business logic and state management
- Integration tests are in separate task (Task 24)
