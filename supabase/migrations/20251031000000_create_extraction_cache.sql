/*
  # Create Extraction Cache Table

  ## Changes
  - Create extraction_cache table to store cached URL extractions
  - Add indexes for efficient lookups and expiry cleanup
  - Add trigger for automatic updated_at timestamp

  ## Purpose
  Cache extracted content from URLs to avoid re-fetching (Task 15.1, Requirement 2.5)
  
  ## Benefits
  - Faster response times for repeated URLs
  - Reduced API calls to external services
  - Lower bandwidth usage
  - Better user experience
*/

-- Create extraction_cache table
CREATE TABLE IF NOT EXISTS extraction_cache (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  url TEXT NOT NULL UNIQUE,
  url_hash TEXT NOT NULL UNIQUE,
  content_type TEXT NOT NULL,
  extracted_data JSONB NOT NULL,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '24 hours'),
  hit_count INTEGER DEFAULT 0,
  last_accessed_at TIMESTAMPTZ,
  CONSTRAINT valid_content_type CHECK (content_type IN ('documentation', 'github', 'video', 'pdf', 'generic'))
);

-- Create indexes for efficient queries
CREATE INDEX idx_extraction_cache_url ON extraction_cache(url);
CREATE INDEX idx_extraction_cache_url_hash ON extraction_cache(url_hash);
CREATE INDEX idx_extraction_cache_expires_at ON extraction_cache(expires_at);
CREATE INDEX idx_extraction_cache_content_type ON extraction_cache(content_type);
CREATE INDEX idx_extraction_cache_created_at ON extraction_cache(created_at);

-- Create trigger to auto-update updated_at
CREATE OR REPLACE FUNCTION update_extraction_cache_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_extraction_cache_timestamp
  BEFORE UPDATE ON extraction_cache
  FOR EACH ROW
  EXECUTE FUNCTION update_extraction_cache_updated_at();

-- Create function to cleanup expired cache entries
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS INTEGER AS $$
DECLARE
  deleted_count INTEGER;
BEGIN
  DELETE FROM extraction_cache
  WHERE expires_at < NOW();
  
  GET DIAGNOSTICS deleted_count = ROW_COUNT;
  RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Add comments for documentation
COMMENT ON TABLE extraction_cache IS 'Caches extracted content from URLs to avoid re-fetching';
COMMENT ON COLUMN extraction_cache.url IS 'Original URL that was extracted';
COMMENT ON COLUMN extraction_cache.url_hash IS 'MD5 hash of URL for faster lookups';
COMMENT ON COLUMN extraction_cache.content_type IS 'Type of content extracted (documentation, github, video, pdf, generic)';
COMMENT ON COLUMN extraction_cache.extracted_data IS 'JSON data containing extracted content structure';
COMMENT ON COLUMN extraction_cache.metadata IS 'Additional metadata (extractor version, processing time, etc.)';
COMMENT ON COLUMN extraction_cache.expires_at IS 'When this cache entry expires (default 24 hours)';
COMMENT ON COLUMN extraction_cache.hit_count IS 'Number of times this cache entry was accessed';
COMMENT ON COLUMN extraction_cache.last_accessed_at IS 'Last time this cache entry was accessed';

-- Create a view for cache statistics
CREATE OR REPLACE VIEW extraction_cache_stats AS
SELECT
  content_type,
  COUNT(*) as total_entries,
  COUNT(*) FILTER (WHERE expires_at > NOW()) as valid_entries,
  COUNT(*) FILTER (WHERE expires_at <= NOW()) as expired_entries,
  SUM(hit_count) as total_hits,
  AVG(hit_count) as avg_hits_per_entry,
  MIN(created_at) as oldest_entry,
  MAX(created_at) as newest_entry,
  pg_size_pretty(SUM(pg_column_size(extracted_data))) as total_data_size
FROM extraction_cache
GROUP BY content_type
UNION ALL
SELECT
  'TOTAL' as content_type,
  COUNT(*) as total_entries,
  COUNT(*) FILTER (WHERE expires_at > NOW()) as valid_entries,
  COUNT(*) FILTER (WHERE expires_at <= NOW()) as expired_entries,
  SUM(hit_count) as total_hits,
  AVG(hit_count) as avg_hits_per_entry,
  MIN(created_at) as oldest_entry,
  MAX(created_at) as newest_entry,
  pg_size_pretty(SUM(pg_column_size(extracted_data))) as total_data_size
FROM extraction_cache;

COMMENT ON VIEW extraction_cache_stats IS 'Statistics about cache usage by content type';

