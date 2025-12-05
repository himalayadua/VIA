-- Create message_bus_events table
-- Tracks inter-agent communication events

CREATE TABLE IF NOT EXISTS message_bus_events (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  event_id UUID UNIQUE NOT NULL DEFAULT uuid_generate_v4(),
  event_type VARCHAR(100) NOT NULL,
  source_agent VARCHAR(100) NOT NULL,
  target_agent VARCHAR(100),
  payload JSONB DEFAULT '{}',
  priority INTEGER DEFAULT 0, -- Higher = more urgent (0-10)
  processing_status VARCHAR(20) DEFAULT 'pending', -- pending, processing, completed, failed
  created_at TIMESTAMP DEFAULT NOW(),
  processed_at TIMESTAMP,
  completed_at TIMESTAMP,
  error_message TEXT,
  retry_count INTEGER DEFAULT 0,
  max_retries INTEGER DEFAULT 3
);

-- Create indexes for performance
CREATE INDEX idx_message_bus_events_status ON message_bus_events(processing_status);
CREATE INDEX idx_message_bus_events_created ON message_bus_events(created_at DESC);
CREATE INDEX idx_message_bus_events_target ON message_bus_events(target_agent, processing_status);
CREATE INDEX idx_message_bus_events_source ON message_bus_events(source_agent);
CREATE INDEX idx_message_bus_events_event_type ON message_bus_events(event_type);
CREATE INDEX idx_message_bus_events_priority ON message_bus_events(priority DESC, created_at ASC) 
  WHERE processing_status = 'pending';

-- Add comments
COMMENT ON TABLE message_bus_events IS 'Tracks inter-agent communication events for multi-agent coordination';
COMMENT ON COLUMN message_bus_events.event_type IS 'Type of event: agent.task.delegate, agent.result.notify, canvas.update, card.created, action.trigger';
COMMENT ON COLUMN message_bus_events.payload IS 'JSONB containing event-specific data and parameters';
COMMENT ON COLUMN message_bus_events.priority IS 'Event priority (0-10, higher = more urgent)';
COMMENT ON COLUMN message_bus_events.target_agent IS 'Target agent ID (null for broadcast events)';

-- Function to cleanup old completed events (retention policy)
CREATE OR REPLACE FUNCTION cleanup_old_message_bus_events()
RETURNS INTEGER AS $$
DECLARE
  deleted_count INTEGER;
BEGIN
  DELETE FROM message_bus_events
  WHERE processing_status IN ('completed', 'failed')
    AND completed_at < NOW() - INTERVAL '7 days';
  
  GET DIAGNOSTICS deleted_count = ROW_COUNT;
  RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_old_message_bus_events() IS 'Deletes message bus events older than 7 days that are completed or failed';

-- Optional: Create a scheduled job to run cleanup (requires pg_cron extension)
-- SELECT cron.schedule('cleanup-message-bus', '0 2 * * *', 'SELECT cleanup_old_message_bus_events()');
