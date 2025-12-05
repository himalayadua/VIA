"""
Extraction Cache System

Caches extracted content to avoid re-fetching the same URLs.
Uses filesystem storage with MD5 hashed keys and 24-hour expiry.
"""

import os
import json
import hashlib
import time
import logging
from typing import Optional, Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ExtractionCache:
    """
    Cache extracted content to avoid re-fetching.
    
    Features:
    - MD5 hash for cache keys
    - 24-hour expiry
    - Filesystem storage
    - Cache hit/miss logging
    """
    
    def __init__(self, cache_dir: str = "cache/extractions"):
        """
        Initialize extraction cache.
        
        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        logger.info(f"ExtractionCache initialized at: {cache_dir}")
    
    def get_cache_key(self, url: str) -> str:
        """
        Generate MD5 hash of URL for cache key.
        
        Args:
            url: URL to hash
            
        Returns:
            MD5 hash as hex string
        """
        return hashlib.md5(url.encode()).hexdigest()
    
    def get(self, url: str) -> Optional[Dict]:
        """
        Get cached extraction if exists and not expired.
        
        Args:
            url: URL to look up
            
        Returns:
            Cached data if found and valid, None otherwise
        """
        cache_key = self.get_cache_key(url)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        if not os.path.exists(cache_file):
            logger.debug(f"Cache MISS: {url}")
            return None
        
        # Check expiry (24 hours)
        file_age = time.time() - os.path.getmtime(cache_file)
        if file_age > 86400:  # 24 hours in seconds
            logger.info(f"Cache EXPIRED: {url} (age: {file_age/3600:.1f} hours)")
            os.remove(cache_file)
            return None
        
        try:
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
            
            logger.info(f"Cache HIT: {url} (age: {file_age/3600:.1f} hours)")
            return cached_data.get('data')
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Cache read error for {url}: {e}")
            os.remove(cache_file)
            return None
    
    def set(self, url: str, data: Dict):
        """
        Cache extraction result.
        
        Args:
            url: URL being cached
            data: Extracted data to cache
        """
        cache_key = self.get_cache_key(url)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        cache_entry = {
            "url": url,
            "cached_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
            "data": data
        }
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(cache_entry, f, indent=2)
            
            logger.info(f"Cached: {url}")
            
        except Exception as e:
            logger.error(f"Cache write error for {url}: {e}")
    
    def clear_expired(self) -> int:
        """
        Remove all expired cache entries.
        
        Returns:
            Number of entries removed
        """
        count = 0
        
        try:
            for filename in os.listdir(self.cache_dir):
                if not filename.endswith('.json'):
                    continue
                
                filepath = os.path.join(self.cache_dir, filename)
                file_age = time.time() - os.path.getmtime(filepath)
                
                if file_age > 86400:  # 24 hours
                    os.remove(filepath)
                    count += 1
            
            if count > 0:
                logger.info(f"Cleared {count} expired cache entries")
                
        except Exception as e:
            logger.error(f"Error clearing expired cache: {e}")
        
        return count
    
    def clear_all(self) -> int:
        """
        Remove all cache entries.
        
        Returns:
            Number of entries removed
        """
        count = 0
        
        try:
            for filename in os.listdir(self.cache_dir):
                if not filename.endswith('.json'):
                    continue
                
                filepath = os.path.join(self.cache_dir, filename)
                os.remove(filepath)
                count += 1
            
            logger.info(f"Cleared all {count} cache entries")
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
        
        return count
    
    def get_stats(self) -> Dict:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        total = 0
        expired = 0
        total_size = 0
        
        try:
            for filename in os.listdir(self.cache_dir):
                if not filename.endswith('.json'):
                    continue
                
                filepath = os.path.join(self.cache_dir, filename)
                total += 1
                total_size += os.path.getsize(filepath)
                
                file_age = time.time() - os.path.getmtime(filepath)
                if file_age > 86400:
                    expired += 1
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
        
        return {
            "total_entries": total,
            "expired_entries": expired,
            "valid_entries": total - expired,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2)
        }


# Global cache instance
_cache_instance = None


def get_extraction_cache() -> ExtractionCache:
    """
    Get global extraction cache instance.
    
    Returns:
        ExtractionCache instance
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = ExtractionCache()
    return _cache_instance
