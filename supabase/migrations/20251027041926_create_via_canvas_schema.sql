/*
  # Via Canvas - Mind Mapping & Temporal Visualization Schema

  ## Overview
  This migration creates the database schema for Via Canvas, an infinite canvas mind-mapping
  application with temporal visualization capabilities.

  ## Tables Created

  ### 1. `canvases`
  Stores individual canvas workspaces
  - `id` (uuid, primary key) - Unique canvas identifier
  - `name` (text) - Canvas name/title
  - `description` (text, optional) - Canvas description
  - `created_at` (timestamptz) - Creation timestamp
  - `updated_at` (timestamptz) - Last update timestamp
  - `user_id` (uuid, optional) - Owner user ID (for future auth integration)

  ### 2. `nodes`
  Stores individual nodes/cards on canvases
  - `id` (uuid, primary key) - Unique node identifier
  - `canvas_id` (uuid, foreign key) - Parent canvas
  - `parent_id` (uuid, foreign key, optional) - Parent node for hierarchical relationships
  - `content` (text) - Node content (supports markdown)
  - `position_x` (float) - X coordinate on canvas
  - `position_y` (float) - Y coordinate on canvas
  - `width` (float) - Node width
  - `height` (float) - Node height
  - `type` (text) - Node type (default, root, etc.)
  - `style` (jsonb) - Custom styling properties
  - `created_at` (timestamptz) - Creation timestamp
  - `updated_at` (timestamptz) - Last update timestamp

  ### 3. `connections`
  Stores edges/connections between nodes
  - `id` (uuid, primary key) - Unique connection identifier
  - `canvas_id` (uuid, foreign key) - Parent canvas
  - `source_id` (uuid, foreign key) - Source node
  - `target_id` (uuid, foreign key) - Target node
  - `type` (text) - Connection type (default, bezier, step)
  - `animated` (boolean) - Whether the edge is animated
  - `style` (jsonb) - Custom styling properties
  - `created_at` (timestamptz) - Creation timestamp

  ### 4. `node_history`
  Stores historical snapshots of nodes for temporal visualization
  - `id` (uuid, primary key) - Unique history entry identifier
  - `node_id` (uuid, foreign key) - Related node
  - `canvas_id` (uuid, foreign key) - Parent canvas
  - `content` (text) - Node content at this point in time
  - `position_x` (float) - X coordinate at this point
  - `position_y` (float) - Y coordinate at this point
  - `action_type` (text) - Type of action (created, updated, moved, deleted)
  - `snapshot` (jsonb) - Full node state snapshot
  - `created_at` (timestamptz) - When this history entry was created

  ## Security
  - Row Level Security (RLS) enabled on all tables
  - Public access policies for demo purposes (can be restricted later with auth)

  ## Indexes
  - Indexes on foreign keys for optimal query performance
  - Index on canvas_id for quick canvas data retrieval
  - Index on created_at for temporal queries
*/

-- Create canvases table
CREATE TABLE IF NOT EXISTS canvases (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  description text DEFAULT '',
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),
  user_id uuid
);

