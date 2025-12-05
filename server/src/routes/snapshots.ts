import express from 'express';
import { db } from '../db.js';

const router = express.Router();

// GET /api/snapshots?canvas_id=:id - Get last 5 snapshots for canvas
router.get('/', async (req, res) => {
  try {
    const { canvas_id } = req.query;
    
    if (!canvas_id) {
      return res.status(400).json({ error: 'canvas_id query parameter is required' });
    }
    
    const result = await db.query(
      `SELECT * FROM canvas_snapshots 
       WHERE canvas_id = $1 
       ORDER BY created_at DESC 
       LIMIT 5`,
      [canvas_id]
    );
    
    res.json(result.rows);
  } catch (error) {
    console.error('Error fetching snapshots:', error);
    res.status(500).json({ 
      error: 'Failed to fetch snapshots',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// POST /api/snapshots - Create new snapshot
router.post('/', async (req, res) => {
  try {
    const { canvas_id, snapshot_data } = req.body;
    
    if (!canvas_id || !snapshot_data) {
      return res.status(400).json({ 
        error: 'canvas_id and snapshot_data are required' 
      });
    }
    
    // Validate snapshot_data structure
    if (!snapshot_data.nodes || !snapshot_data.edges || !snapshot_data.viewport) {
      return res.status(400).json({ 
        error: 'snapshot_data must contain nodes, edges, and viewport' 
      });
    }
    
    const result = await db.query(
      `INSERT INTO canvas_snapshots (canvas_id, snapshot_data)
       VALUES ($1, $2)
       RETURNING *`,
      [canvas_id, JSON.stringify(snapshot_data)]
    );
    
    res.status(201).json(result.rows[0]);
  } catch (error) {
    console.error('Error creating snapshot:', error);
    res.status(500).json({ 
      error: 'Failed to create snapshot',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// DELETE /api/snapshots/:id - Delete snapshot
router.delete('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    
    const result = await db.query(
      'DELETE FROM canvas_snapshots WHERE id = $1 RETURNING *',
      [id]
    );
    
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Snapshot not found' });
    }
    
    res.json({ 
      message: 'Snapshot deleted successfully',
      snapshot: result.rows[0]
    });
  } catch (error) {
    console.error('Error deleting snapshot:', error);
    res.status(500).json({ 
      error: 'Failed to delete snapshot',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

export default router;
