/**
 * AI Features Router
 * 
 * Express routes for AI-powered canvas features:
 * - Grow card (expand card with AI-generated concepts)
 * - Batch URL extraction
 * - Operation status tracking
 */

import express, { Request, Response } from 'express';
import { db } from '../db.js';

const router = express.Router();

// Python AI Service URL from environment
const PYTHON_AI_SERVICE_URL = process.env.PYTHON_AI_SERVICE_URL || 'http://localhost:8000';

/**
 * POST /api/ai/cards/:id/grow
 * 
 * Grow a card by analyzing its content and creating connected child cards
 * with key concepts extracted by AI.
 */
router.post('/cards/:id/grow', async (req: Request, res: Response) => {
  const { id: cardId } = req.params;
  const { num_concepts = 3, canvas_id } = req.body;
  const sessionId = req.headers['x-session-id'] as string;

  try {
    console.log(`[AI Features] Grow card request: ${cardId}`);

    // Validate card exists
    const cardResult = await db.query(
      'SELECT * FROM nodes WHERE id = $1',
      [cardId]
    );

    if (cardResult.rows.length === 0) {
      return res.status(404).json({ error: 'Card not found' });
    }

    const card = cardResult.rows[0];

    // Validate canvas_id matches
    if (card.canvas_id !== canvas_id) {
      return res.status(400).json({ 
        error: 'Card does not belong to specified canvas' 
      });
    }

    // Validate card has content
    if (!card.content || card.content.trim() === '') {
      return res.status(400).json({ 
        error: 'Card has no content to analyze' 
      });
    }

    // Forward request to Python AI Service
    const response = await fetch(`${PYTHON_AI_SERVICE_URL}/ai/grow`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Session-ID': sessionId || '',
      },
      body: JSON.stringify({
        card_id: cardId,
        canvas_id: canvas_id,
        num_concepts: num_concepts,
        card_content: card.content,
        card_title: card.title
      }),
    });

    if (!response.ok) {
      throw new Error(`Python AI Service returned ${response.status}`);
    }

    // Get operation ID from response headers
    const operationId = response.headers.get('x-operation-id');

    // Set SSE headers
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');
    if (operationId) {
      res.setHeader('X-Operation-ID', operationId);
      res.setHeader('Access-Control-Expose-Headers', 'X-Operation-ID');
    }

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
      } finally {
        reader.releaseLock();
        res.end();
      }
    } else {
      res.end();
    }

  } catch (error) {
    console.error('[AI Features] Error in grow endpoint:', error);
    
    const errorEvent = `event: error\ndata: ${JSON.stringify({
      type: 'error',
      message: error instanceof Error ? error.message : 'Failed to grow card'
    })}\n\n`;
    
    res.write(errorEvent);
    res.end();
  }
});

/**
 * POST /api/ai/cards/:id/simplify
 * 
 * Simplify complex content into easy-to-understand explanations (ELI5).
 */
