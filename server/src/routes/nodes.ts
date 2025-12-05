import express from 'express';
import { db } from '../db.js';

const router = express.Router();

const VALID_CARD_TYPES = ['rich_text', 'todo', 'video', 'link', 'reminder'];

// GET /api/nodes?canvas_id=:id - List nodes by canvas
router.get('/', async (req, res) => {
  try {
    const { canvas_id } = req.query;
    
    if (!canvas_id) {
      return res.status(400).json({ error: 'canvas_id query parameter is required' });
    }
    
    const result = await db.query(
      'SELECT * FROM nodes WHERE canvas_id = $1 ORDER BY created_at ASC',
      [canvas_id]
    );
    
    res.json(result.rows);
  } catch (error) {
    console.error('Error fetching nodes:', error);
    res.status(500).json({ 
      error: 'Failed to fetch nodes',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// GET /api/nodes/:id - Get single node
router.get('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const result = await db.query(
      'SELECT * FROM nodes WHERE id = $1',
      [id]
    );
    
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Node not found' });
    }
    
    res.json(result.rows[0]);
  } catch (error) {
    console.error('Error fetching node:', error);
    res.status(500).json({ 
      error: 'Failed to fetch node',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// POST /api/nodes - Create new node
router.post('/', async (req, res) => {
  try {
    const {
      canvas_id,
      parent_id = null,
      title = '',
      content = '',
      card_type = 'rich_text',
      card_data = {},
      tags = [],
      position_x = 0,
      position_y = 0,
      width = 300,
      height = 150,
      type = 'custom',
      style = {},
      source_url = null,
      source_type = 'manual',
      sources = [],
      has_conflict = false
    } = req.body;
    
    if (!canvas_id) {
      return res.status(400).json({ error: 'canvas_id is required' });
    }
    
    if (!VALID_CARD_TYPES.includes(card_type)) {
      return res.status(400).json({ 
        error: 'Invalid card_type',
        valid_types: VALID_CARD_TYPES
      });
    }
    
    const result = await db.query(
      `INSERT INTO nodes (
        canvas_id, parent_id, title, content, card_type, card_data, tags,
        position_x, position_y, width, height, type, style,
        source_url, source_type, sources, has_conflict
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
      RETURNING *`,
      [
        canvas_id, parent_id, title, content, card_type, 
        JSON.stringify(card_data), tags, position_x, position_y, 
        width, height, type, JSON.stringify(style),
        source_url, source_type, JSON.stringify(sources), has_conflict
      ]
    );
    
    res.status(201).json(result.rows[0]);
  } catch (error) {
    console.error('Error creating node:', error);
    res.status(500).json({ 
      error: 'Failed to create node',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// PUT /api/nodes/:id - Update node
router.put('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const {
      title,
      content,
      card_type,
      card_data,
      tags,
      position_x,
      position_y,
      width,
      height,
      parent_id,
      style
    } = req.body;
    
    // Build dynamic update query
    const updates: string[] = [];
    const values: any[] = [];
    let paramCount = 1;
    
    if (title !== undefined) {
      updates.push(`title = $${paramCount++}`);
      values.push(title);
    }
    
    if (content !== undefined) {
      updates.push(`content = $${paramCount++}`);
      values.push(content);
    }
    
    if (card_type !== undefined) {
      if (!VALID_CARD_TYPES.includes(card_type)) {
        return res.status(400).json({ 
          error: 'Invalid card_type',
          valid_types: VALID_CARD_TYPES
        });
      }
      updates.push(`card_type = $${paramCount++}`);
      values.push(card_type);
    }
    
    if (card_data !== undefined) {
      updates.push(`card_data = $${paramCount++}`);
      values.push(JSON.stringify(card_data));
    }
    
    if (tags !== undefined) {
      updates.push(`tags = $${paramCount++}`);
      values.push(tags);
    }
    
    if (position_x !== undefined) {
      updates.push(`position_x = $${paramCount++}`);
      values.push(position_x);
    }
    
    if (position_y !== undefined) {
      updates.push(`position_y = $${paramCount++}`);
      values.push(position_y);
    }
    
    if (width !== undefined) {
      updates.push(`width = $${paramCount++}`);
      values.push(width);
    }
    
    if (height !== undefined) {
      updates.push(`height = $${paramCount++}`);
      values.push(height);
    }
    
    if (parent_id !== undefined) {
      updates.push(`parent_id = $${paramCount++}`);
      values.push(parent_id);
    }
    
    if (style !== undefined) {
      updates.push(`style = $${paramCount++}`);
      values.push(JSON.stringify(style));
    }
    
    if (updates.length === 0) {
      return res.status(400).json({ error: 'No fields to update' });
    }
    
    values.push(id);
    
    const result = await db.query(
      `UPDATE nodes 
       SET ${updates.join(', ')}, updated_at = NOW()
       WHERE id = $${paramCount}
       RETURNING *`,
      values
    );
    
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Node not found' });
    }
    
    res.json(result.rows[0]);
  } catch (error) {
    console.error('Error updating node:', error);
    res.status(500).json({ 
      error: 'Failed to update node',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// DELETE /api/nodes/:id - Delete node
router.delete('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    
    const result = await db.query(
      'DELETE FROM nodes WHERE id = $1 RETURNING *',
      [id]
    );
    
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Node not found' });
    }
    
    res.json({ 
      message: 'Node deleted successfully',
      node: result.rows[0]
    });
  } catch (error) {
    console.error('Error deleting node:', error);
    res.status(500).json({ 
      error: 'Failed to delete node',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// POST /api/nodes/batch - Batch update node positions
router.post('/batch', async (req, res) => {
  try {
    const { updates } = req.body;
    
    if (!Array.isArray(updates) || updates.length === 0) {
      return res.status(400).json({ error: 'updates array is required' });
    }
    
    const client = await db.getClient();
    
    try {
      await client.query('BEGIN');
      
      const results = [];
      for (const update of updates) {
        const { id, position_x, position_y } = update;
        
        if (!id || position_x === undefined || position_y === undefined) {
          throw new Error('Each update must have id, position_x, and position_y');
        }
        
        const result = await client.query(
          `UPDATE nodes 
           SET position_x = $1, position_y = $2, updated_at = NOW()
           WHERE id = $3
           RETURNING *`,
          [position_x, position_y, id]
        );
        
        results.push(result.rows[0]);
      }
      
      await client.query('COMMIT');
      res.json(results);
    } catch (error) {
      await client.query('ROLLBACK');
      throw error;
    } finally {
      client.release();
    }
  } catch (error) {
    console.error('Error batch updating nodes:', error);
    res.status(500).json({ 
      error: 'Failed to batch update nodes',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

export default router;
