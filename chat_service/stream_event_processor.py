"""
Stream Event Processor for Via Canvas AI Service

Processes streaming events from Strands agent and formats them as
Server-Sent Events (SSE) for the frontend.
"""

import logging
import json
import asyncio
from typing import AsyncGenerator, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class StreamEventProcessor:
    """
    Processes streaming events from Strands agent
    
    Handles different event types from the agent stream and formats them
    as Server-Sent Events for real-time frontend updates.
    """
    
    def __init__(self):
        """Initialize StreamEventProcessor"""
        self.seen_tool_uses = set()
        logger.debug("StreamEventProcessor initialized")
    
    async def process_stream(
        self,
        agent,
        message: str,
        files: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        canvas_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Process streaming events from agent
        
        Args:
            agent: Strands agent instance
            message: User message
            files: Optional list of file paths
            session_id: Optional session ID
            canvas_id: Optional canvas ID for context
            
        Yields:
            SSE formatted event strings
        """
        try:
            # Reset seen tool uses for new stream
            self.seen_tool_uses.clear()
            
            logger.info(f"Processing stream for session: {session_id}")
            
            # Send init event
            yield self.format_sse({'type': 'init'})
            
            # Create multimodal message if files present
            content = self.create_multimodal_message(message, files)
            
            # Stream from agent
            logger.debug("Starting agent stream...")
            stream = agent.stream_async(content)
            
            async for event in stream:
                # Handle text response
                if event.get('data') and not event.get('reasoning'):
                    yield self.format_sse({
                        'type': 'response',
                        'data': event['data']
                    })
                
                # Handle reasoning (thinking process)
                elif event.get('reasoning') and event.get('reasoningText'):
                    yield self.format_sse({
                        'type': 'reasoning',
                        'text': event['reasoningText']
                    })
                
                # Handle tool use
                elif event.get('current_tool_use'):
                    tool_use = event['current_tool_use']
                    tool_use_id = tool_use.get('toolUseId')
                    
                    # Only process complete tool uses (avoid duplicates)
                    if tool_use_id and tool_use_id not in self.seen_tool_uses:
                        self.seen_tool_uses.add(tool_use_id)
                        
                        # Process tool input
                        tool_input = tool_use.get('input', {})
                        if isinstance(tool_input, str):
                            try:
                                tool_input = json.loads(tool_input)
                            except json.JSONDecodeError:
                                # Input not yet complete, skip
                                continue
                        
                        yield self.format_sse({
                            'type': 'tool_use',
                            'toolUseId': tool_use_id,
                            'name': tool_use.get('name'),
                            'input': tool_input
                        })
                        
                        await asyncio.sleep(0.1)
                
                # Handle tool results
                elif event.get('message') and event['message'].get('content'):
                    for item in event['message']['content']:
                        if isinstance(item, dict) and 'toolResult' in item:
                            tool_result = item['toolResult']
                            yield self.format_sse({
                                'type': 'tool_result',
                                'toolUseId': tool_result.get('toolUseId'),
                                'result': tool_result.get('content')
                            })
                
                # Handle progress updates
                elif event.get('type') == 'progress_update':
                    yield self.format_sse({
                        'type': 'progress',
                        'operation_id': event.get('operation_id'),
                        'operation_type': event.get('operation_type'),
                        'step': event.get('step'),
                        'progress': event.get('progress'),
                        'message': event.get('message'),
                        'cards_created': event.get('cards_created'),
                        'estimated_time': event.get('estimated_time'),
                        'can_cancel': event.get('can_cancel', True)
                    })
                
                # Handle completion
                elif event.get('result'):
                    result = event['result']
                    
                    # Convert AgentResult to dict if needed
                    # Use to_dict() method which properly excludes non-serializable fields like EventLoopMetrics
                    if hasattr(result, 'to_dict'):
                        result = result.to_dict()
                    elif hasattr(result, 'as_dict'):
                        result = result.as_dict()
                    elif hasattr(result, '__dict__'):
                        result = result.__dict__
                    elif not isinstance(result, (dict, str, list)):
                        result = str(result)
                    
                    images = self.extract_images(result)
                    yield self.format_sse({
                        'type': 'complete',
                        'result': result,
                        'images': images
                    })
                    return
            
            logger.info("Stream completed successfully")
                    
        except asyncio.CancelledError:
            logger.info("Stream cancelled by client")
            return
            
        except Exception as e:
            logger.error(f"Stream processing error: {e}", exc_info=True)
            yield self.format_sse({
                'type': 'error',
                'message': str(e)
            })
    
    def format_sse(self, event: dict) -> str:
        """
        Format event as Server-Sent Event
        
        Args:
            event: Event dictionary
            
        Returns:
            SSE formatted string
        """
        try:
            event_type = event.get('type', 'message')
            # Clean the event to ensure it's JSON serializable
            cleaned_event = self._clean_for_json(event)
            data = json.dumps(cleaned_event)
            return f"event: {event_type}\ndata: {data}\n\n"
        except Exception as e:
            logger.error(f"Failed to format SSE event: {e}", exc_info=True)
            # Return a safe error event
            return f"event: error\ndata: {{\"type\": \"error\", \"message\": \"Failed to format event\"}}\n\n"
    
    def _clean_for_json(self, obj):
        """
        Recursively clean an object to make it JSON serializable.
        
        This handles complex objects like EventLoopMetrics, AgentResult, etc.
        
        Args:
            obj: Object to clean
            
        Returns:
            JSON-serializable version of the object
        """
        if obj is None:
            return None
        elif isinstance(obj, (str, int, float, bool)):
            return obj
        elif isinstance(obj, dict):
            return {k: self._clean_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._clean_for_json(item) for item in obj]
        elif hasattr(obj, 'to_dict'):
            # Use to_dict() method if available (e.g., AgentResult)
            return self._clean_for_json(obj.to_dict())
        elif hasattr(obj, 'as_dict'):
            # Use as_dict() method if available
            return self._clean_for_json(obj.as_dict())
        elif hasattr(obj, '__dict__'):
            # Convert dataclass or object to dict
            return self._clean_for_json(obj.__dict__)
        else:
            # For any other type (like EventLoopMetrics), convert to string
            return str(obj)
    
    def create_multimodal_message(
        self, 
        text: str, 
        files: Optional[List[str]] = None
    ):
        """
        Create multimodal message with text and files
        
        Args:
            text: Message text
            files: Optional list of file paths
            
        Returns:
            Text string or multimodal content list
        """
        if not files:
            return text
        
        content = [{'text': text}]
        
        for file_path in files:
            try:
                with open(file_path, 'rb') as f:
                    file_data = f.read()
                
                mime_type = self.get_mime_type(file_path)
                
                if mime_type.startswith('image/'):
                    content.append({
                        'image': {
                            'format': mime_type.split('/')[1],
                            'source': {'bytes': file_data}
                        }
                    })
                elif mime_type == 'application/pdf':
                    import os
                    content.append({
                        'document': {
                            'format': 'pdf',
                            'name': os.path.basename(file_path),
                            'source': {'bytes': file_data}
                        }
                    })
            except Exception as e:
                logger.error(f"Error reading file {file_path}: {e}")
                continue
        
        return content
    
    def get_mime_type(self, file_path: str) -> str:
        """
        Get MIME type of file
        
        Args:
            file_path: Path to file
            
        Returns:
            MIME type string
        """
        import mimetypes
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or 'application/octet-stream'
    
    def extract_images(self, result) -> List[dict]:
        """
        Extract images from result
        
        Args:
            result: Agent result
            
        Returns:
            List of image dicts
        """
        # Placeholder for image extraction
        # Can be enhanced based on result format
        images = []
        
        # Check if result has images
        if isinstance(result, dict) and 'images' in result:
            images = result['images']
        
        return images
    
    def get_current_timestamp(self) -> str:
        """
        Get current timestamp in ISO format
        
        Returns:
            ISO formatted timestamp string
        """
        return datetime.now().isoformat()
