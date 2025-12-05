# Via Canvas AI Service

Python FastAPI service for AI chat operations using Strands + NVIDIA NIM.

## Setup

### 1. Create Virtual Environment

```bash
cd chat_service
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your NVIDIA_NIM_API_KEY
```

### 4. Run Development Server

```bash
uvicorn app:app --reload --port 8000
```

The service will be available at `http://localhost:8000`

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Architecture

- **FastAPI**: Async web framework
- **Strands**: AI agent orchestration
- **NVIDIA NIM**: LLM inference (meta/llama-3.1-70b-instruct)
- **PostgreSQL**: Shared database with Express.js backend

## Endpoints

- `POST /chat/stream` - Stream chat responses
- `GET /health` - Health check

## Development

```bash
# Run with auto-reload
uvicorn app:app --reload --port 8000

# Run with specific host
uvicorn app:app --host 0.0.0.0 --port 8000
```

## Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```
