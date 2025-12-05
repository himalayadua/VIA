-- Create automatic_actions_history table
-- Tracks execution history of automatic actions

CREATE TABLE IF NOT EXISTS automatic_actions_history (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  canvas_id UUID NOT NULL REFERENCES canvases(id) ON DELETE CASCADE,
  card_id UUID REFERENCES nodes(id) ON DELETE SET NULL,
  action_type VARCHAR(50) NOT NULL,
  triggered_at TIMESTAMP DEFAULT NOW(),
  completed_at TIMESTAMP,
  status VARCHAR(20) DEFAULT 'pending', -- pending, running, completed, failed
  result JSONB DEFAULT '{}',
  error_message TEXT,
  execution_time_ms INTEGER,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_automatic_actions_history_canvas ON automatic_actions_history(canvas_id);
CREATE INDEX idx_automatic_actions_history_card ON automatic_actions_history(card_id) WHERE card_id IS NOT NULL;
CREATE INDEX idx_automatic_actions_history_status ON automatic_actions_history(status);
CREATE INDEX idx_automatic_actions_history_triggered ON automatic_actions_history(triggered_at DESC);
CREATE INDEX idx_automatic_actions_history_action_type ON automatic_actions_history(action_type);

-- Add comment
COMMENT ON TABLE automatic_actions_history IS 'Tracks execution history of automatic actions for monitoring and analytics';
COMMENT ON COLUMN automatic_actions_history.result IS 'JSONB containing action-specific results (e.g., conflicts found, cards categorized)';
COMMENT ON COLUMN automatic_actions_history.execution_time_ms IS 'Time taken to execute the action in milliseconds';