router.post('/cards/:id/simplify', async (req: Request, res: Response) => {
  const { id: cardId } = req.params;
  const { canvas_id, create_card_option = false } = req.body;
  const sessionId = req.headers['x-session-id'] as string;

  try {
    console.log(`[AI Features] Simplify request for card: ${cardId}`);

    // Validate card exists
    const cardResult = await db.query('SELECT * FROM nodes WHERE id = $1', [cardId]);
    if (cardResult.rows.length === 0) {
      return res.status(404).json({ error: 'Card not found' });
    }

    const card = cardResult.rows[0];

    // Validate canvas_id matches
    if (card.canvas_id !== canvas_id) {
      return res.status(400).json({ error: 'Card does not belong to specified canvas' });
    }

    // Forward to Python AI Service
    const response = await fetch(`${PYTHON_AI_SERVICE_URL}/ai/learning/simplify`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Session-ID': sessionId || '',
      },
      body: JSON.stringify({
        card_id: cardId,
        canvas_id,
        create_card_option,
        card_content: card.content,
        card_title: card.title
      })
    });

    if (!response.ok) {
      throw new Error(`Python AI Service returned ${response.status}`);
    }

    const result = await response.json();
    res.json(result);

  } catch (error) {
    console.error('[AI Features] Error in simplify endpoint:', error);
    res.status(500).json({
      error: 'Failed to simplify explanation',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

/**
 * POST /api/ai/cards/:id/find-examples
 * 
 * Find real-world applications and use cases for a topic.
 */
router.post('/cards/:id/find-examples', async (req: Request, res: Response) => {
  const { id: cardId } = req.params;
  const { canvas_id, create_card_option = false } = req.body;
  const sessionId = req.headers['x-session-id'] as string;

  try {
    console.log(`[AI Features] Find examples request for card: ${cardId}`);

    const cardResult = await db.query('SELECT * FROM nodes WHERE id = $1', [cardId]);
    if (cardResult.rows.length === 0) {
      return res.status(404).json({ error: 'Card not found' });
    }

    const card = cardResult.rows[0];

    if (card.canvas_id !== canvas_id) {
      return res.status(400).json({ error: 'Card does not belong to specified canvas' });
    }

    const response = await fetch(`${PYTHON_AI_SERVICE_URL}/ai/learning/find-examples`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Session-ID': sessionId || '',
      },
      body: JSON.stringify({
        card_id: cardId,
        canvas_id,
        create_card_option,
        topic: card.title || card.content?.substring(0, 100),
        card_content: card.content,
        card_title: card.title
      })
    });

    if (!response.ok) {
      throw new Error(`Python AI Service returned ${response.status}`);
    }

    const result = await response.json();
    res.json(result);

  } catch (error) {
    console.error('[AI Features] Error in find-examples endpoint:', error);
    res.status(500).json({
      error: 'Failed to find examples',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

/**
 * POST /api/ai/cards/:id/find-gaps
 * 
 * Analyze knowledge gaps - find missing prerequisites and advanced topics.
 */
router.post('/cards/:id/find-gaps', async (req: Request, res: Response) => {
  const { id: cardId } = req.params;
  const { canvas_id, create_card_option = false } = req.body;
  const sessionId = req.headers['x-session-id'] as string;

  try {
    console.log(`[AI Features] Find gaps request for card: ${cardId}`);

    const cardResult = await db.query('SELECT * FROM nodes WHERE id = $1', [cardId]);
    if (cardResult.rows.length === 0) {
      return res.status(404).json({ error: 'Card not found' });
    }

    const card = cardResult.rows[0];

    if (card.canvas_id !== canvas_id) {
      return res.status(400).json({ error: 'Card does not belong to specified canvas' });
    }

    const response = await fetch(`${PYTHON_AI_SERVICE_URL}/ai/learning/find-gaps`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Session-ID': sessionId || '',
      },
      body: JSON.stringify({
        card_ids: [cardId],
        canvas_id,
        create_card_option,
        card_content: card.content,
        card_title: card.title
      })
    });

    if (!response.ok) {
      throw new Error(`Python AI Service returned ${response.status}`);
    }

    const result = await response.json();
    res.json(result);

  } catch (error) {
    console.error('[AI Features] Error in find-gaps endpoint:', error);
    res.status(500).json({
      error: 'Failed to analyze knowledge gaps',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

/**
 * POST /api/ai/cards/:id/go-deeper
 * 
 * Find academic papers and research sources.
 */
router.post('/cards/:id/go-deeper', async (req: Request, res: Response) => {
  const { id: cardId } = req.params;
  const { canvas_id, create_card_option = false, max_papers = 5 } = req.body;
  const sessionId = req.headers['x-session-id'] as string;

  try {
    console.log(`[AI Features] Go deeper request for card: ${cardId}`);

    const cardResult = await db.query('SELECT * FROM nodes WHERE id = $1', [cardId]);
    if (cardResult.rows.length === 0) {
      return res.status(404).json({ error: 'Card not found' });
    }

    const card = cardResult.rows[0];

    if (card.canvas_id !== canvas_id) {
      return res.status(400).json({ error: 'Card does not belong to specified canvas' });
    }

    const response = await fetch(`${PYTHON_AI_SERVICE_URL}/ai/learning/go-deeper`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Session-ID': sessionId || '',
      },
      body: JSON.stringify({
        topic: card.title || card.content?.substring(0, 100),
        card_id: cardId,
        canvas_id,
        create_card_option,
        max_papers,
        card_content: card.content,
        card_title: card.title
      })
    });

    if (!response.ok) {
      throw new Error(`Python AI Service returned ${response.status}`);
    }

    const result = await response.json();
    res.json(result);

  } catch (error) {
    console.error('[AI Features] Error in go-deeper endpoint:', error);
    res.status(500).json({
      error: 'Failed to find academic sources',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

/**
 * POST /api/ai/cards/:id/challenge
 * 
 * Find counter-arguments and alternative perspectives.
 */
router.post('/cards/:id/challenge', async (req: Request, res: Response) => {
  const { id: cardId } = req.params;
  const { canvas_id, create_card_option = false } = req.body;
  const sessionId = req.headers['x-session-id'] as string;

  try {
    console.log(`[AI Features] Challenge request for card: ${cardId}`);

    const cardResult = await db.query('SELECT * FROM nodes WHERE id = $1', [cardId]);
    if (cardResult.rows.length === 0) {
      return res.status(404).json({ error: 'Card not found' });
    }

    const card = cardResult.rows[0];

    if (card.canvas_id !== canvas_id) {
      return res.status(400).json({ error: 'Card does not belong to specified canvas' });
    }

    const response = await fetch(`${PYTHON_AI_SERVICE_URL}/ai/learning/challenge`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Session-ID': sessionId || '',
      },
      body: JSON.stringify({
        topic: card.title || card.content?.substring(0, 100),
        card_id: cardId,
        canvas_id,
        create_card_option,
        card_content: card.content,
        card_title: card.title
      })
    });

    if (!response.ok) {
      throw new Error(`Python AI Service returned ${response.status}`);
    }

    const result = await response.json();
    res.json(result);

  } catch (error) {
    console.error('[AI Features] Error in challenge endpoint:', error);
    res.status(500).json({
      error: 'Failed to find counterpoints',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

/**
 * POST /api/ai/cards/:id/connect-dots
 * 
 * Find surprising connections between topics.
 */
router.post('/cards/:id/connect-dots', async (req: Request, res: Response) => {
  const { id: cardId } = req.params;
  const { canvas_id, create_card_option = false } = req.body;
  const sessionId = req.headers['x-session-id'] as string;

  try {
    console.log(`[AI Features] Connect dots request for card: ${cardId}`);

    const cardResult = await db.query('SELECT * FROM nodes WHERE id = $1', [cardId]);
    if (cardResult.rows.length === 0) {
      return res.status(404).json({ error: 'Card not found' });
    }

    const card = cardResult.rows[0];

    if (card.canvas_id !== canvas_id) {
      return res.status(400).json({ error: 'Card does not belong to specified canvas' });
    }

    const response = await fetch(`${PYTHON_AI_SERVICE_URL}/ai/learning/connect-dots`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Session-ID': sessionId || '',
      },
      body: JSON.stringify({
        card_ids: [cardId],
        canvas_id,
        create_card_option,
        card_content: card.content,
        card_title: card.title
      })
    });

    if (!response.ok) {
      throw new Error(`Python AI Service returned ${response.status}`);
    }

    const result = await response.json();
    res.json(result);

  } catch (error) {
    console.error('[AI Features] Error in connect-dots endpoint:', error);
    res.status(500).json({
      error: 'Failed to find connections',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

/**
 * POST /api/ai/cards/:id/update
 * 
 * Refresh outdated content with recent developments.
 */
router.post('/cards/:id/update', async (req: Request, res: Response) => {
  const { id: cardId } = req.params;
  const { canvas_id, create_card_option = false } = req.body;
  const sessionId = req.headers['x-session-id'] as string;

  try {
    console.log(`[AI Features] Update request for card: ${cardId}`);

    const cardResult = await db.query('SELECT * FROM nodes WHERE id = $1', [cardId]);
    if (cardResult.rows.length === 0) {
      return res.status(404).json({ error: 'Card not found' });
    }

    const card = cardResult.rows[0];

    if (card.canvas_id !== canvas_id) {
      return res.status(400).json({ error: 'Card does not belong to specified canvas' });
    }

    const response = await fetch(`${PYTHON_AI_SERVICE_URL}/ai/learning/update`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Session-ID': sessionId || '',
      },
      body: JSON.stringify({
        topic: card.title || card.content?.substring(0, 100),
        card_id: cardId,
        canvas_id,
        create_card_option,
        card_content: card.content,
        card_title: card.title
      })
    });

    if (!response.ok) {
      throw new Error(`Python AI Service returned ${response.status}`);
    }

    const result = await response.json();
    res.json(result);

  } catch (error) {
    console.error('[AI Features] Error in update endpoint:', error);
    res.status(500).json({
      error: 'Failed to update information',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

/**
 * POST /api/ai/cards/:id/action-plan
 * 
 * Convert knowledge to actionable implementation steps.
 */
router.post('/cards/:id/action-plan', async (req: Request, res: Response) => {
  const { id: cardId } = req.params;
  const { canvas_id, create_card_option = false } = req.body;
  const sessionId = req.headers['x-session-id'] as string;

  try {
    console.log(`[AI Features] Action plan request for card: ${cardId}`);

    const cardResult = await db.query('SELECT * FROM nodes WHERE id = $1', [cardId]);
    if (cardResult.rows.length === 0) {
      return res.status(404).json({ error: 'Card not found' });
    }

    const card = cardResult.rows[0];

    if (card.canvas_id !== canvas_id) {
      return res.status(400).json({ error: 'Card does not belong to specified canvas' });
    }

    const response = await fetch(`${PYTHON_AI_SERVICE_URL}/ai/learning/action-plan`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Session-ID': sessionId || '',
      },
      body: JSON.stringify({
        topic: card.title || card.content?.substring(0, 100),
        card_ids: [cardId],
        canvas_id,
        create_card_option,
        card_content: card.content,
        card_title: card.title
      })
    });

    if (!response.ok) {
      throw new Error(`Python AI Service returned ${response.status}`);
    }

    const result = await response.json();
    res.json(result);

  } catch (error) {
    console.error('[AI Features] Error in action-plan endpoint:', error);
    res.status(500).json({
      error: 'Failed to create action plan',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

/**
 * POST /api/ai/canvas/:id/comprehensive-learn
 * 
 * Execute comprehensive learning workflow for a card/topic.
 * Creates a complete knowledge cluster with multiple related cards.
 */
router.post('/canvas/:id/comprehensive-learn', async (req: Request, res: Response) => {
  const { id: canvasId } = req.params;
  const { card_id, topic, depth = 'standard' } = req.body;
  const sessionId = req.headers['x-session-id'] as string;

  try {
    console.log(`[AI Features] Comprehensive learn request for canvas: ${canvasId}`);

    // Validate canvas exists
    const canvasResult = await db.query('SELECT * FROM canvases WHERE id = $1', [canvasId]);
    if (canvasResult.rows.length === 0) {
      return res.status(404).json({ error: 'Canvas not found' });
    }

    // If card_id provided, validate it exists and get topic from it
    let topicToLearn = topic;
    if (card_id) {
      const cardResult = await db.query('SELECT * FROM nodes WHERE id = $1', [card_id]);
      if (cardResult.rows.length === 0) {
        return res.status(404).json({ error: 'Card not found' });
      }
      
      const card = cardResult.rows[0];
      if (card.canvas_id !== canvasId) {
        return res.status(400).json({ error: 'Card does not belong to specified canvas' });
      }
      
      // Use card title as topic if not provided
      topicToLearn = topic || card.title || card.content?.substring(0, 100);
    }

    if (!topicToLearn) {
      return res.status(400).json({ error: 'Either card_id or topic is required' });
    }

    // Forward to Python AI Service
    const response = await fetch(`${PYTHON_AI_SERVICE_URL}/ai/learning/comprehensive-learn`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Session-ID': sessionId || '',
      },
      body: JSON.stringify({
        canvas_id: canvasId,
        card_id: card_id || null,
        topic: topicToLearn,
        depth: depth
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Python AI Service returned ${response.status}: ${errorText}`);
    }

    const result = await response.json();
    res.json(result);

  } catch (error) {
    console.error('[AI Features] Error in comprehensive-learn endpoint:', error);
    res.status(500).json({
      error: 'Failed to execute comprehensive learning',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

/**
 * POST /api/ai/canvas/:id/talk
 * 
 * Have a conversation about the canvas content.
 * Enables natural language queries about cards, relationships, and insights.
 */
router.post('/canvas/:id/talk', async (req: Request, res: Response) => {
  const { id: canvasId } = req.params;
  const { message, context = {} } = req.body;
  const sessionId = req.headers['x-session-id'] as string;

  try {
    console.log(`[AI Features] Talk to canvas request: ${canvasId}`);

    // Validate canvas exists
    const canvasResult = await db.query('SELECT * FROM canvases WHERE id = $1', [canvasId]);
    if (canvasResult.rows.length === 0) {
      return res.status(404).json({ error: 'Canvas not found' });
    }

    if (!message || typeof message !== 'string' || message.trim() === '') {
      return res.status(400).json({ error: 'message is required' });
    }

    // Get all cards on canvas for context
    const cardsResult = await db.query(
      'SELECT id, title, content, card_type, tags FROM nodes WHERE canvas_id = $1',
      [canvasId]
    );

    // Forward to Python AI Service
    const response = await fetch(`${PYTHON_AI_SERVICE_URL}/ai/canvas/talk`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Session-ID': sessionId || '',
      },
      body: JSON.stringify({
        canvas_id: canvasId,
        message: message,
        cards: cardsResult.rows,
        context: context
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Python AI Service returned ${response.status}: ${errorText}`);
    }

    const result = await response.json();
    res.json(result);

  } catch (error) {
    console.error('[AI Features] Error in talk endpoint:', error);
    res.status(500).json({
      error: 'Failed to process canvas conversation',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

export default router;

/**
 * POST /api/ai/extract/batch
 * 
 * Extract content from multiple URLs in parallel and create cards.
 */
router.post('/extract/batch', async (req: Request, res: Response) => {
  const { urls, canvas_id, parent_id } = req.body;
  const sessionId = req.headers['x-session-id'] as string;

  try {
    console.log(`[AI Features] Batch extraction request`);
    console.log(`[AI Features] URLs: ${urls?.length || 0}, Canvas: ${canvas_id}`);

    // Validate input
    if (!urls || !Array.isArray(urls) || urls.length === 0) {
      return res.status(400).json({ 
        error: 'urls array is required and must not be empty' 
      });
    }

    if (!canvas_id) {
      return res.status(400).json({ error: 'canvas_id is required' });
    }

    // Validate URL format
    const urlPattern = /^https?:\/\/.+/i;
    for (const url of urls) {
      if (typeof url !== 'string' || !urlPattern.test(url)) {
        return res.status(400).json({ 
          error: `Invalid URL format: ${url}` 
        });
      }
    }

    // Validate canvas exists
    const canvasResult = await db.query(
      'SELECT id FROM canvases WHERE id = $1',
      [canvas_id]
    );

    if (canvasResult.rows.length === 0) {
      return res.status(404).json({ error: 'Canvas not found' });
    }

    // Forward request to Python AI Service
    const response = await fetch(`${PYTHON_AI_SERVICE_URL}/ai/extract/batch`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Session-ID': sessionId || '',
      },
      body: JSON.stringify({
        urls: urls,
        canvas_id: canvas_id,
        parent_id: parent_id || null
      }),
    });

    if (!response.ok) {
      throw new Error(`Python AI Service returned ${response.status}`);
    }

    // Get operation ID from response headers
    const operationId = response.headers.get('x-operation-id');

    // Set SSE headers
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');
    if (operationId) {
      res.setHeader('X-Operation-ID', operationId);
      res.setHeader('Access-Control-Expose-Headers', 'X-Operation-ID');
    }

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
      } finally {
        reader.releaseLock();
        res.end();
      }
    } else {
      res.end();
    }

  } catch (error) {
    console.error('[AI Features] Error in batch extract endpoint:', error);
    
    const errorEvent = `event: error\ndata: ${JSON.stringify({
      type: 'error',
      message: error instanceof Error ? error.message : 'Failed to extract URLs'
    })}\n\n`;
    
    res.write(errorEvent);
    res.end();
  }
});

/**
 * GET /api/ai/operations/:id/status
 * 
 * Get the status of a long-running operation.
 */
router.get('/operations/:id/status', async (req: Request, res: Response) => {
  const { id: operationId } = req.params;

  try {
    console.log(`[AI Features] Status check for operation: ${operationId}`);

    // Fetch checkpoint from database
    const result = await db.query(
      `SELECT * FROM operation_checkpoints 
       WHERE operation_id = $1 
       ORDER BY updated_at DESC 
       LIMIT 1`,
      [operationId]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Operation not found' });
    }

    const checkpoint = result.rows[0];
    const state = checkpoint.state || {};

    // Calculate progress percentage
    const currentStep = state.current_step || 0;
    const totalSteps = state.total_steps || 1;
    const progress = Math.round((currentStep / totalSteps) * 100);

    // Estimate time remaining
    let estimatedTimeRemaining = null;
    if (state.started_at && currentStep > 0 && currentStep < totalSteps) {
      const startTime = new Date(state.started_at).getTime();
      const now = Date.now();
      const elapsed = now - startTime;
      const avgTimePerStep = elapsed / currentStep;
      const stepsRemaining = totalSteps - currentStep;
      estimatedTimeRemaining = Math.round((avgTimePerStep * stepsRemaining) / 1000); // seconds
    }

    res.json({
      operation_id: operationId,
      status: checkpoint.status,
      progress: progress,
      current_step: currentStep,
      total_steps: totalSteps,
      cards_created: state.cards_created || [],
      estimated_time_remaining: estimatedTimeRemaining,
      created_at: checkpoint.created_at,
      updated_at: checkpoint.updated_at,
      error: state.error || null
    });

  } catch (error) {
    console.error('[AI Features] Error fetching operation status:', error);
    res.status(500).json({
      error: 'Failed to fetch operation status',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});
