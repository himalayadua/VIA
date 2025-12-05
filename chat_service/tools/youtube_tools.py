"""
YouTube Tools

Tools for extracting YouTube video content and transcripts.
Uses youtube-transcript-api which doesn't require API keys.
"""

import logging
from typing import Dict
from strands import tool
from youtube_transcript_api import YouTubeTranscriptApi

logger = logging.getLogger(__name__)


@tool
def get_transcript_snippets_in_range(video_id: str, video_start: float, video_end: float) -> dict:
    """
    Fetch YouTube transcript snippets within [video_start, video_end).
    
    Args:
        video_id: The ID following "/watch?v=" in the YouTube URL.
        video_start: Start time in seconds (inclusive).
        video_end: End time in seconds (exclusive).
        
    Returns:
        Dict mapping snippet start times (seconds) to transcript text.
    """
    try:
        api = YouTubeTranscriptApi()
        transcript_snippets = api.fetch(video_id)
        
        filtered: dict = {}
        for snippet in transcript_snippets:
            start = getattr(snippet, "start", None)
            text = getattr(snippet, "text", None)
            
            if start is None or text is None:
                # Fallback if API returns dicts instead of objects
                if isinstance(snippet, dict):
                    start = snippet.get("start")
                    text = snippet.get("text")
                    
            if start is None or text is None:
                continue
                
            if start >= float(video_start) and start < float(video_end):
                filtered[start] = text
        
        logger.info(f"Found {len(filtered)} transcript snippets for video {video_id} in range {video_start}-{video_end}s")
        return filtered
        
    except Exception as e:
        logger.error(f"Error getting transcript for video {video_id}: {e}")
        return {}
