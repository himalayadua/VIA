/**
 * Chat Proxy Router
 * 
 * Proxies chat requests from the frontend to the Python AI Service.
 * Handles streaming responses and session management.
 */

import express, { Request, Response } from 'express';
import { db } from '../db.js';
import { sessionService } from '../services/sessionService.js';
import { parseSSEChunk, extractStreamData, type SSEEvent } from '../utils/sseParser.js';

const router = express.Router();

// Python AI Service URL from environment
const PYTHON_AI_SERVICE_URL = process.env.PYTHON_AI_SERVICE_URL || 'http://localhost:8000';

/**
 * Proxy streaming chat to Python AI Service
 * POST /api/chat/stream
 */
router.post('/stream', async (req: Request, res: Response) => {
  const { message, session_id, canvas_id } = req.body;
  const sessionId = req.headers['x-session-id'] as string || session_id;

  if (!message || !message.trim()) {
    return res.status(400).json({ error: 'Message is required' });
  }

  try {
    console.log(`[Chat Proxy] Forwarding stream request to Python AI Service`);
    console.log(`[Chat Proxy] Session ID: ${sessionId || 'new'}, Canvas ID: ${canvas_id || 'none'}`);

    // Forward request to Python AI Service using fetch
    const response = await fetch(`${PYTHON_AI_SERVICE_URL}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Session-ID': sessionId || '',
      },
      body: JSON.stringify({ message, session_id: sessionId, canvas_id }),
    });

    if (!response.ok) {
      throw new Error(`Python AI Service returned ${response.status}: ${response.statusText}`);
    }

    // Get session ID from response headers
    const responseSessionId = response.headers.get('x-session-id') || sessionId;

    // Save user message to database
    try {
      await sessionService.saveMessage(responseSessionId, 'user', message);
      console.log('[Chat Proxy] Saved user message to database');
    } catch (error) {
      console.error('[Chat Proxy] Error saving user message:', error);
      // Continue even if save fails
    }

    // Set SSE headers
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');
    res.setHeader('X-Session-ID', responseSessionId);
    res.setHeader('Access-Control-Expose-Headers', 'X-Session-ID');

    // Collect stream chunks for parsing
    const streamChunks: string[] = [];
    const allEvents: SSEEvent[] = [];

    // Pipe the response stream
    if (response.body) {
      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          
          const chunk = decoder.decode(value, { stream: true });
          streamChunks.push(chunk);
          
          // Parse events from this chunk
          const events = parseSSEChunk(chunk);
          allEvents.push(...events);
          
          // Forward to frontend
          res.write(chunk);
        }
      } catch (error) {
        console.error('[Chat Proxy] Stream error:', error);
      } finally {
        reader.releaseLock();
        res.end();
      }
    } else {
      res.end();
    }

    // After streaming completes, save assistant message
    try {
      const streamData = extractStreamData(allEvents);
      
      if (streamData.responseText) {
        await sessionService.saveMessage(
          responseSessionId,
          'assistant',
          streamData.responseText,
          {
            toolExecutions: streamData.toolExecutions,
            images: streamData.images
          }
        );
        console.log('[Chat Proxy] Saved assistant message to database');
      }
    } catch (error) {
      console.error('[Chat Proxy] Error saving assistant message:', error);
      // Don't throw - streaming already completed
    }

  } catch (error) {
    console.error('[Chat Proxy] Error proxying to Python AI service:', error);
    
    // Send error as SSE event
    const errorEvent = `event: error\ndata: ${JSON.stringify({
      type: 'error',
      message: error instanceof Error ? error.message : 'Failed to connect to AI service'
    })}\n\n`;
    
    res.write(errorEvent);
    res.end();
  }
});

/**
 * Proxy multimodal chat with file upload
 * POST /api/chat/multimodal
 * 
 * Note: This endpoint forwards multipart/form-data directly to the Python service.
 * The Python service handles file parsing and temporary storage.
 */
router.post('/multimodal', async (req: Request, res: Response) => {
  const sessionId = req.headers['x-session-id'] as string;

  try {
    console.log('[Chat Proxy] Forwarding multimodal request to Python AI Service');
    console.log(`[Chat Proxy] Session ID: ${sessionId || 'new'}`);

    // Get the content type from the request
    const contentType = req.headers['content-type'] || '';
    
    if (!contentType.includes('multipart/form-data')) {
      return res.status(400).json({ 
        error: 'Invalid content type',
        message: 'Expected multipart/form-data for file uploads'
      });
    }

    // Forward the entire request body to Python service
    // Python service will handle multipart parsing with FastAPI's UploadFile
    const response = await fetch(`${PYTHON_AI_SERVICE_URL}/chat/multimodal`, {
      method: 'POST',
      headers: {
        'Content-Type': contentType,
        'X-Session-ID': sessionId || '',
      },
      // @ts-ignore - req is a readable stream
      body: req,
      duplex: 'half'
    });

    if (!response.ok) {
      throw new Error(`Python AI Service returned ${response.status}: ${response.statusText}`);
    }

    // Get session ID from response headers
    const responseSessionId = response.headers.get('x-session-id') || sessionId;

    // Set SSE headers
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');
    res.setHeader('X-Session-ID', responseSessionId);
    res.setHeader('Access-Control-Expose-Headers', 'X-Session-ID');

    // Pipe the response stream
    if (response.body) {
      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          
          const chunk = decoder.decode(value, { stream: true });
          res.write(chunk);
        }
      } catch (error) {
        console.error('[Chat Proxy] Stream error:', error);
      } finally {
        reader.releaseLock();
        res.end();
      }
    } else {
      res.end();
    }

  } catch (error) {
    console.error('[Chat Proxy] Error proxying multimodal request:', error);
    
    // Send error as SSE event
    const errorEvent = `event: error\ndata: ${JSON.stringify({
      type: 'error',
      message: error instanceof Error ? error.message : 'Failed to connect to AI service'
    })}\n\n`;
    
    res.write(errorEvent);
    res.end();
  }
});

/**
 * Get chat history from PostgreSQL
 * GET /api/chat/history/:sessionId
 */
router.get('/history/:sessionId', async (req: Request, res: Response) => {
  const { sessionId } = req.params;
  const limit = parseInt(req.query.limit as string) || 50;

  try {
    const messages = await sessionService.getChatHistory(sessionId, limit);

    res.json({
      session_id: sessionId,
      messages: messages,
      count: messages.length
    });

  } catch (error) {
    console.error('[Chat Proxy] Error fetching chat history:', error);
    res.status(500).json({
      error: 'Failed to fetch chat history',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

/**
 * Create new chat session
 * POST /api/chat/session
 */
router.post('/session', async (req: Request, res: Response) => {
  const { canvas_id } = req.body;

  try {
    const sessionId = await sessionService.createSession(canvas_id);
    const session = await sessionService.getSession(sessionId);

    res.json({
      session_id: sessionId,
      canvas_id: session?.canvas_id || null,
      created_at: session?.created_at
    });

  } catch (error) {
    console.error('[Chat Proxy] Error creating session:', error);
    res.status(500).json({
      error: 'Failed to create session',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

/**
 * Delete chat session and all messages
 * DELETE /api/chat/session/:sessionId
 */
router.delete('/session/:sessionId', async (req: Request, res: Response) => {
  const { sessionId } = req.params;

  try {
    await sessionService.clearSession(sessionId);

    res.json({
      success: true,
      session_id: sessionId,
      message: 'Session and all messages deleted'
    });

  } catch (error) {
    if (error instanceof Error && error.message === 'Session not found') {
      return res.status(404).json({ error: 'Session not found' });
    }
    
    console.error('[Chat Proxy] Error deleting session:', error);
    res.status(500).json({
      error: 'Failed to delete session',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

/**
 * Cleanup inactive sessions
 * POST /api/chat/cleanup
 */
router.post('/cleanup', async (req: Request, res: Response) => {
  const maxAgeHours = parseInt(req.body.max_age_hours as string) || 24;

  try {
    const deletedCount = await sessionService.cleanupInactiveSessions(maxAgeHours);

    res.json({
      success: true,
      deleted_count: deletedCount,
      max_age_hours: maxAgeHours
    });

  } catch (error) {
    console.error('[Chat Proxy] Error cleaning up sessions:', error);
    res.status(500).json({
      error: 'Failed to cleanup sessions',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

export default router;
