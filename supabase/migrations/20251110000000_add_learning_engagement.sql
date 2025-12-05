-- Migration: Add learning engagement tracking
-- Adds read_count, importance, and card_type_icon fields to nodes table

-- Add read_count field to track engagement
ALTER TABLE nodes ADD COLUMN IF NOT EXISTS read_count INTEGER DEFAULT 0;

-- Add importance field for marking important cards
ALTER TABLE nodes ADD COLUMN IF NOT EXISTS importance VARCHAR(10) DEFAULT 'normal';

-- Add card_type_icon field for visual indicators
ALTER TABLE nodes ADD COLUMN IF NOT EXISTS card_type_icon VARCHAR(10);

-- Create index on read_count for performance
CREATE INDEX IF NOT EXISTS idx_nodes_read_count ON nodes(read_count);

-- Create index on importance for filtering
CREATE INDEX IF NOT EXISTS idx_nodes_importance ON nodes(importance);

-- Add comment
COMMENT ON COLUMN nodes.read_count IS 'Number of times user has engaged with this card (clicks, checks, chat references)';
COMMENT ON COLUMN nodes.importance IS 'Importance level: normal, high';
COMMENT ON COLUMN nodes.card_type_icon IS 'Icon type: question, todo, reminder, person, concept, technique, contradiction, example, challenge';
