-- Migration: Create RAG Index Tracking Table
-- Purpose: Track which cards/documents have been indexed in the knowledge base
-- This prevents duplicates and allows efficient re-indexing

-- Create rag_index_tracking table
CREATE TABLE IF NOT EXISTS rag_index_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Entity identification
    entity_id UUID NOT NULL,
    entity_type VARCHAR(50) NOT NULL CHECK (entity_type IN ('card', 'document', 'resource')),
    canvas_id UUID NOT NULL,
    
    -- Content tracking
    content_hash VARCHAR(64) NOT NULL, -- SHA-256 hash of content
    content_length INTEGER NOT NULL,
    
    -- Indexing metadata
    indexed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    num_chunks INTEGER NOT NULL DEFAULT 0,
    embedding_model VARCHAR(100) NOT NULL DEFAULT 'all-MiniLM-L6-v2',
    
    -- Status tracking
    index_status VARCHAR(20) NOT NULL DEFAULT 'indexed' CHECK (index_status IN ('indexed', 'pending', 'failed', 'deleted')),
    error_message TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0,
    
    -- Qdrant metadata
    qdrant_collection VARCHAR(100) NOT NULL DEFAULT 'via_canvas_kb',
    qdrant_point_ids TEXT[], -- Array of Qdrant point IDs for this entity
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Unique constraint: one entry per entity
    CONSTRAINT unique_entity_index UNIQUE (entity_id, entity_type)
);

-- Create indexes for efficient queries
CREATE INDEX idx_rag_tracking_entity ON rag_index_tracking(entity_id, entity_type);
CREATE INDEX idx_rag_tracking_canvas ON rag_index_tracking(canvas_id);
CREATE INDEX idx_rag_tracking_status ON rag_index_tracking(index_status);
CREATE INDEX idx_rag_tracking_content_hash ON rag_index_tracking(content_hash);
CREATE INDEX idx_rag_tracking_indexed_at ON rag_index_tracking(indexed_at DESC);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_rag_tracking_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to auto-update updated_at
CREATE TRIGGER trigger_update_rag_tracking_updated_at
    BEFORE UPDATE ON rag_index_tracking
    FOR EACH ROW
    EXECUTE FUNCTION update_rag_tracking_updated_at();

-- Create view for easy querying of indexed entities
CREATE OR REPLACE VIEW rag_indexed_entities AS
SELECT 
    entity_id,
    entity_type,
    canvas_id,
    content_hash,
    content_length,
    num_chunks,
    index_status,
    indexed_at,
    updated_at,
    embedding_model
FROM rag_index_tracking
WHERE index_status = 'indexed'
ORDER BY indexed_at DESC;

-- Create view for entities needing re-indexing
CREATE OR REPLACE VIEW rag_entities_needing_reindex AS
SELECT 
    rt.entity_id,
    rt.entity_type,
    rt.canvas_id,
    rt.content_hash AS old_content_hash,
    rt.indexed_at,
    rt.num_chunks
FROM rag_index_tracking rt
WHERE rt.index_status = 'indexed'
ORDER BY rt.updated_at ASC;

-- Add comments for documentation
COMMENT ON TABLE rag_index_tracking IS 'Tracks which entities have been indexed in the RAG knowledge base';
COMMENT ON COLUMN rag_index_tracking.entity_id IS 'ID of the card, document, or resource';
COMMENT ON COLUMN rag_index_tracking.entity_type IS 'Type of entity: card, document, or resource';
COMMENT ON COLUMN rag_index_tracking.content_hash IS 'SHA-256 hash of content for change detection';
COMMENT ON COLUMN rag_index_tracking.num_chunks IS 'Number of chunks created during indexing';
COMMENT ON COLUMN rag_index_tracking.qdrant_point_ids IS 'Array of Qdrant point IDs for cleanup';
COMMENT ON COLUMN rag_index_tracking.index_status IS 'Current indexing status';

-- Grant permissions (adjust based on your setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON rag_index_tracking TO authenticated;
-- GRANT SELECT ON rag_indexed_entities TO authenticated;
-- GRANT SELECT ON rag_entities_needing_reindex TO authenticated;
