"""
Via Canvas AI Service - FastAPI Application

Main application entry point for the Python AI service that handles
chat operations using Strands agents with NVIDIA NIM.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import sys
import asyncio
from session_manager import get_session_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Via Canvas AI Service",
    description="Python FastAPI service for AI chat operations with Strands + NVIDIA NIM",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware - will be configured from environment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Will be loaded from config
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Session-ID"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "via-canvas-ai",
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Via Canvas AI Service",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc)
        }
    )

# Background task for session cleanup
cleanup_task = None

async def cleanup_sessions_periodically():
    """Background task to cleanup inactive sessions every hour"""
    session_manager = get_session_manager()
    
    while True:
        try:
            await asyncio.sleep(3600)  # Wait 1 hour
            deleted_count = session_manager.cleanup_inactive_sessions(max_age_hours=24)
            if deleted_count > 0:
                logger.info(f"🧹 Cleaned up {deleted_count} inactive sessions")
        except asyncio.CancelledError:
            logger.info("Session cleanup task cancelled")
            break
        except Exception as e:
            logger.error(f"Error in session cleanup task: {e}", exc_info=True)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    global cleanup_task
    
    logger.info("🚀 Via Canvas AI Service starting up...")
    
    # Validate database connection
    try:
        import psycopg2
        from config import settings
        
        conn = psycopg2.connect(
            host=settings.db_host,
            port=settings.db_port,
            database=settings.db_name,
            user=settings.db_user,
            password=settings.db_password
        )
        conn.close()
        logger.info("✅ Database connection validated")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        logger.error("   Service will start but database operations will fail")
    
    # Validate NVIDIA NIM API key
    from config import settings
    if not settings.nvidia_nim_api_key:
        logger.warning("⚠️  NVIDIA_NIM_API_KEY not set! AI features will not work.")
    else:
        logger.info("✅ NVIDIA NIM API key configured")
    
    # Initialize RAG Service
    try:
        from knowledge_base import VectorStore, RAGService, IndexTracker
        from graph.embedding_provider import EmbeddingProvider
        from tools import knowledge_base_tools
        from routers import knowledge_base as kb_router
        
        # Initialize components
        vector_store = VectorStore(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
            collection_name=settings.qdrant_collection,
            api_key=settings.qdrant_api_key if settings.qdrant_api_key else None
        )
        
        index_tracker = IndexTracker(settings.get_db_config())
        
        embedding_provider = EmbeddingProvider()
        
        rag_service = RAGService(
            vector_store=vector_store,
            index_tracker=index_tracker,
            embedding_provider=embedding_provider,
            chunk_size=settings.rag_chunk_size,
            chunk_overlap=settings.rag_chunk_overlap
        )
        
        # Set global instances
        knowledge_base_tools.set_rag_service(rag_service)
        kb_router.set_rag_service(rag_service)
        
        # Initialize auto-indexer
        from knowledge_base.auto_indexer import set_rag_service as set_auto_indexer_rag_service
        set_auto_indexer_rag_service(rag_service)
        
        logger.info("✅ RAG Service initialized successfully")
        logger.info(f"   - Qdrant: {settings.qdrant_host}:{settings.qdrant_port}")
        logger.info(f"   - Collection: {settings.qdrant_collection}")
        logger.info(f"   - Chunk size: {settings.rag_chunk_size} words")
        logger.info(f"   - Auto-indexing: Enabled")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize RAG Service: {e}")
        logger.error("   Knowledge base features will not be available")
    
    logger.info("📝 API documentation available at /docs")
    logger.info("❤️  Health check available at /health")
    
    # Start session cleanup background task
    cleanup_task = asyncio.create_task(cleanup_sessions_periodically())
    logger.info("🧹 Session cleanup task started (runs every hour)")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    global cleanup_task
    
    logger.info("👋 Via Canvas AI Service shutting down...")
    
    # Cancel cleanup task
    if cleanup_task:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass
        logger.info("🧹 Session cleanup task stopped")

# Import and include routers
from routers import chat
from routers import knowledge_base

app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(knowledge_base.router)

logger.info("📡 Chat router registered at /chat")
logger.info("📡 Knowledge Base router registered at /api/knowledge-base")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
