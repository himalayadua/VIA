"""
NVIDIA NIM Adapter for Strands Agent

Correctly converts NVIDIA NIM responses to Strands StreamEvent format.
Based on Strands Custom Provider documentation and working test example.
"""

from openai import AsyncOpenAI
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class NVIDIAStrandsModel:
    """
    NVIDIA NIM model that follows Strands' StreamEvent format.
    
    This adapter ensures compatibility between NVIDIA NIM's OpenAI-compatible API
    and Strands' expected StreamEvent format for streaming responses.
    """
    
    def __init__(self, api_key: str, model_id: str = "meta/llama-3.1-70b-instruct"):
        """
        Initialize NVIDIA Strands model adapter.
        
        Args:
            api_key: NVIDIA NIM API key
            model_id: Model identifier (default: meta/llama-3.1-70b-instruct)
        """
        # AsyncOpenAI client for NVIDIA
        self.client = AsyncOpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=api_key
        )
        
        self.model_id = model_id
        self.params = {
            "max_tokens": 4096,
            "temperature": 0.7,
            "top_p": 1,
        }
        
        # Properties Strands expects
        self.config = {
            'model_id': model_id,
            'params': self.params
        }
        
        logger.info(f"NVIDIAStrandsModel initialized with model: {model_id}")
    
    def _format_messages(self, messages: List[Dict]) -> List[Dict]:
        """
        Convert Strands message format to NVIDIA format.
        
        Args:
            messages: List of message dicts from Strands
            
        Returns:
            List of formatted messages for NVIDIA API
        """
        formatted = []
        
        for msg in messages:
            content = msg.get('content', '')
            
            # Handle different content formats
            if isinstance(content, str):
                formatted_content = content
            elif isinstance(content, list):
                # Extract text from list of content blocks
                text_parts = []
                for part in content:
                    if isinstance(part, dict) and 'text' in part:
                        text_parts.append(part['text'])
                    elif isinstance(part, str):
                        text_parts.append(part)
                formatted_content = ' '.join(text_parts) if text_parts else ''
            else:
                formatted_content = str(content) if content else ''
            
            formatted.append({
                'role': msg.get('role', 'user'),
                'content': formatted_content
            })
        
        logger.debug(f"Formatted {len(messages)} messages for NVIDIA")
        return formatted
    
    async def stream_async(self, messages: List[Dict], **kwargs):
        """
        Async stream that yields Strands StreamEvent format.
        
        This is the core method that converts NVIDIA NIM streaming responses
        into the format Strands expects.
        
        Args:
            messages: List of conversation messages
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Yields:
            Strands StreamEvent dicts
        """
        logger.info(f"Stream called with {len(messages)} messages")
        
        # Format messages for NVIDIA
        formatted_messages = self._format_messages(messages)
        
        # Skip empty messages
        formatted_messages = [m for m in formatted_messages if m.get('content', '').strip()]
        
        # If no valid messages, add a default one
        if not formatted_messages:
            formatted_messages = [{'role': 'user', 'content': 'Hello'}]
        
        # Prepare parameters
        call_params = {**self.params}
        for key in ['temperature', 'max_tokens', 'top_p']:
            if key in kwargs:
                call_params[key] = kwargs[key]
        
        try:
            # Build request
            request = {
                'model': self.model_id,
                'messages': formatted_messages,
                'stream': True,
                **call_params
            }
            
            logger.debug(f"Calling NVIDIA with {len(formatted_messages)} messages")
            
            # Make async call to NVIDIA
            completion = await self.client.chat.completions.create(**request)
            
            # Yield Strands StreamEvent: messageStart
            yield {
                "messageStart": {
                    "role": "assistant"
                }
            }
            
            # Yield Strands StreamEvent: contentBlockStart
            yield {
                "contentBlockStart": {
                    "start": {}
                }
            }
            
            # Process chunks
            chunk_num = 0
            content_started = False
            collected_content = []
            
            async for chunk in completion:
                chunk_num += 1
                
                # Check if this chunk has actual content
                if chunk.choices and chunk.choices[0].delta:
                    delta = chunk.choices[0].delta
                    content = delta.content
                    
                    # Skip reasoning chunks, only process actual content
                    if content is not None:
                        if not content_started:
                            content_started = True
                            logger.debug(f"Content starts at chunk {chunk_num}")
                        
                        collected_content.append(content)
                        
                        # Yield Strands StreamEvent: contentBlockDelta
                        # IMPORTANT: Use "text" not "content" in delta!
                        yield {
                            "contentBlockDelta": {
                                "delta": {
                                    "text": content
                                }
                            }
                        }
                
                # Check for finish
                if chunk.choices and chunk.choices[0].finish_reason:
                    logger.debug(f"Stream finished at chunk {chunk_num}")
                    logger.debug(f"Total content: {''.join(collected_content)[:100]}...")
            
            # Yield Strands StreamEvent: contentBlockStop
            yield {
                "contentBlockStop": {
                    "stop": {}
                }
            }
            
            # Yield Strands StreamEvent: messageStop
            yield {
                "messageStop": {
                    "stopReason": "stop"
                }
            }
            
        except Exception as e:
            logger.error(f"Error in stream: {e}", exc_info=True)
            
            # Yield error stop events
            yield {
                "contentBlockStop": {
                    "stop": {}
                }
            }
            yield {
                "messageStop": {
                    "stopReason": "error"
                }
            }
    
    def stream(self, *args, **kwargs):
        """
        Stream method that Strands calls.
        
        This method is called by Strands Agent and should return an async generator.
        
        Returns:
            Async generator yielding StreamEvents
        """
        # Get messages from various possible positions
        messages = None
        
        if args:
            if isinstance(args[0], list):
                messages = args[0]
            elif len(args) > 1 and isinstance(args[1], list):
                messages = args[1]
        
        if messages is None and 'messages' in kwargs:
            messages = kwargs['messages']
        
        if messages is None:
            messages = []
        
        # Return async generator directly
        return self.stream_async(messages, **kwargs)
