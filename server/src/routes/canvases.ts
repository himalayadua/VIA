import express from 'express';
import { db } from '../db.js';

const router = express.Router();

// GET /api/canvases - List all canvases
router.get('/', async (req, res) => {
  try {
    const result = await db.query(
      'SELECT * FROM canvases ORDER BY updated_at DESC'
    );
    res.json(result.rows);
  } catch (error) {
    console.error('Error fetching canvases:', error);
    res.status(500).json({ 
      error: 'Failed to fetch canvases',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// GET /api/canvases/:id - Get single canvas
router.get('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const result = await db.query(
      'SELECT * FROM canvases WHERE id = $1',
      [id]
    );
    
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Canvas not found' });
    }
    
    res.json(result.rows[0]);
  } catch (error) {
    console.error('Error fetching canvas:', error);
    res.status(500).json({ 
      error: 'Failed to fetch canvas',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// POST /api/canvases - Create new canvas
router.post('/', async (req, res) => {
  try {
    const { name, description = '' } = req.body;
    
    if (!name || typeof name !== 'string') {
      return res.status(400).json({ error: 'Canvas name is required' });
    }
    
    const result = await db.query(
      `INSERT INTO canvases (name, description) 
       VALUES ($1, $2) 
       RETURNING *`,
      [name, description]
    );
    
    res.status(201).json(result.rows[0]);
  } catch (error) {
    console.error('Error creating canvas:', error);
    res.status(500).json({ 
      error: 'Failed to create canvas',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// PUT /api/canvases/:id - Update canvas
router.put('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const { name, description } = req.body;
    
    // Build dynamic update query
    const updates: string[] = [];
    const values: any[] = [];
    let paramCount = 1;
    
    if (name !== undefined) {
      updates.push(`name = $${paramCount++}`);
      values.push(name);
    }
    
    if (description !== undefined) {
      updates.push(`description = $${paramCount++}`);
      values.push(description);
    }
    
    if (updates.length === 0) {
      return res.status(400).json({ error: 'No fields to update' });
    }
    
    values.push(id);
    
    const result = await db.query(
      `UPDATE canvases 
       SET ${updates.join(', ')}, updated_at = NOW()
       WHERE id = $${paramCount}
       RETURNING *`,
      values
    );
    
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Canvas not found' });
    }
    
    res.json(result.rows[0]);
  } catch (error) {
    console.error('Error updating canvas:', error);
    res.status(500).json({ 
      error: 'Failed to update canvas',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// DELETE /api/canvases/:id - Delete canvas (cascades to nodes and connections)
router.delete('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    
    const result = await db.query(
      'DELETE FROM canvases WHERE id = $1 RETURNING *',
      [id]
    );
    
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Canvas not found' });
    }
    
    res.json({ 
      message: 'Canvas deleted successfully',
      canvas: result.rows[0]
    });
  } catch (error) {
    console.error('Error deleting canvas:', error);
    res.status(500).json({ 
      error: 'Failed to delete canvas',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

export default router;
