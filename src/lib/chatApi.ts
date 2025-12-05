/**
 * Chat API Client
 * 
 * Handles all chat-related API calls including SSE streaming,
 * file uploads, session management, and chat history.
 */

import { Message, ImageData } from '../store/chatStore';
import type { ChatSettings } from '../components/chat/SettingsModal';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:3000';

// SSE Event types
export type SSEEventType = 
  | 'init' 
  | 'thinking' 
  | 'response' 
  | 'reasoning' 
  | 'tool_use' 
  | 'tool_result' 
  | 'progress'  // NEW: Progress tracking
  | 'complete' 
  | 'error';

export interface SSEEvent {
  type: SSEEventType;
  data?: string;
  text?: string;
  message?: string;
  toolUseId?: string;
  name?: string;
  input?: Record<string, any>;
  result?: string;
  images?: ImageData[];
  // NEW: Progress tracking fields
  operation_id?: string;
  operation_type?: string;
  step?: string;
  progress?: number;  // 0.0 to 1.0
  cards_created?: number;
  estimated_time?: number;
  can_cancel?: boolean;
}

export interface StreamChatOptions {
  message: string;
  sessionId?: string | null;
  canvasId?: string;
  settings: ChatSettings;
  onEvent: (event: SSEEvent) => void;
  onSessionId?: (sessionId: string) => void;
  onError?: (error: Error) => void;
}

export interface UploadFilesOptions {
  message: string;
  files: File[];
  sessionId?: string | null;
  canvasId?: string;
  settings: ChatSettings;
  onEvent: (event: SSEEvent) => void;
  onSessionId?: (sessionId: string) => void;
  onError?: (error: Error) => void;
}

/**
 * Stream chat messages using Server-Sent Events
 */
export async function streamChat(options: StreamChatOptions): Promise<void> {
  const { message, sessionId, canvasId, settings, onEvent, onSessionId, onError } = options;

  try {
    const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(sessionId && { 'X-Session-ID': sessionId })
      },
      body: JSON.stringify({
        message,
        session_id: sessionId,
        canvas_id: canvasId,
        model: settings.model,
        api_key: settings.apiKey,
        temperature: settings.temperature,
        max_tokens: settings.maxTokens
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    // Extract session ID from response headers
    const newSessionId = response.headers.get('X-Session-ID');
    if (newSessionId && onSessionId) {
      onSessionId(newSessionId);
    }

    // Handle SSE stream
    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) {
      throw new Error('No response body');
    }

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('event:')) {
          // Event type line (not used currently)
          continue;
        }

        if (line.startsWith('data:')) {
          try {
            const data = JSON.parse(line.substring(5).trim());
            onEvent(data as SSEEvent);
          } catch (e) {
            console.error('Error parsing SSE data:', e);
          }
        }
      }
    }
  } catch (error) {
    console.error('Error streaming chat:', error);
    if (onError) {
      onError(error instanceof Error ? error : new Error('Failed to stream chat'));
    }
    throw error;
  }
}

/**
 * Upload files and stream multimodal chat messages
 */
export async function uploadFiles(options: UploadFilesOptions): Promise<void> {
  const { message, files, sessionId, canvasId, settings, onEvent, onSessionId, onError } = options;

  try {
    // Prepare FormData
    const formData = new FormData();
    formData.append('message', message);
    if (sessionId) formData.append('session_id', sessionId);
    if (canvasId) formData.append('canvas_id', canvasId);
    formData.append('model', settings.model);
    formData.append('api_key', settings.apiKey);
    formData.append('temperature', settings.temperature.toString());
    formData.append('max_tokens', settings.maxTokens.toString());
    files.forEach(file => formData.append('files', file));

    const response = await fetch(`${API_BASE_URL}/api/chat/multimodal`, {
      method: 'POST',
      headers: {
        ...(sessionId && { 'X-Session-ID': sessionId })
      },
      body: formData
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    // Extract session ID from response headers
    const newSessionId = response.headers.get('X-Session-ID');
    if (newSessionId && onSessionId) {
      onSessionId(newSessionId);
    }

    // Handle SSE stream
    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) {
      throw new Error('No response body');
    }

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('data:')) {
          try {
            const data = JSON.parse(line.substring(5).trim());
            onEvent(data as SSEEvent);
          } catch (e) {
            console.error('Error parsing SSE data:', e);
          }
        }
      }
    }
  } catch (error) {
    console.error('Error uploading files:', error);
    if (onError) {
      onError(error instanceof Error ? error : new Error('Failed to upload files'));
    }
    throw error;
  }
}

/**
 * Get chat history for a session
 */
export async function getChatHistory(sessionId: string): Promise<Message[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/chat/history/${sessionId}`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    
    // Convert backend messages to frontend format
    const messages: Message[] = data.messages.map((msg: any) => ({
      id: msg.id,
      role: msg.role,
      content: msg.content,
      timestamp: msg.created_at,
      uploadedFiles: msg.files || [],
      toolExecutions: msg.tool_executions || [],
      images: msg.images || []
    }));

    return messages;
  } catch (error) {
    console.error('Error loading chat history:', error);
    throw error;
  }
}

/**
 * Create a new chat session
 */
export async function createSession(canvasId?: string): Promise<string> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/chat/session`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ canvas_id: canvasId })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data.session_id;
  } catch (error) {
    console.error('Error creating session:', error);
    throw error;
  }
}

/**
 * Clear/delete a chat session
 */
export async function clearSession(sessionId: string): Promise<void> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/chat/session/${sessionId}`, {
      method: 'DELETE'
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
  } catch (error) {
    console.error('Error clearing session:', error);
    throw error;
  }
}
