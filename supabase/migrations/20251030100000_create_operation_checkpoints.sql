-- Create operation_checkpoints table for progress tracking and recovery
-- Migration: 20251030100000_create_operation_checkpoints

-- Create operation_checkpoints table
CREATE TABLE IF NOT EXISTS operation_checkpoints (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  operation_id UUID UNIQUE NOT NULL,
  operation_type TEXT NOT NULL,
  canvas_id UUID REFERENCES canvases(id) ON DELETE CASCADE,
  session_id TEXT,
  current_step INTEGER NOT NULL DEFAULT 0,
  total_steps INTEGER NOT NULL DEFAULT 1,
  progress FLOAT NOT NULL DEFAULT 0.0 CHECK (progress >= 0.0 AND progress <= 1.0),
  state JSONB NOT NULL DEFAULT '{}',
  cards_created TEXT[] DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for efficient queries
CREATE INDEX idx_checkpoints_operation_id ON operation_checkpoints(operation_id);
CREATE INDEX idx_checkpoints_canvas_id ON operation_checkpoints(canvas_id);
CREATE INDEX idx_checkpoints_session_id ON operation_checkpoints(session_id);
CREATE INDEX idx_checkpoints_progress ON operation_checkpoints(progress) WHERE progress < 1.0;
CREATE INDEX idx_checkpoints_updated_at ON operation_checkpoints(updated_at);

-- Create trigger to auto-update updated_at
CREATE OR REPLACE FUNCTION update_checkpoint_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_checkpoint_timestamp
  BEFORE UPDATE ON operation_checkpoints
  FOR EACH ROW
  EXECUTE FUNCTION update_checkpoint_updated_at();

-- Add comments for documentation
COMMENT ON TABLE operation_checkpoints IS 'Stores checkpoints for long-running operations to enable recovery';
COMMENT ON COLUMN operation_checkpoints.operation_id IS 'Unique identifier for the operation';
COMMENT ON COLUMN operation_checkpoints.operation_type IS 'Type of operation (e.g., url_extraction, grow_card)';
COMMENT ON COLUMN operation_checkpoints.canvas_id IS 'Canvas where operation is running';
COMMENT ON COLUMN operation_checkpoints.session_id IS 'Session ID for SSE routing';
COMMENT ON COLUMN operation_checkpoints.progress IS 'Progress value from 0.0 to 1.0';
COMMENT ON COLUMN operation_checkpoints.state IS 'JSON state data for recovery';
COMMENT ON COLUMN operation_checkpoints.cards_created IS 'Array of card IDs created so far';
