"""
Chat Router for Via Canvas AI Service

FastAPI router that handles chat endpoints with streaming responses.
Integrates AgentManager, SessionManager, and StreamEventProcessor.
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, Header, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from agent_manager import get_agent_manager
from session_manager import get_session_manager

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


# Request models
class ChatStreamRequest(BaseModel):
    """Request model for streaming chat"""
    message: str
    session_id: Optional[str] = None
    canvas_id: Optional[str] = None


@router.post("/stream")
async def stream_chat(
    request: ChatStreamRequest,
    x_session_id: Optional[str] = Header(None)
):
    """
    Stream chat responses using Server-Sent Events
    
    This endpoint receives chat messages and streams AI responses in real-time.
    It integrates with the Strands agent, NVIDIA NIM, and canvas tools.
    
    Args:
        request: Chat request with message and optional session/canvas IDs
        x_session_id: Optional session ID from header
        
    Returns:
        StreamingResponse with Server-Sent Events
        
    Headers:
        X-Session-ID: Session ID for conversation continuity
    """
    import re
    import json
    
    try:
        # Extract request data
        message = request.message
        canvas_id = request.canvas_id
        session_id = x_session_id or request.session_id
        
        # Validate message
        if not message or not message.strip():
            raise HTTPException(status_code=400, detail="Message is required")
        
        logger.info(f"📨 Received chat request")
        logger.info(f"   Session: {session_id or 'new'}")
        logger.info(f"   Canvas: {canvas_id or 'none'}")
        logger.info(f"   Message: {message[:100]}...")
        
        # Get managers
        session_manager = get_session_manager()
        agent_manager = get_agent_manager(session_manager)
        
        # Check if agent is available
        if not agent_manager.is_available():
            logger.error("Agent not available - check NVIDIA_NIM_API_KEY")
            raise HTTPException(
                status_code=503,
                detail="AI service not available. Please check configuration."
            )
        
        # Get or create session
        session_id = session_manager.get_or_create_session(session_id, canvas_id)
        logger.info(f"✅ Using session: {session_id}")
        
        # PRE-PROCESSING: Detect URLs and handle directly
        # This bypasses the orchestrator to avoid LLM adding commentary
        url_pattern = r'(?:https?://)?(?:www\.)?([a-zA-Z0-9-]+\.(?:com|org|dev|io|net|edu|gov|co|ai|app|tech|info|me|us|uk|ca|de|fr|jp|cn|in|au|br|ru|es|it|nl|se|no|dk|fi|pl|cz|gr|tr|za|mx|ar|cl|pe|ve|co\.uk|co\.in|co\.jp|co\.kr|co\.nz|co\.za|com\.au|com\.br|com\.mx|com\.ar|com\.co|com\.pe|com\.ve)(?:/[^\s]*)?)'
        
        url_match = re.search(url_pattern, message, re.IGNORECASE)
        
        if url_match and canvas_id:
            # Found URL - extract directly without orchestrator
            url = url_match.group(0)
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            logger.info(f"🔗 Detected URL, extracting directly: {url}")
            
            async def stream_url_extraction():
                """Stream URL extraction results directly"""
                try:
                    # Send init event
                    yield f"event: init\ndata: {json.dumps({'type': 'init'})}\n\n"
                    
                    # Send progress event
                    yield f"event: response\ndata: {json.dumps({'type': 'response', 'data': 'Extracting content from '})}\n\n"
                    yield f"event: response\ndata: {json.dumps({'type': 'response', 'data': url})}\n\n"
                    yield f"event: response\ndata: {json.dumps({'type': 'response', 'data': '...'})}\n\n"
                    
                    # Call extraction tool
                    from tools.canvas_tools import extract_url_content
                    result = extract_url_content(url=url, canvas_id=canvas_id, session_id=session_id)
                    
                    if result.get('success'):
                        # Send success message
                        response_text = f"\n\n✅ Created {result['total_cards']} cards from the URL"
                        yield f"event: response\ndata: {json.dumps({'type': 'response', 'data': response_text})}\n\n"
                    else:
                        # Send error message
                        error_text = f"\n\n❌ Failed to extract: {result.get('error', 'Unknown error')}"
                        yield f"event: response\ndata: {json.dumps({'type': 'response', 'data': error_text})}\n\n"
                    
                    # Send complete event
                    yield f"event: complete\ndata: {json.dumps({'type': 'complete', 'images': []})}\n\n"
                    
                except Exception as e:
                    logger.error(f"Error in URL extraction: {e}", exc_info=True)
                    yield f"event: error\ndata: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            
            return StreamingResponse(
                stream_url_extraction(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Session-ID": session_id,
                    "Access-Control-Expose-Headers": "X-Session-ID",
                }
            )
        
        # No URL detected - use orchestrator for normal chat
        # Stream responses from agent
        return StreamingResponse(
            agent_manager.stream_async(
                message=message,
                session_id=session_id,
                canvas_id=canvas_id,
                files=None
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Session-ID": session_id,
                "Access-Control-Expose-Headers": "X-Session-ID",
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in stream_chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/multimodal")
async def multimodal_chat(
    message: str = Form(...),
    session_id: Optional[str] = Form(None),
    canvas_id: Optional[str] = Form(None),
    files: List[UploadFile] = File(...),
    x_session_id: Optional[str] = Header(None)
):
    """
    Stream chat responses with file uploads (multimodal)
    
    This endpoint handles chat messages with attached files (images, PDFs).
    Files are saved temporarily and passed to the agent for processing.
    
    Args:
        message: Chat message text
        session_id: Optional session ID from form
        canvas_id: Optional canvas ID
        files: List of uploaded files
        x_session_id: Optional session ID from header
        
    Returns:
        StreamingResponse with Server-Sent Events
        
    Headers:
        X-Session-ID: Session ID for conversation continuity
    """
    import os
    import tempfile
    import shutil
    
    temp_files = []
    
    try:
        # Validate message
        if not message or not message.strip():
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Validate files
        if not files or len(files) == 0:
            raise HTTPException(status_code=400, detail="At least one file is required")
        
        logger.info(f"📎 Received multimodal chat request")
        logger.info(f"   Files: {len(files)}")
        logger.info(f"   Message: {message[:100]}...")
        
        # Save uploaded files temporarily
        for file in files:
            # Validate file type
            content_type = file.content_type or ''
            if not (content_type.startswith('image/') or content_type == 'application/pdf'):
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file type: {content_type}. Only images and PDFs are allowed."
                )
            
            # Validate file size (5MB for images, 10MB for PDFs)
            max_size = 10 * 1024 * 1024 if content_type == 'application/pdf' else 5 * 1024 * 1024
            file_content = await file.read()
            if len(file_content) > max_size:
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large: {file.filename}. Max size: {max_size / 1024 / 1024}MB"
                )
            
            # Save to temp file
            suffix = os.path.splitext(file.filename)[1] if file.filename else ''
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            temp_file.write(file_content)
            temp_file.close()
            temp_files.append(temp_file.name)
            
            logger.info(f"   Saved: {file.filename} → {temp_file.name}")
        
        # Get session ID
        final_session_id = x_session_id or session_id
        
        # Get managers
        session_manager = get_session_manager()
        agent_manager = get_agent_manager(session_manager)
        
        # Check if agent is available
        if not agent_manager.is_available():
            raise HTTPException(
                status_code=503,
                detail="AI service not available. Please check configuration."
            )
        
        # Get or create session
        final_session_id = session_manager.get_or_create_session(final_session_id, canvas_id)
        logger.info(f"✅ Using session: {final_session_id}")
        
        # Stream responses from agent with files
        async def stream_with_cleanup():
            """Stream responses and cleanup temp files when done"""
            try:
                async for event in agent_manager.stream_async(
                    message=message,
                    session_id=final_session_id,
                    canvas_id=canvas_id,
                    files=temp_files
                ):
                    yield event
            finally:
                # Cleanup temp files
                for temp_file in temp_files:
                    try:
                        os.unlink(temp_file)
                        logger.debug(f"Cleaned up temp file: {temp_file}")
                    except Exception as e:
                        logger.warning(f"Failed to cleanup temp file {temp_file}: {e}")
        
        return StreamingResponse(
            stream_with_cleanup(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Session-ID": final_session_id,
                "Access-Control-Expose-Headers": "X-Session-ID",
            }
        )
        
    except HTTPException:
        # Cleanup temp files on error
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass
        raise
    except Exception as e:
        # Cleanup temp files on error
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass
        logger.error(f"Error in multimodal_chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/session/{session_id}")
async def get_session_info(session_id: str):
    """
    Get session information
    
    Args:
        session_id: Session ID
        
    Returns:
        Session information dict
    """
    try:
        session_manager = get_session_manager()
        session_info = session_manager.get_session_info(session_id)
        
        if not session_info:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Convert datetime objects to ISO strings
        return {
            "id": session_info["id"],
            "canvas_id": session_info.get("canvas_id"),
            "created_at": session_info["created_at"].isoformat(),
            "last_activity": session_info["last_activity"].isoformat(),
            "message_count": len(session_info.get("messages", []))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session info: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/stats")
async def get_stats():
    """
    Get service statistics
    
    Returns:
        Service statistics including active sessions and agent status
    """
    try:
        session_manager = get_session_manager()
        agent_manager = get_agent_manager(session_manager)
        
        return {
            "active_sessions": session_manager.get_session_count(),
            "agent_available": agent_manager.is_available(),
            "service": "via-canvas-ai",
            "version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

