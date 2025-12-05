-- Create learning_paths table
-- Tracks learning paths and progress for users

CREATE TABLE IF NOT EXISTS learning_paths (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  canvas_id UUID NOT NULL REFERENCES canvases(id) ON DELETE CASCADE,
  user_id UUID, -- Optional: for multi-user support in future
  topic TEXT NOT NULL,
  path_data JSONB DEFAULT '{}', -- Structured learning path with steps
  progress JSONB DEFAULT '{}', -- Progress tracking data
  status VARCHAR(20) DEFAULT 'active', -- active, completed, abandoned
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  completed_at TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_learning_paths_canvas ON learning_paths(canvas_id);
CREATE INDEX idx_learning_paths_status ON learning_paths(status);
CREATE INDEX idx_learning_paths_user ON learning_paths(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX idx_learning_paths_topic ON learning_paths(topic);
CREATE INDEX idx_learning_paths_created ON learning_paths(created_at DESC);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_learning_paths_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_learning_paths_updated_at
  BEFORE UPDATE ON learning_paths
  FOR EACH ROW
  EXECUTE FUNCTION update_learning_paths_updated_at();

-- Add comments
COMMENT ON TABLE learning_paths IS 'Tracks learning paths and user progress through structured learning content';
COMMENT ON COLUMN learning_paths.path_data IS 'JSONB containing learning path structure: steps, prerequisites, difficulty, estimated time';
COMMENT ON COLUMN learning_paths.progress IS 'JSONB containing progress data: completed steps, current step, cards read, time spent';
COMMENT ON COLUMN learning_paths.user_id IS 'Optional user ID for multi-user support (future feature)';
