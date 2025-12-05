import express from 'express';
import { db } from '../db.js';

const router = express.Router();

// GET /api/connections?canvas_id=:id - List connections by canvas
router.get('/', async (req, res) => {
  try {
    const { canvas_id } = req.query;
    
    if (!canvas_id) {
      return res.status(400).json({ error: 'canvas_id query parameter is required' });
    }
    
    const result = await db.query(
      'SELECT * FROM connections WHERE canvas_id = $1 ORDER BY created_at ASC',
      [canvas_id]
    );
    
    res.json(result.rows);
  } catch (error) {
    console.error('Error fetching connections:', error);
    res.status(500).json({ 
      error: 'Failed to fetch connections',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// POST /api/connections - Create new connection
router.post('/', async (req, res) => {
  try {
    const {
      canvas_id,
      source_id,
      target_id,
      type = 'default',
      animated = false, // Default to false for solid lines (not dotted)
      style = {}
    } = req.body;
    
    if (!canvas_id || !source_id || !target_id) {
      return res.status(400).json({ 
        error: 'canvas_id, source_id, and target_id are required' 
      });
    }
    
    const result = await db.query(
      `INSERT INTO connections (canvas_id, source_id, target_id, type, animated, style)
       VALUES ($1, $2, $3, $4, $5, $6)
       RETURNING *`,
      [canvas_id, source_id, target_id, type, animated, JSON.stringify(style)]
    );
    
    res.status(201).json(result.rows[0]);
  } catch (error) {
    console.error('Error creating connection:', error);
    res.status(500).json({ 
      error: 'Failed to create connection',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// DELETE /api/connections/:id - Delete connection
router.delete('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    
    const result = await db.query(
      'DELETE FROM connections WHERE id = $1 RETURNING *',
      [id]
    );
    
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Connection not found' });
    }
    
    res.json({ 
      message: 'Connection deleted successfully',
      connection: result.rows[0]
    });
  } catch (error) {
    console.error('Error deleting connection:', error);
    res.status(500).json({ 
      error: 'Failed to delete connection',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

export default router;
