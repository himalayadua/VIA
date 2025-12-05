"""
Content Extraction Agent - URL and Code Analysis

Specialized agent for extracting and processing external content.
Handles URL extraction, code analysis, and entity extraction.
"""

import logging
from strands import Agent, tool
from typing import Optional

# Import extraction tools
from tools.youtube_tools import get_transcript_snippets_in_range
from tools.canvas_tools import extract_url_content, grow_card_content

logger = logging.getLogger(__name__)

# Import centralized prompts
from prompts import PromptTemplates


@tool
def content_extraction_agent(user_query: str, canvas_id: str):
    """
    Specialized agent for content extraction tasks with canvas creation capabilities.
    
    Use this agent when the user wants to:
    - Extract content from URLs (automatically creates cards)
    - Grow/expand existing cards
    - Import from external sources (GitHub, documentation, videos)
    - Get YouTube video transcripts
    
    Args:
        user_query: The user's extraction request
        canvas_id: Canvas ID where content will be added
        
    Returns:
        Extraction results as string
    """
    import re
    from .model_provider import get_nvidia_nim_model
    from tool_manager import ToolManager
    
    logger.info(f"Content extraction agent processing: {user_query[:50]}...")
    
    # PRE-PROCESSING: Detect URLs and call extract_url_content directly
    # This bypasses the LLM's tendency to respond conversationally
    url_pattern = r'(?:https?://)?(?:www\.)?([a-zA-Z0-9-]+\.(?:com|org|dev|io|net|edu|gov|co|ai|app|tech|info|me|us|uk|ca|de|fr|jp|cn|in|au|br|ru|es|it|nl|se|no|dk|fi|pl|cz|gr|tr|za|mx|ar|cl|pe|ve|co\.uk|co\.in|co\.jp|co\.kr|co\.nz|co\.za|com\.au|com\.br|com\.mx|com\.ar|com\.co|com\.pe|com\.ve)(?:/[^\s]*)?)'
    
    urls = re.findall(url_pattern, user_query, re.IGNORECASE)
    
    if urls:
        # Found URL(s) - extract directly without asking LLM
        logger.info(f"Detected URL in query, extracting directly: {urls[0]}")
        
        # Reconstruct full URL
        url_match = re.search(url_pattern, user_query, re.IGNORECASE)
        if url_match:
            url = url_match.group(0)
            # Add https:// if missing
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Call extract_url_content directly
            try:
                result = extract_url_content(url=url, canvas_id=canvas_id)
                
                if result.get('success'):
                    return f"✅ Created {result['total_cards']} cards from {url}\n\nParent card: {result['parent_card_id']}\nChild cards: {len(result['child_card_ids'])}"
                else:
                    return f"❌ Failed to extract from {url}: {result.get('error', 'Unknown error')}"
            except Exception as e:
                logger.error(f"Error extracting URL: {e}", exc_info=True)
                return f"❌ Error extracting {url}: {str(e)}"
    
    # No URL detected - use agent for other extraction tasks
    # Get model instance
    model = get_nvidia_nim_model()
    
    # Get extraction tools (includes canvas creation tools)
    tool_manager = ToolManager()
    extraction_tools = tool_manager.get_extraction_tools()
    
    # Add YouTube transcript tool
    extraction_tools.append(get_transcript_snippets_in_range)
    
    # Create agent with extraction tools
    agent = Agent(
        system_prompt=PromptTemplates.content_extraction_system_prompt(),
        model=model,
        tools=extraction_tools
    )
    
    # Add context
    query_with_context = f"Canvas ID: {canvas_id}\n\nUser Query: {user_query}"
    
    # Get response
    response = agent(query_with_context)
    
    logger.info("Content extraction agent completed")
    return str(response)