-- Create nodes table
CREATE TABLE IF NOT EXISTS nodes (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  canvas_id uuid NOT NULL REFERENCES canvases(id) ON DELETE CASCADE,
  parent_id uuid REFERENCES nodes(id) ON DELETE SET NULL,
  content text DEFAULT '',
  position_x float DEFAULT 0,
  position_y float DEFAULT 0,
  width float DEFAULT 300,
  height float DEFAULT 150,
  type text DEFAULT 'default',
  style jsonb DEFAULT '{}',
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Create connections table
CREATE TABLE IF NOT EXISTS connections (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  canvas_id uuid NOT NULL REFERENCES canvases(id) ON DELETE CASCADE,
  source_id uuid NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
  target_id uuid NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
  type text DEFAULT 'default',
  animated boolean DEFAULT false,
  style jsonb DEFAULT '{}',
  created_at timestamptz DEFAULT now()
);

-- Create node_history table for temporal visualization
CREATE TABLE IF NOT EXISTS node_history (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  node_id uuid NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
  canvas_id uuid NOT NULL REFERENCES canvases(id) ON DELETE CASCADE,
  content text,
  position_x float,
  position_y float,
  action_type text NOT NULL,
  snapshot jsonb DEFAULT '{}',
  created_at timestamptz DEFAULT now()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_nodes_canvas_id ON nodes(canvas_id);
CREATE INDEX IF NOT EXISTS idx_nodes_parent_id ON nodes(parent_id);
CREATE INDEX IF NOT EXISTS idx_connections_canvas_id ON connections(canvas_id);
CREATE INDEX IF NOT EXISTS idx_connections_source_id ON connections(source_id);
CREATE INDEX IF NOT EXISTS idx_connections_target_id ON connections(target_id);
CREATE INDEX IF NOT EXISTS idx_node_history_canvas_id ON node_history(canvas_id);
CREATE INDEX IF NOT EXISTS idx_node_history_node_id ON node_history(node_id);
CREATE INDEX IF NOT EXISTS idx_node_history_created_at ON node_history(created_at);

-- Enable Row Level Security
ALTER TABLE canvases ENABLE ROW LEVEL SECURITY;
ALTER TABLE nodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE connections ENABLE ROW LEVEL SECURITY;
ALTER TABLE node_history ENABLE ROW LEVEL SECURITY;

-- Create RLS Policies (permissive for demo, can be restricted with auth later)
CREATE POLICY "Allow public read access to canvases"
  ON canvases FOR SELECT
  USING (true);

CREATE POLICY "Allow public insert to canvases"
  ON canvases FOR INSERT
  WITH CHECK (true);

CREATE POLICY "Allow public update to canvases"
  ON canvases FOR UPDATE
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Allow public delete from canvases"
  ON canvases FOR DELETE
  USING (true);

CREATE POLICY "Allow public read access to nodes"
  ON nodes FOR SELECT
  USING (true);

CREATE POLICY "Allow public insert to nodes"
  ON nodes FOR INSERT
  WITH CHECK (true);

CREATE POLICY "Allow public update to nodes"
  ON nodes FOR UPDATE
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Allow public delete from nodes"
  ON nodes FOR DELETE
  USING (true);

CREATE POLICY "Allow public read access to connections"
  ON connections FOR SELECT
  USING (true);

CREATE POLICY "Allow public insert to connections"
  ON connections FOR INSERT
  WITH CHECK (true);

CREATE POLICY "Allow public update to connections"
  ON connections FOR UPDATE
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Allow public delete from connections"
  ON connections FOR DELETE
  USING (true);

CREATE POLICY "Allow public read access to node_history"
  ON node_history FOR SELECT
  USING (true);

CREATE POLICY "Allow public insert to node_history"
  ON node_history FOR INSERT
  WITH CHECK (true);

-- Create function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
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

-- Create function to automatically log node changes to history
CREATE OR REPLACE FUNCTION log_node_history()
RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    INSERT INTO node_history (node_id, canvas_id, content, position_x, position_y, action_type, snapshot)
    VALUES (NEW.id, NEW.canvas_id, NEW.content, NEW.position_x, NEW.position_y, 'created', 
            jsonb_build_object('width', NEW.width, 'height', NEW.height, 'type', NEW.type, 'style', NEW.style));
  ELSIF TG_OP = 'UPDATE' THEN
    INSERT INTO node_history (node_id, canvas_id, content, position_x, position_y, action_type, snapshot)
    VALUES (NEW.id, NEW.canvas_id, NEW.content, NEW.position_x, NEW.position_y, 'updated',
            jsonb_build_object('width', NEW.width, 'height', NEW.height, 'type', NEW.type, 'style', NEW.style));
  ELSIF TG_OP = 'DELETE' THEN
    INSERT INTO node_history (node_id, canvas_id, content, position_x, position_y, action_type, snapshot)
    VALUES (OLD.id, OLD.canvas_id, OLD.content, OLD.position_x, OLD.position_y, 'deleted',
            jsonb_build_object('width', OLD.width, 'height', OLD.height, 'type', OLD.type, 'style', OLD.style));
  END IF;
  
  IF TG_OP = 'DELETE' THEN
    RETURN OLD;
  ELSE
    RETURN NEW;
  END IF;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to log node history
CREATE TRIGGER log_node_changes
  AFTER INSERT OR UPDATE OR DELETE ON nodes
  FOR EACH ROW
  EXECUTE FUNCTION log_node_history();