"""
Rate Limiter for Content Extraction

Prevents overwhelming external services with too many requests.
Uses sliding window algorithm for accurate rate limiting.
"""

import time
import logging
from collections import deque
from typing import Optional

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Rate limiter using sliding window algorithm.
    
    Features:
    - Configurable requests per minute
    - Sliding window tracking
    - Wait/timeout support
    - Request counting
    """
    
    def __init__(self, max_requests_per_minute: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_requests_per_minute: Maximum requests allowed per minute
        """
        self.max_requests = max_requests_per_minute
        self.requests = deque()  # Timestamps of requests
        self.window_size = 60  # seconds
        
        logger.info(f"RateLimiter initialized: {max_requests_per_minute} req/min")
    
    def _clean_old_requests(self):
        """Remove requests outside the sliding window"""
        now = time.time()
        while self.requests and now - self.requests[0] > self.window_size:
            self.requests.popleft()
    
    def check_rate_limit(self) -> bool:
        """
        Check if request is allowed under rate limit.
        
        Returns:
            True if request is allowed, False if rate limited
        """
        self._clean_old_requests()
        
        # Check if under limit
        if len(self.requests) >= self.max_requests:
            logger.warning(f"Rate limit reached: {len(self.requests)}/{self.max_requests}")
            return False
        
        # Add current request
        self.requests.append(time.time())
        logger.debug(f"Request allowed: {len(self.requests)}/{self.max_requests}")
        return True
    
    def wait_if_needed(self, timeout: Optional[float] = None) -> bool:
        """
        Wait until rate limit allows request.
        
        Args:
            timeout: Maximum time to wait in seconds (None = wait forever)
            
        Returns:
            True if request can proceed, False if timeout reached
        """
        start_time = time.time()
        
        while True:
            self._clean_old_requests()
            
            # Check if we can proceed
            if len(self.requests) < self.max_requests:
                self.requests.append(time.time())
                return True
            
            # Check timeout
            if timeout and (time.time() - start_time) > timeout:
                logger.error(f"Rate limit timeout after {timeout}s")
                return False
            
            # Calculate wait time
            if self.requests:
                oldest_request = self.requests[0]
                wait_time = self.window_size - (time.time() - oldest_request)
                sleep_time = min(wait_time + 0.1, 1.0)  # Sleep max 1 second at a time
                
                logger.info(f"Rate limited, waiting {sleep_time:.1f}s...")
                time.sleep(sleep_time)
            else:
                time.sleep(0.1)
    
    def get_remaining_requests(self) -> int:
        """
        Get number of requests remaining in current window.
        
        Returns:
            Number of requests that can be made
        """
        self._clean_old_requests()
        return max(0, self.max_requests - len(self.requests))
    
    def get_wait_time(self) -> float:
        """
        Get estimated wait time until next request is allowed.
        
        Returns:
            Wait time in seconds (0 if request can be made now)
        """
        self._clean_old_requests()
        
        if len(self.requests) < self.max_requests:
            return 0.0
        
        if self.requests:
            oldest_request = self.requests[0]
            wait_time = self.window_size - (time.time() - oldest_request)
            return max(0.0, wait_time)
        
        return 0.0
    
    def reset(self):
        """Reset rate limiter (clear all tracked requests)"""
        self.requests.clear()
        logger.info("Rate limiter reset")
    
    def get_stats(self) -> dict:
        """
        Get rate limiter statistics.
        
        Returns:
            Dictionary with stats
        """
        self._clean_old_requests()
        
        return {
            "max_requests_per_minute": self.max_requests,
            "current_requests": len(self.requests),
            "remaining_requests": self.get_remaining_requests(),
            "wait_time_seconds": self.get_wait_time(),
            "utilization_percent": round((len(self.requests) / self.max_requests) * 100, 1)
        }


# Global rate limiter instances
_global_rate_limiter = None
_github_rate_limiter = None
_youtube_rate_limiter = None


def get_global_rate_limiter() -> RateLimiter:
    """
    Get global rate limiter for general requests.
    
    Returns:
        RateLimiter instance (60 req/min)
    """
    global _global_rate_limiter
    if _global_rate_limiter is None:
        _global_rate_limiter = RateLimiter(max_requests_per_minute=60)
    return _global_rate_limiter


def get_github_rate_limiter() -> RateLimiter:
    """
    Get rate limiter for GitHub API.
    
    Returns:
        RateLimiter instance (60 req/hour = 1 req/min for safety)
    """
    global _github_rate_limiter
    if _github_rate_limiter is None:
        _github_rate_limiter = RateLimiter(max_requests_per_minute=1)
    return _github_rate_limiter


def get_youtube_rate_limiter() -> RateLimiter:
    """
    Get rate limiter for YouTube API.
    
    Returns:
        RateLimiter instance (conservative 30 req/min)
    """
    global _youtube_rate_limiter
    if _youtube_rate_limiter is None:
        _youtube_rate_limiter = RateLimiter(max_requests_per_minute=30)
    return _youtube_rate_limiter
