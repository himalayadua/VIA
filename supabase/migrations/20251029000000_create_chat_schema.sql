/*
  # Chat Sidebar Schema

  ## Overview
  This migration creates the database schema for the Chat Sidebar feature,
  which provides AI-powered chat functionality with conversation history.

  ## Tables Created

  ### 1. `chat_sessions`
  Stores chat session metadata
  - `id` (uuid, primary key) - Unique session identifier
  - `canvas_id` (uuid, foreign key) - Associated canvas
  - `created_at` (timestamptz) - Creation timestamp
  - `updated_at` (timestamptz) - Last update timestamp
  - `last_activity` (timestamptz) - Last activity timestamp for cleanup

  ### 2. `chat_messages`
  Stores individual chat messages
  - `id` (uuid, primary key) - Unique message identifier
  - `session_id` (uuid, foreign key) - Parent session
  - `role` (text) - Message role (user, assistant, system)
  - `content` (text) - Message content
  - `files` (jsonb) - Attached files metadata
  - `tool_executions` (jsonb) - Tool execution metadata
  - `images` (jsonb) - Generated images metadata
  - `created_at` (timestamptz) - Creation timestamp

  ## Indexes
  - Indexes on foreign keys for optimal query performance
  - Index on session_id for quick message retrieval
  - Index on created_at for temporal queries
  - Index on last_activity for session cleanup

  ## Triggers
  - Auto-update last_activity on new messages
*/

-- Create chat_sessions table
CREATE TABLE IF NOT EXISTS chat_sessions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  canvas_id uuid REFERENCES canvases(id) ON DELETE CASCADE,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),
  last_activity timestamptz DEFAULT now()
);

-- Create chat_messages table
CREATE TABLE IF NOT EXISTS chat_messages (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id uuid NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
  role text NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
  content text NOT NULL,
  files jsonb DEFAULT '[]'::jsonb,
  tool_executions jsonb DEFAULT '[]'::jsonb,
  images jsonb DEFAULT '[]'::jsonb,
  created_at timestamptz DEFAULT now()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_chat_sessions_canvas_id ON chat_sessions(canvas_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_last_activity ON chat_sessions(last_activity);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at);
CREATE INDEX IF NOT EXISTS idx_chat_messages_role ON chat_messages(role);

-- Enable Row Level Security
ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;

-- Create RLS Policies (permissive for demo, can be restricted with auth later)
CREATE POLICY "Allow public read access to chat_sessions"
  ON chat_sessions FOR SELECT
  USING (true);

CREATE POLICY "Allow public insert to chat_sessions"
  ON chat_sessions FOR INSERT
  WITH CHECK (true);

CREATE POLICY "Allow public update to chat_sessions"
  ON chat_sessions FOR UPDATE
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Allow public delete from chat_sessions"
  ON chat_sessions FOR DELETE
  USING (true);

CREATE POLICY "Allow public read access to chat_messages"
  ON chat_messages FOR SELECT
  USING (true);

CREATE POLICY "Allow public insert to chat_messages"
  ON chat_messages FOR INSERT
  WITH CHECK (true);

CREATE POLICY "Allow public update to chat_messages"
  ON chat_messages FOR UPDATE
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Allow public delete from chat_messages"
  ON chat_messages FOR DELETE
  USING (true);

-- Create function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_chat_session_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for updated_at
CREATE TRIGGER update_chat_sessions_updated_at
  BEFORE UPDATE ON chat_sessions
  FOR EACH ROW
  EXECUTE FUNCTION update_chat_session_updated_at();

-- Create function to automatically update session last_activity on new messages
CREATE OR REPLACE FUNCTION update_session_last_activity()
RETURNS TRIGGER AS $$
BEGIN
  UPDATE chat_sessions
  SET last_activity = now()
  WHERE id = NEW.session_id;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to update last_activity
CREATE TRIGGER update_session_activity_on_message
  AFTER INSERT ON chat_messages
  FOR EACH ROW
  EXECUTE FUNCTION update_session_last_activity();

-- Create function to clean up old inactive sessions
CREATE OR REPLACE FUNCTION cleanup_inactive_chat_sessions(max_age_hours integer DEFAULT 24)
RETURNS integer AS $$
DECLARE
  deleted_count integer;
BEGIN
  DELETE FROM chat_sessions
  WHERE last_activity < (now() - (max_age_hours || ' hours')::interval);
  
  GET DIAGNOSTICS deleted_count = ROW_COUNT;
  RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Add comment for documentation
COMMENT ON TABLE chat_sessions IS 'Chat sessions for AI assistant conversations';
COMMENT ON TABLE chat_messages IS 'Individual messages within chat sessions';
COMMENT ON FUNCTION cleanup_inactive_chat_sessions IS 'Cleanup function to remove inactive sessions older than specified hours';
