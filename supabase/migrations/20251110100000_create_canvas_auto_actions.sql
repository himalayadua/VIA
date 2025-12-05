-- Create canvas_auto_actions table for automatic action configuration

CREATE TABLE IF NOT EXISTS canvas_auto_actions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  canvas_id UUID NOT NULL REFERENCES canvases(id) ON DELETE CASCADE,
  action_type VARCHAR(50) NOT NULL,
  enabled BOOLEAN DEFAULT false,
  config JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(canvas_id, action_type)
);

-- Create index for faster lookups
CREATE INDEX idx_canvas_auto_actions_canvas_id ON canvas_auto_actions(canvas_id);
CREATE INDEX idx_canvas_auto_actions_enabled ON canvas_auto_actions(canvas_id, enabled) WHERE enabled = true;

-- Add trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_canvas_auto_actions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_canvas_auto_actions_updated_at
  BEFORE UPDATE ON canvas_auto_actions
  FOR EACH ROW
  EXECUTE FUNCTION update_canvas_auto_actions_updated_at();

-- Insert default auto-actions for existing canvases
INSERT INTO canvas_auto_actions (canvas_id, action_type, enabled, config)
SELECT 
  id as canvas_id,
  action_type,
  false as enabled,
  '{}'::jsonb as config
FROM canvases
CROSS JOIN (
  VALUES 
    ('conflict_detection'),
    ('auto_categorize'),
    ('suggest_connections'),
    ('update_outdated'),
    ('find_duplicates')
) AS actions(action_type)
ON CONFLICT (canvas_id, action_type) DO NOTHING;
