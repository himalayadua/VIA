/**
 * Auto-Actions Router
 * 
 * Express routes for automatic action configuration:
 * - Get enabled automatic actions for a canvas
 * - Configure automatic actions
 * - Manually trigger automatic actions
 */

import express, { Request, Response } from 'express';
import { db } from '../db.js';

const router = express.Router();

// Python AI Service URL from environment
const PYTHON_AI_SERVICE_URL = process.env.PYTHON_AI_SERVICE_URL || 'http://localhost:8000';

/**
 * GET /api/canvas/:id/auto-actions
 * 
 * Get all automatic actions configuration for a canvas.
 */
router.get('/:id/auto-actions', async (req: Request, res: Response) => {
  const { id: canvasId } = req.params;

  try {
    console.log(`[Auto-Actions] Get config for canvas: ${canvasId}`);

    // Validate canvas exists
    const canvasResult = await db.query('SELECT * FROM canvases WHERE id = $1', [canvasId]);
    if (canvasResult.rows.length === 0) {
      return res.status(404).json({ error: 'Canvas not found' });
    }

    // Get all auto-actions for this canvas
    const result = await db.query(
      `SELECT action_type, enabled, config, created_at, updated_at
       FROM canvas_auto_actions
       WHERE canvas_id = $1
       ORDER BY action_type`,
      [canvasId]
    );

    // If no actions exist, create defaults
    if (result.rows.length === 0) {
      const defaultActions = [
        'conflict_detection',
        'auto_categorize',
        'suggest_connections',
        'update_outdated',
        'find_duplicates'
      ];

      for (const actionType of defaultActions) {
        await db.query(
          `INSERT INTO canvas_auto_actions (canvas_id, action_type, enabled, config)
           VALUES ($1, $2, false, '{}')
           ON CONFLICT (canvas_id, action_type) DO NOTHING`,
          [canvasId, actionType]
        );
      }

      // Fetch again
      const newResult = await db.query(
        `SELECT action_type, enabled, config, created_at, updated_at
         FROM canvas_auto_actions
         WHERE canvas_id = $1
         ORDER BY action_type`,
        [canvasId]
      );

      return res.json({
        canvas_id: canvasId,
        auto_actions: newResult.rows
      });
    }

    res.json({
      canvas_id: canvasId,
      auto_actions: result.rows
    });

  } catch (error) {
    console.error('[Auto-Actions] Error fetching config:', error);
    res.status(500).json({
      error: 'Failed to fetch auto-actions configuration',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

/**
 * PUT /api/canvas/:id/auto-actions
 * 
 * Update automatic actions configuration for a canvas.
 */
router.put('/:id/auto-actions', async (req: Request, res: Response) => {
  const { id: canvasId } = req.params;
  const { auto_actions } = req.body;

  try {
    console.log(`[Auto-Actions] Update config for canvas: ${canvasId}`);

    // Validate canvas exists
    const canvasResult = await db.query('SELECT * FROM canvases WHERE id = $1', [canvasId]);
    if (canvasResult.rows.length === 0) {
      return res.status(404).json({ error: 'Canvas not found' });
    }

    // Validate input
    if (!auto_actions || !Array.isArray(auto_actions)) {
      return res.status(400).json({ error: 'auto_actions array is required' });
    }

    // Valid action types
    const validActionTypes = [
      'conflict_detection',
      'auto_categorize',
      'suggest_connections',
      'update_outdated',
      'find_duplicates'
    ];

    // Update each action
    const updatedActions = [];
    for (const action of auto_actions) {
      const { action_type, enabled, config = {} } = action;

      if (!action_type || !validActionTypes.includes(action_type)) {
        return res.status(400).json({ 
          error: `Invalid action_type: ${action_type}. Must be one of: ${validActionTypes.join(', ')}` 
        });
      }

      if (typeof enabled !== 'boolean') {
        return res.status(400).json({ 
          error: `enabled must be a boolean for action_type: ${action_type}` 
        });
      }

      // Upsert the action
      const result = await db.query(
        `INSERT INTO canvas_auto_actions (canvas_id, action_type, enabled, config)
         VALUES ($1, $2, $3, $4)
         ON CONFLICT (canvas_id, action_type)
         DO UPDATE SET enabled = $3, config = $4, updated_at = NOW()
         RETURNING action_type, enabled, config, updated_at`,
        [canvasId, action_type, enabled, JSON.stringify(config)]
      );

      updatedActions.push(result.rows[0]);
    }

    res.json({
      canvas_id: canvasId,
      auto_actions: updatedActions,
      message: `Updated ${updatedActions.length} auto-action(s)`
    });

  } catch (error) {
    console.error('[Auto-Actions] Error updating config:', error);
    res.status(500).json({
      error: 'Failed to update auto-actions configuration',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

/**
 * POST /api/canvas/:id/auto-actions/trigger
 * 
 * Manually trigger all enabled automatic actions for a canvas.
 */
router.post('/:id/auto-actions/trigger', async (req: Request, res: Response) => {
  const { id: canvasId } = req.params;
  const { action_types } = req.body; // Optional: specific actions to trigger
  const sessionId = req.headers['x-session-id'] as string;

  try {
    console.log(`[Auto-Actions] Manual trigger for canvas: ${canvasId}`);

    // Validate canvas exists
    const canvasResult = await db.query('SELECT * FROM canvases WHERE id = $1', [canvasId]);
    if (canvasResult.rows.length === 0) {
      return res.status(404).json({ error: 'Canvas not found' });
    }

    // Get enabled actions (or specific ones if provided)
    let query = `
      SELECT action_type, config
      FROM canvas_auto_actions
      WHERE canvas_id = $1 AND enabled = true
    `;
    const params: any[] = [canvasId];

    if (action_types && Array.isArray(action_types) && action_types.length > 0) {
      query += ` AND action_type = ANY($2)`;
      params.push(action_types);
    }

    const actionsResult = await db.query(query, params);

    if (actionsResult.rows.length === 0) {
      return res.json({
        canvas_id: canvasId,
        triggered_actions: [],
        results: {},
        message: 'No enabled auto-actions to trigger'
      });
    }

    // Get all cards for the canvas
    const cardsResult = await db.query(
      'SELECT id, title, content, card_type, tags, card_data FROM nodes WHERE canvas_id = $1',
      [canvasId]
    );

    // Forward to Python AI Service to execute actions
    const response = await fetch(`${PYTHON_AI_SERVICE_URL}/ai/auto-actions/trigger`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Session-ID': sessionId || '',
      },
      body: JSON.stringify({
        canvas_id: canvasId,
        actions: actionsResult.rows,
        cards: cardsResult.rows
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Python AI Service returned ${response.status}: ${errorText}`);
    }

    const result = await response.json() as { results?: Record<string, any> };
    
    res.json({
      canvas_id: canvasId,
      triggered_actions: actionsResult.rows.map(r => r.action_type),
      results: result.results || {},
      message: `Triggered ${actionsResult.rows.length} auto-action(s)`
    });

  } catch (error) {
    console.error('[Auto-Actions] Error triggering actions:', error);
    res.status(500).json({
      error: 'Failed to trigger automatic actions',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

export default router;
