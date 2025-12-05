/**
 * SSE Parser Utility
 * 
 * Parses Server-Sent Events (SSE) from streaming responses.
 * Extracts message content, tool executions, and other metadata.
 */

export interface SSEEvent {
  type: string;
  data: any;
}

export interface ParsedStreamData {
  responseText: string;
  toolExecutions: any[];
  images: any[];
  reasoning: string[];
}

/**
 * Parse SSE chunk and extract events
 * 
 * @param chunk - Raw SSE chunk string
 * @returns Array of parsed events
 */
export function parseSSEChunk(chunk: string): SSEEvent[] {
  const events: SSEEvent[] = [];
  const lines = chunk.split('\n');
  
  let currentEvent: { type?: string; data?: string } = {};
  
  for (const line of lines) {
    if (line.startsWith('event:')) {
      currentEvent.type = line.substring(6).trim();
    } else if (line.startsWith('data:')) {
      currentEvent.data = line.substring(5).trim();
    } else if (line.trim() === '' && currentEvent.type && currentEvent.data) {
      // End of event
      try {
        const parsedData = JSON.parse(currentEvent.data);
        events.push({
          type: currentEvent.type,
          data: parsedData
        });
      } catch (error) {
        // If JSON parse fails, use raw data
        events.push({
          type: currentEvent.type,
          data: currentEvent.data
        });
      }
      currentEvent = {};
    }
  }
  
  return events;
}

/**
 * Extract complete message data from SSE events
 * 
 * @param events - Array of SSE events
 * @returns Parsed stream data with response text, tool executions, etc.
 */
export function extractStreamData(events: SSEEvent[]): ParsedStreamData {
  const data: ParsedStreamData = {
    responseText: '',
    toolExecutions: [],
    images: [],
    reasoning: []
  };
  
  const toolUseMap = new Map<string, any>();
  
  for (const event of events) {
    switch (event.type) {
      case 'response':
        // Accumulate response text
        if (event.data && event.data.data) {
          data.responseText += event.data.data;
        }
        break;
        
      case 'tool_use':
        // Store tool use by ID
        if (event.data && event.data.toolUseId) {
          toolUseMap.set(event.data.toolUseId, {
            id: event.data.toolUseId,
            name: event.data.name,
            input: event.data.input,
            result: null
          });
        }
        break;
        
      case 'tool_result':
        // Add result to corresponding tool use
        if (event.data && event.data.toolUseId) {
          const toolUse = toolUseMap.get(event.data.toolUseId);
          if (toolUse) {
            toolUse.result = event.data.result;
          }
        }
        break;
        
      case 'reasoning':
        // Collect reasoning steps
        if (event.data && event.data.text) {
          data.reasoning.push(event.data.text);
        }
        break;
        
      case 'complete':
        // Extract images from completion
        if (event.data && event.data.images) {
          data.images = event.data.images;
        }
        break;
    }
  }
  
  // Convert tool use map to array
  data.toolExecutions = Array.from(toolUseMap.values());
  
  return data;
}

/**
 * Parse complete SSE stream
 * 
 * @param streamChunks - Array of raw SSE chunks
 * @returns Parsed stream data
 */
export function parseCompleteStream(streamChunks: string[]): ParsedStreamData {
  const allEvents: SSEEvent[] = [];
  
  for (const chunk of streamChunks) {
    const events = parseSSEChunk(chunk);
    allEvents.push(...events);
  }
  
  return extractStreamData(allEvents);
}

