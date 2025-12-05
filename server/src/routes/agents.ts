/**
 * Agent Management Router
 * 
 * Express routes for managing AI agents:
 * - Get agent statuses
 * - Restart agents
 * - Get agent metrics
 * - Get agent logs
 */

import express, { Request, Response } from 'express';

const router = express.Router();

// Python AI Service URL from environment
const PYTHON_AI_SERVICE_URL = process.env.PYTHON_AI_SERVICE_URL || 'http://localhost:8000';

/**
 * GET /api/agents/status
 * 
 * Get health status of all agents.
 */
router.get('/status', async (req: Request, res: Response) => {
  try {
    console.log('[Agents] Fetching all agent statuses');

    // Forward to Python AI Service
    const response = await fetch(`${PYTHON_AI_SERVICE_URL}/api/agents/status`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Python AI Service returned ${response.status}`);
    }

    const result = await response.json();
    res.json(result);

  } catch (error) {
    console.error('[Agents] Error fetching agent statuses:', error);
    res.status(500).json({
      error: 'Failed to fetch agent statuses',
      message: error instanceof Error ? error.message : 'Unknown error',
      agents: [] // Return empty array on error
    });
  }
});

/**
 * POST /api/agents/:agentId/restart
 * 
 * Restart a specific agent.
 */
router.post('/:agentId/restart', async (req: Request, res: Response) => {
  const { agentId } = req.params;

  try {
    console.log(`[Agents] Restart request for agent: ${agentId}`);

    // Validate agent ID format
    const validAgentIds = [
      'chat_agent',
      'content_extraction_agent',
      'knowledge_graph_agent',
      'background_intelligence_agent',
      'learning_assistant_agent'
    ];

    if (!validAgentIds.includes(agentId)) {
      return res.status(400).json({ 
        error: `Invalid agent ID: ${agentId}. Must be one of: ${validAgentIds.join(', ')}` 
      });
    }

    // Forward to Python AI Service
    const response = await fetch(`${PYTHON_AI_SERVICE_URL}/api/agents/${agentId}/restart`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Python AI Service returned ${response.status}: ${errorText}`);
    }

    const result = await response.json();
    res.json(result);

  } catch (error) {
    console.error(`[Agents] Error restarting agent ${agentId}:`, error);
    res.status(500).json({
      error: 'Failed to restart agent',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

/**
 * GET /api/agents/:agentId/metrics
 * 
 * Get performance metrics for a specific agent.
 */
router.get('/:agentId/metrics', async (req: Request, res: Response) => {
  const { agentId } = req.params;
  const { period = 'last_hour' } = req.query;

  try {
    console.log(`[Agents] Fetching metrics for agent: ${agentId}`);

    // Validate period
    const validPeriods = ['last_hour', 'last_day', 'last_week', 'last_month'];
    if (!validPeriods.includes(period as string)) {
      return res.status(400).json({ 
        error: `Invalid period: ${period}. Must be one of: ${validPeriods.join(', ')}` 
      });
    }

    // Forward to Python AI Service
    const response = await fetch(
      `${PYTHON_AI_SERVICE_URL}/api/agents/${agentId}/metrics?period=${period}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      if (response.status === 404) {
        return res.status(404).json({ error: 'Agent not found' });
      }
      throw new Error(`Python AI Service returned ${response.status}`);
    }

    const result = await response.json();
    res.json(result);

  } catch (error) {
    console.error(`[Agents] Error fetching metrics for agent ${agentId}:`, error);
    res.status(500).json({
      error: 'Failed to fetch agent metrics',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

/**
 * GET /api/agents/:agentId/logs
 * 
 * Get recent log entries for a specific agent.
 */
router.get('/:agentId/logs', async (req: Request, res: Response) => {
  const { agentId } = req.params;
  const { 
    level = 'all', 
    limit = '100', 
    page = '1' 
  } = req.query;

  try {
    console.log(`[Agents] Fetching logs for agent: ${agentId}`);

    // Validate level
    const validLevels = ['all', 'debug', 'info', 'warning', 'error'];
    if (!validLevels.includes(level as string)) {
      return res.status(400).json({ 
        error: `Invalid level: ${level}. Must be one of: ${validLevels.join(', ')}` 
      });
    }

    // Validate limit and page
    const limitNum = parseInt(limit as string);
    const pageNum = parseInt(page as string);
    
    if (isNaN(limitNum) || limitNum < 1 || limitNum > 1000) {
      return res.status(400).json({ error: 'limit must be between 1 and 1000' });
    }
    
    if (isNaN(pageNum) || pageNum < 1) {
      return res.status(400).json({ error: 'page must be >= 1' });
    }

    // Forward to Python AI Service
    const response = await fetch(
      `${PYTHON_AI_SERVICE_URL}/api/agents/${agentId}/logs?level=${level}&limit=${limit}&page=${page}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      if (response.status === 404) {
        return res.status(404).json({ error: 'Agent not found' });
      }
      throw new Error(`Python AI Service returned ${response.status}`);
    }

    const result = await response.json();
    res.json(result);

  } catch (error) {
    console.error(`[Agents] Error fetching logs for agent ${agentId}:`, error);
    res.status(500).json({
      error: 'Failed to fetch agent logs',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

export default router;
