"""
Index Tracker

Tracks which entities have been indexed in the knowledge base.
Uses PostgreSQL to prevent duplicates and enable efficient re-indexing.
"""

import logging
import hashlib
from typing import Optional, List, Dict, Any
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


class IndexTracker:
    """Tracks indexed entities in PostgreSQL"""
    
    def __init__(self, db_config: Dict[str, Any]):
        """
        Initialize Index Tracker
        
        Args:
            db_config: Database configuration dict
        """
        self.db_config = db_config
        self.conn = None
        self._connect()
    
    def _connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            logger.info("IndexTracker connected to PostgreSQL")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise
    
    def _ensure_connection(self):
        """Ensure database connection is alive"""
        if self.conn is None or self.conn.closed:
            self._connect()
    
    @staticmethod
    def compute_content_hash(content: str) -> str:
        """Compute SHA-256 hash of content"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    async def is_indexed(
        self,
        entity_id: str,
        entity_type: str
    ) -> bool:
        """
        Check if entity is already indexed
        
        Args:
            entity_id: Entity ID
            entity_type: Entity type (card, document, resource)
        
        Returns:
            True if indexed
        """
        self._ensure_connection()
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT EXISTS(
                        SELECT 1 FROM rag_index_tracking
                        WHERE entity_id = %s AND entity_type = %s AND index_status = 'indexed'
                    )
                    """,
                    (entity_id, entity_type)
                )
                return cur.fetchone()[0]
        except Exception as e:
            logger.error(f"Error checking if indexed: {e}")
            return False
    
    async def needs_reindex(
        self,
        entity_id: str,
        entity_type: str,
        current_content: str
    ) -> bool:
        """
        Check if entity needs re-indexing (content changed)
        
        Args:
            entity_id: Entity ID
            entity_type: Entity type
            current_content: Current content
        
        Returns:
            True if needs re-indexing
        """
        self._ensure_connection()
        
        current_hash = self.compute_content_hash(current_content)
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT content_hash FROM rag_index_tracking
                    WHERE entity_id = %s AND entity_type = %s AND index_status = 'indexed'
                    """,
                    (entity_id, entity_type)
                )
                result = cur.fetchone()
                
                if not result:
                    return True  # Not indexed yet
                
                stored_hash = result[0]
                return stored_hash != current_hash
        
        except Exception as e:
            logger.error(f"Error checking if needs reindex: {e}")
            return True  # Re-index on error to be safe
    
    async def record_index(
        self,
        entity_id: str,
        entity_type: str,
        canvas_id: str,
        content: str,
        num_chunks: int,
        qdrant_point_ids: List[str],
        embedding_model: str = "all-MiniLM-L6-v2",
        qdrant_collection: str = "via_canvas_kb"
    ) -> bool:
        """
        Record successful indexing
        
        Args:
            entity_id: Entity ID
            entity_type: Entity type
            canvas_id: Canvas ID
            content: Content that was indexed
            num_chunks: Number of chunks created
            qdrant_point_ids: List of Qdrant point IDs
            embedding_model: Model used for embeddings
            qdrant_collection: Qdrant collection name
        
        Returns:
            True if successful
        """
        self._ensure_connection()
        
        content_hash = self.compute_content_hash(content)
        content_length = len(content)
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO rag_index_tracking (
                        entity_id, entity_type, canvas_id, content_hash, content_length,
                        num_chunks, embedding_model, index_status, qdrant_collection,
                        qdrant_point_ids, indexed_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, 'indexed', %s, %s, NOW()
                    )
                    ON CONFLICT (entity_id, entity_type)
                    DO UPDATE SET
                        canvas_id = EXCLUDED.canvas_id,
                        content_hash = EXCLUDED.content_hash,
                        content_length = EXCLUDED.content_length,
                        num_chunks = EXCLUDED.num_chunks,
                        embedding_model = EXCLUDED.embedding_model,
                        index_status = 'indexed',
                        qdrant_collection = EXCLUDED.qdrant_collection,
                        qdrant_point_ids = EXCLUDED.qdrant_point_ids,
                        indexed_at = NOW(),
                        error_message = NULL,
                        retry_count = 0
                    """,
                    (
                        entity_id, entity_type, canvas_id, content_hash, content_length,
                        num_chunks, embedding_model, qdrant_collection, qdrant_point_ids
                    )
                )
                self.conn.commit()
                logger.info(f"Recorded index for {entity_type}/{entity_id}")
                return True
        
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error recording index: {e}")
            return False
    
    async def record_index_failure(
        self,
        entity_id: str,
        entity_type: str,
        canvas_id: str,
        error_message: str
    ) -> bool:
        """
        Record indexing failure
        
        Args:
            entity_id: Entity ID
            entity_type: Entity type
            canvas_id: Canvas ID
            error_message: Error message
        
        Returns:
            True if successful
        """
        self._ensure_connection()
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO rag_index_tracking (
                        entity_id, entity_type, canvas_id, content_hash, content_length,
                        index_status, error_message, retry_count
                    ) VALUES (
                        %s, %s, %s, '', 0, 'failed', %s, 1
                    )
                    ON CONFLICT (entity_id, entity_type)
                    DO UPDATE SET
                        index_status = 'failed',
                        error_message = EXCLUDED.error_message,
                        retry_count = rag_index_tracking.retry_count + 1,
                        updated_at = NOW()
                    """,
                    (entity_id, entity_type, canvas_id, error_message)
                )
                self.conn.commit()
                logger.info(f"Recorded index failure for {entity_type}/{entity_id}")
                return True
        
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error recording index failure: {e}")
            return False
    
    async def mark_deleted(
        self,
        entity_id: str,
        entity_type: str
    ) -> bool:
        """
        Mark entity as deleted
        
        Args:
            entity_id: Entity ID
            entity_type: Entity type
        
        Returns:
            True if successful
        """
        self._ensure_connection()
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE rag_index_tracking
                    SET index_status = 'deleted', updated_at = NOW()
                    WHERE entity_id = %s AND entity_type = %s
                    """,
                    (entity_id, entity_type)
                )
                self.conn.commit()
                logger.info(f"Marked as deleted: {entity_type}/{entity_id}")
                return True
        
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error marking as deleted: {e}")
            return False
    
    async def get_qdrant_point_ids(
        self,
        entity_id: str,
        entity_type: str
    ) -> Optional[List[str]]:
        """
        Get Qdrant point IDs for an entity
        
        Args:
            entity_id: Entity ID
            entity_type: Entity type
        
        Returns:
            List of point IDs or None
        """
        self._ensure_connection()
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT qdrant_point_ids FROM rag_index_tracking
                    WHERE entity_id = %s AND entity_type = %s
                    """,
                    (entity_id, entity_type)
                )
                result = cur.fetchone()
                return result[0] if result else None
        
        except Exception as e:
            logger.error(f"Error getting point IDs: {e}")
            return None
    
    async def get_indexed_entities(
        self,
        canvas_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get list of indexed entities
        
        Args:
            canvas_id: Optional canvas ID filter
            entity_type: Optional entity type filter
            limit: Maximum number of results
        
        Returns:
            List of indexed entities
        """
        self._ensure_connection()
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = """
                    SELECT entity_id, entity_type, canvas_id, content_hash,
                           content_length, num_chunks, index_status, indexed_at,
                           embedding_model
                    FROM rag_index_tracking
                    WHERE index_status = 'indexed'
                """
                params = []
                
                if canvas_id:
                    query += " AND canvas_id = %s"
                    params.append(canvas_id)
                
                if entity_type:
                    query += " AND entity_type = %s"
                    params.append(entity_type)
                
                query += " ORDER BY indexed_at DESC LIMIT %s"
                params.append(limit)
                
                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]
        
        except Exception as e:
            logger.error(f"Error getting indexed entities: {e}")
            return []
    
    async def get_stats(self, canvas_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get indexing statistics
        
        Args:
            canvas_id: Optional canvas ID filter
        
        Returns:
            Statistics dictionary
        """
        self._ensure_connection()
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = """
                    SELECT 
                        COUNT(*) as total_entities,
                        SUM(CASE WHEN index_status = 'indexed' THEN 1 ELSE 0 END) as indexed_count,
                        SUM(CASE WHEN index_status = 'failed' THEN 1 ELSE 0 END) as failed_count,
                        SUM(CASE WHEN index_status = 'pending' THEN 1 ELSE 0 END) as pending_count,
                        SUM(num_chunks) as total_chunks,
                        SUM(content_length) as total_content_length
                    FROM rag_index_tracking
                """
                params = []
                
                if canvas_id:
                    query += " WHERE canvas_id = %s"
                    params.append(canvas_id)
                
                cur.execute(query, params)
                result = cur.fetchone()
                return dict(result) if result else {}
        
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}
    
    def close(self):
        """Close database connection"""
        if self.conn and not self.conn.closed:
            self.conn.close()
            logger.info("IndexTracker connection closed")
