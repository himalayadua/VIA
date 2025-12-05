# Knowledge Base - Quick Start Guide

## Setup (5 minutes)

### 1. Start Qdrant

```bash
# Start Qdrant container
docker-compose up -d qdrant

# Verify it's running
curl http://localhost:6333/health
# Should return: {"title":"qdrant - vector search engine","version":"..."}
```

### 2. Run Database Migration

```bash
# Apply migration
psql -h localhost -U viacanvas -d via_canvas -f supabase/migrations/20251117000000_create_rag_index_tracking.sql

# Verify table was created
psql -h localhost -U viacanvas -d via_canvas -c "\d rag_index_tracking"
```

### 3. Install Dependencies

```bash
cd chat_service
pip install qdrant-client sentence-transformers
```

### 4. Configure Environment

```bash
# Add to .env file
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=via_canvas_kb
RAG_CHUNK_SIZE=500
RAG_CHUNK_OVERLAP=50
```

### 5. Start Service

```bash
python app.py
```

## Test It (2 minutes)

### 1. Check Status

```bash
curl http://localhost:8000/api/knowledge-base/status
```

Expected response:
```json
{
  "status": "operational",
  "backend": "qdrant",
  "collection": "via_canvas_kb"
}
```

### 2. Index a Test Card

```bash
curl -X POST http://localhost:8000/api/knowledge-base/index \
  -H "Content-Type: application/json" \
  -d '{
    "card_id": "test-card-1",
    "canvas_id": "test-canvas",
    "content": "Machine learning is a subset of artificial intelligence that focuses on building systems that can learn from data.",
    "card_type": "richtext"
  }'
```

Expected response:
```json
{
  "indexed": true,
  "card_id": "test-card-1",
  "num_chunks": 1,
  "point_ids": ["..."]
}
```

### 3. Search

```bash
curl -X POST http://localhost:8000/api/knowledge-base/search \
  -H "Content-Type": application/json" \
  -d '{
    "query": "What is machine learning?",
    "canvas_id": "test-canvas",
    "top_k": 5
  }'
```

Expected response:
```json
{
  "success": true,
  "results": [
    {
      "id": "...",
      "score": 0.92,
      "content": "Machine learning is a subset...",
      "card_id": "test-card-1"
    }
  ],
  "count": 1
}
```

### 4. Get Stats

```bash
curl http://localhost:8000/api/knowledge-base/stats?canvas_id=test-canvas
```

## Use in Code

### Python

```python
from knowledge_base import RAGService

# Index a card
result = await rag_service.index_card(
    card_id="card-123",
    content="Your content here...",
    canvas_id="canvas-456",
    card_type="richtext"
)

# Search
results = await rag_service.search_knowledge_base(
    query="your question",
    canvas_id="canvas-456",
    top_k=5
)

# Get context for RAG
context = await rag_service.retrieve_context(
    query="your question",
    canvas_id="canvas-456"
)
```

### Strands Tools

```python
from tools.knowledge_base_tools import search_knowledge_base, get_knowledge_context

# In agent
agent = Agent(
    name="Assistant",
    tools=[search_knowledge_base, get_knowledge_context]
)

# Agent can now search automatically
```

## Monitoring

### Qdrant Dashboard
http://localhost:6333/dashboard

### Check Indexed Entities

```sql
SELECT entity_id, num_chunks, index_status, indexed_at
FROM rag_index_tracking
WHERE canvas_id = 'your-canvas-id'
ORDER BY indexed_at DESC;
```

### View Stats

```bash
curl http://localhost:8000/api/knowledge-base/stats
```

## Troubleshooting

### Qdrant not starting?
```bash
docker logs via-canvas-qdrant
```

### Migration failed?
```bash
# Check if table exists
psql -h localhost -U viacanvas -d via_canvas -c "\dt rag_*"
```

### Service not initializing?
Check logs for:
```
✅ RAG Service initialized successfully
```

If you see errors, check:
1. Qdrant is running
2. Database connection works
3. Dependencies installed

## Next Steps

1. **Auto-Indexing**: Hook into card creation/update
2. **Chat Integration**: Add RAG to chat responses
3. **UI**: Build knowledge base panel

## Documentation

- Full docs: `.kiro/specs/refly-integration/WEEK_6_7_IMPLEMENTATION_COMPLETE.md`
- Analysis: `.kiro/specs/refly-integration/WEEK_6_7_KNOWLEDGE_BASE_ANALYSIS.md`
