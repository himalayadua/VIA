-- Create agent_health table
-- Tracks agent health and status

CREATE TABLE IF NOT EXISTS agent_health (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  agent_id VARCHAR(100) NOT NULL UNIQUE,
  agent_name VARCHAR(200) NOT NULL,
  status VARCHAR(20) DEFAULT 'unknown', -- running, stopped, error, unknown
  last_heartbeat TIMESTAMP DEFAULT NOW(),
  uptime_seconds INTEGER DEFAULT 0,
  restart_count INTEGER DEFAULT 0,
  error_message TEXT,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for agent_health
CREATE INDEX idx_agent_health_status ON agent_health(status);
CREATE INDEX idx_agent_health_heartbeat ON agent_health(last_heartbeat DESC);
CREATE INDEX idx_agent_health_agent_id ON agent_health(agent_id);

-- Trigger to update updated_at for agent_health
CREATE OR REPLACE FUNCTION update_agent_health_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_agent_health_updated_at
  BEFORE UPDATE ON agent_health
  FOR EACH ROW
  EXECUTE FUNCTION update_agent_health_updated_at();

-- Create agent_metrics table
-- Tracks agent performance metrics over time

CREATE TABLE IF NOT EXISTS agent_metrics (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  agent_id VARCHAR(100) NOT NULL,
  timestamp TIMESTAMP DEFAULT NOW(),
  requests_handled INTEGER DEFAULT 0,
  requests_per_minute DECIMAL(10,2) DEFAULT 0,
  average_response_time_ms DECIMAL(10,2) DEFAULT 0,
  error_count INTEGER DEFAULT 0,
  error_rate DECIMAL(5,4) DEFAULT 0,
  memory_usage_mb DECIMAL(10,2) DEFAULT 0,
  cpu_usage_percent DECIMAL(5,2) DEFAULT 0,
  active_tasks INTEGER DEFAULT 0,
  queue_size INTEGER DEFAULT 0,
  metadata JSONB DEFAULT '{}'
);

-- Create indexes for agent_metrics
CREATE INDEX idx_agent_metrics_agent ON agent_metrics(agent_id);
CREATE INDEX idx_agent_metrics_timestamp ON agent_metrics(timestamp DESC);
CREATE INDEX idx_agent_metrics_agent_time ON agent_metrics(agent_id, timestamp DESC);

-- Add comments
COMMENT ON TABLE agent_health IS 'Tracks real-time health status of all AI agents';
COMMENT ON COLUMN agent_health.metadata IS 'JSONB containing agent-specific metadata and configuration';
COMMENT ON COLUMN agent_health.last_heartbeat IS 'Last time agent sent a heartbeat signal';

COMMENT ON TABLE agent_metrics IS 'Tracks performance metrics for AI agents over time';
COMMENT ON COLUMN agent_metrics.metadata IS 'JSONB containing tool usage stats, cache hit rates, and other metrics';
COMMENT ON COLUMN agent_metrics.error_rate IS 'Percentage of requests that resulted in errors (0.0 to 1.0)';

-- Insert default agent health records for known agents
INSERT INTO agent_health (agent_id, agent_name, status) VALUES
  ('chat_agent', 'Chat Agent', 'unknown'),
  ('content_extraction_agent', 'Content Extraction Agent', 'unknown'),
  ('knowledge_graph_agent', 'Knowledge Graph Agent', 'unknown'),
  ('background_intelligence_agent', 'Background Intelligence Agent', 'unknown'),
  ('learning_assistant_agent', 'Learning Assistant Agent', 'unknown')
ON CONFLICT (agent_id) DO NOTHING;
