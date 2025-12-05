/*
  # Add Source Attribution to Nodes

  ## Changes
  - Add source_url column to track where content came from
  - Add source_type column to indicate origin (url, ai_generated, manual)
  - Add extracted_at column to track when content was extracted
  - Add sources column (JSONB) to store multiple sources for merged content
  - Add has_conflict column to flag conflicting information

  ## Purpose
  Enable source attribution and multi-source content merging (Task 8)
*/

-- Add source attribution columns to nodes table
ALTER TABLE nodes ADD COLUMN IF NOT EXISTS source_url TEXT;
ALTER TABLE nodes ADD COLUMN IF NOT EXISTS source_type TEXT DEFAULT 'manual' CHECK (source_type IN ('url', 'ai_generated', 'manual'));
ALTER TABLE nodes ADD COLUMN IF NOT EXISTS extracted_at TIMESTAMPTZ;
ALTER TABLE nodes ADD COLUMN IF NOT EXISTS sources JSONB DEFAULT '[]'::jsonb;
ALTER TABLE nodes ADD COLUMN IF NOT EXISTS has_conflict BOOLEAN DEFAULT false;

-- Create index on source_url for faster lookups
CREATE INDEX IF NOT EXISTS idx_nodes_source_url ON nodes(source_url);
CREATE INDEX IF NOT EXISTS idx_nodes_source_type ON nodes(source_type);
CREATE INDEX IF NOT EXISTS idx_nodes_has_conflict ON nodes(has_conflict);

-- Add comments for documentation
COMMENT ON COLUMN nodes.source_url IS 'URL where content was extracted from (for url type)';
COMMENT ON COLUMN nodes.source_type IS 'Origin of content: url, ai_generated, or manual';
COMMENT ON COLUMN nodes.extracted_at IS 'Timestamp when content was extracted';
COMMENT ON COLUMN nodes.sources IS 'Array of source objects for merged content: [{url, type, extracted_at, contribution}]';
COMMENT ON COLUMN nodes.has_conflict IS 'Flag indicating this card has conflicting information with another card';

-- Create a function to update extracted_at automatically
CREATE OR REPLACE FUNCTION set_extracted_at()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.source_type IN ('url', 'ai_generated') AND NEW.extracted_at IS NULL THEN
    NEW.extracted_at = NOW();
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to auto-set extracted_at
CREATE TRIGGER set_extracted_at_trigger
  BEFORE INSERT ON nodes
  FOR EACH ROW
  EXECUTE FUNCTION set_extracted_at();
