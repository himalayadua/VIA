-- Via Canvas Database Initialization Script
-- PostgreSQL 15+

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create canvases table
CREATE TABLE IF NOT EXISTS canvases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    user_id UUID DEFAULT NULL
);

-- Create nodes table with new card type fields
CREATE TABLE IF NOT EXISTS nodes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    canvas_id UUID NOT NULL REFERENCES canvases(id) ON DELETE CASCADE,
    parent_id UUID DEFAULT NULL REFERENCES nodes(id) ON DELETE SET NULL,
    
    -- Legacy field (kept for backward compatibility)
    content TEXT DEFAULT '',
    
    -- New card type fields
    title TEXT DEFAULT '',
    card_type TEXT DEFAULT 'rich_text',
    card_data JSONB DEFAULT '{}',
    tags TEXT[] DEFAULT '{}',
    
    -- Position and styling
    position_x NUMERIC DEFAULT 0,
    position_y NUMERIC DEFAULT 0,
    width NUMERIC DEFAULT 300,
    height NUMERIC DEFAULT 150,
    type TEXT DEFAULT 'custom',
    style JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create connections table
CREATE TABLE IF NOT EXISTS connections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    canvas_id UUID NOT NULL REFERENCES canvases(id) ON DELETE CASCADE,
    source_id UUID NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    target_id UUID NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    type TEXT DEFAULT 'default',
    animated BOOLEAN DEFAULT true,
    style JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create node_history table for tracking changes
CREATE TABLE IF NOT EXISTS node_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    node_id UUID NOT NULL,
    canvas_id UUID NOT NULL REFERENCES canvases(id) ON DELETE CASCADE,
    content TEXT DEFAULT NULL,
    position_x NUMERIC DEFAULT NULL,
    position_y NUMERIC DEFAULT NULL,
    action_type TEXT NOT NULL,
    snapshot JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create canvas_snapshots table for storing canvas state history
CREATE TABLE IF NOT EXISTS canvas_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    canvas_id UUID NOT NULL REFERENCES canvases(id) ON DELETE CASCADE,
    snapshot_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance

-- Canvases indexes
CREATE INDEX IF NOT EXISTS idx_canvases_updated_at ON canvases(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_canvases_user_id ON canvases(user_id);

-- Nodes indexes
CREATE INDEX IF NOT EXISTS idx_nodes_canvas_id ON nodes(canvas_id);
CREATE INDEX IF NOT EXISTS idx_nodes_parent_id ON nodes(parent_id);
CREATE INDEX IF NOT EXISTS idx_nodes_card_type ON nodes(card_type);
CREATE INDEX IF NOT EXISTS idx_nodes_title ON nodes(title);
CREATE INDEX IF NOT EXISTS idx_nodes_created_at ON nodes(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_nodes_tags ON nodes USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_nodes_card_data ON nodes USING GIN(card_data);

-- Connections indexes
CREATE INDEX IF NOT EXISTS idx_connections_canvas_id ON connections(canvas_id);
CREATE INDEX IF NOT EXISTS idx_connections_source_id ON connections(source_id);
CREATE INDEX IF NOT EXISTS idx_connections_target_id ON connections(target_id);

-- Node history indexes
CREATE INDEX IF NOT EXISTS idx_node_history_node_id ON node_history(node_id);
CREATE INDEX IF NOT EXISTS idx_node_history_canvas_id ON node_history(canvas_id);
CREATE INDEX IF NOT EXISTS idx_node_history_created_at ON node_history(created_at DESC);

-- Canvas snapshots indexes
CREATE INDEX IF NOT EXISTS idx_snapshots_canvas_id ON canvas_snapshots(canvas_id);
CREATE INDEX IF NOT EXISTS idx_snapshots_created_at ON canvas_snapshots(created_at DESC);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at
CREATE TRIGGER update_canvases_updated_at
    BEFORE UPDATE ON canvases
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_nodes_updated_at
    BEFORE UPDATE ON nodes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create function to auto-cleanup old snapshots (keep only last 5 per canvas)
CREATE OR REPLACE FUNCTION cleanup_old_snapshots()
RETURNS TRIGGER AS $$
BEGIN
    DELETE FROM canvas_snapshots
    WHERE canvas_id = NEW.canvas_id
    AND id NOT IN (
        SELECT id FROM canvas_snapshots
        WHERE canvas_id = NEW.canvas_id
        ORDER BY created_at DESC
        LIMIT 5
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for snapshot cleanup
CREATE TRIGGER trigger_cleanup_snapshots
    AFTER INSERT ON canvas_snapshots
    FOR EACH ROW
    EXECUTE FUNCTION cleanup_old_snapshots();

-- Create constraint to ensure valid card types
ALTER TABLE nodes
ADD CONSTRAINT check_card_type
CHECK (card_type IN ('rich_text', 'todo', 'video', 'link', 'reminder'));

-- Create constraint to ensure valid connection types
ALTER TABLE connections
ADD CONSTRAINT check_connection_type
CHECK (type IN ('default', 'straight', 'step', 'smoothstep', 'simplebezier'));

-- Insert sample canvas for testing (optional, can be removed in production)
INSERT INTO canvases (name, description) VALUES
    ('Welcome Canvas', 'Your first canvas to get started with Via Canvas')
ON CONFLICT DO NOTHING;

-- Grant permissions (adjust as needed for production)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO viacanvas;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO viacanvas;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Via Canvas database initialized successfully!';
    RAISE NOTICE 'Tables created: canvases, nodes, connections, node_history, canvas_snapshots';
    RAISE NOTICE 'Indexes and triggers configured';
END $$;
