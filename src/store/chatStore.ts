/**
 * Chat Store
 * 
 * Zustand store for managing chat state, messages, and SSE streaming.
 * Handles communication with the backend chat API and session persistence.
 */

import { create } from 'zustand';
import * as chatApi from '../lib/chatApi';
import { ChatErrorHandler, ChatError, ChatErrorType } from '../utils/chatErrorHandler';
import type { ChatSettings } from '../components/chat/SettingsModal';

// Types
export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  uploadedFiles?: FileInfo[];
  images?: ImageData[];
  toolExecutions?: ToolExecution[];
  isToolMessage?: boolean;
  toolUseId?: string;
}

export interface FileInfo {
  name: string;
  size: number;
  type: string;
  url?: string;
}

export interface ImageData {
  id: string;
  url: string;
  alt?: string;
  format?: string;
}

export interface ToolExecution {
  id: string;
  toolName: string;
  toolInput: Record<string, any>;
  toolResult?: string;
  reasoningText?: string;
  images?: ImageData[];
  isComplete: boolean;
  // Progress tracking
  progress?: OperationProgress;
  // Extraction results
  extractionSummary?: ExtractionSummary;
}

export interface ExtractionSummary {
  cards: Array<{
    id: string;
    title: string;
    type: string;
    parent_id?: string | null;
  }>;
  sourceUrl?: string;
  operationType?: string;
}

export interface OperationProgress {
  operation_id: string;
  operation_type: string;
  step: string;
  progress: number;  // 0.0 to 1.0
  message: string;
  cards_created: number;
  estimated_time?: number;
  can_cancel: boolean;
}

export interface ReasoningState {
  text: string;
  isActive: boolean;
}

interface ChatState {
  // Core state
  messages: Message[];
  inputMessage: string;
  selectedFiles: File[];
  isTyping: boolean;
  sessionId: string | null;
  isConnected: boolean;
  isSidebarOpen: boolean;
  
  // Streaming state
  currentStreamingMessage: string;
  toolExecutions: ToolExecution[];
  currentReasoning: ReasoningState | null;
  
  // Error state
  error: string | null;
  errorType: ChatErrorType | null;
  isRetryable: boolean;
  lastFailedMessage: { message: string; files?: File[]; canvasId?: string } | null;
  
  // Settings state
  settings: ChatSettings;
  
  // Actions
  sendMessage: (message: string, canvasId?: string) => Promise<void>;
  sendMultimodalMessage: (message: string, files: File[], canvasId?: string) => Promise<void>;
  addMessage: (message: Message) => void;
  clearChat: () => Promise<void>;
  setSessionId: (id: string) => void;
  setInputMessage: (text: string) => void;
  setSelectedFiles: (files: File[]) => void;
  addSelectedFile: (file: File) => void;
  removeSelectedFile: (index: number) => void;
  loadChatHistory: (sessionId: string) => Promise<void>;
  createNewSession: (canvasId?: string) => Promise<void>;
  toggleSidebar: () => void;
  openSidebar: () => void;
  closeSidebar: () => void;
  setError: (error: string | null) => void;
  setChatError: (error: ChatError) => void;
  clearError: () => void;
  retryLastMessage: () => Promise<void>;
  updateSettings: (settings: ChatSettings) => void;
}

// Helper to generate unique IDs
const generateId = () => `msg_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;

// Default settings
const DEFAULT_SETTINGS: ChatSettings = {
  model: 'meta/llama-3.3-70b-instruct',
  apiKey: '',
  temperature: 0.7,
  maxTokens: 2048
};

// Load settings from localStorage
const SETTINGS_STORAGE_KEY = 'chat_settings';
const loadSettings = (): ChatSettings => {
  try {
    const stored = localStorage.getItem(SETTINGS_STORAGE_KEY);
    if (stored) {
      return { ...DEFAULT_SETTINGS, ...JSON.parse(stored) };
    }
  } catch (error) {
    console.error('Failed to load settings:', error);
  }
  return DEFAULT_SETTINGS;
};

export const useChatStore = create<ChatState>((set, get) => ({
  // Initial state
  messages: [],
  inputMessage: '',
  selectedFiles: [],
  isTyping: false,
  sessionId: null,
  isConnected: true,
  isSidebarOpen: false,
  currentStreamingMessage: '',
  toolExecutions: [],
  currentReasoning: null,
  error: null,
  errorType: null,
  isRetryable: false,
  lastFailedMessage: null,
  settings: loadSettings(),

  // Send text message
  sendMessage: async (message, canvasId) => {
    const { sessionId, addMessage, settings } = get();
    
    if (!message.trim()) return;

    set({ error: null, isTyping: true, currentStreamingMessage: '', toolExecutions: [] });

    // Add user message immediately
    const userMessage: Message = {
      id: generateId(),
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    };
    addMessage(userMessage);

    let assistantMessageContent = '';
    const toolExecutionsMap = new Map<string, ToolExecution>();

    try {
      await chatApi.streamChat({
        message,
        sessionId,
        canvasId,
        settings,
        onSessionId: (newSessionId) => {
          if (newSessionId !== sessionId) {
            get().setSessionId(newSessionId);
          }
        },
        onEvent: (event) => {
          switch (event.type) {
            case 'init':
              set({ isConnected: true });
              break;

            case 'response':
              if (event.data) {
                assistantMessageContent += event.data;
                set({ currentStreamingMessage: assistantMessageContent });
              }
              break;

            case 'reasoning':
              if (event.text) {
                set({
                  currentReasoning: {
                    text: event.text,
                    isActive: true
                  }
                });
              }
              break;

            case 'tool_use':
              if (event.toolUseId) {
                const toolExecution: ToolExecution = {
                  id: event.toolUseId,
                  toolName: event.name || '',
                  toolInput: event.input || {},
                  isComplete: false
                };
                toolExecutionsMap.set(event.toolUseId, toolExecution);
                set({ toolExecutions: Array.from(toolExecutionsMap.values()) });
              }
              break;

            case 'tool_result':
              if (event.toolUseId && toolExecutionsMap.has(event.toolUseId)) {
                const tool = toolExecutionsMap.get(event.toolUseId)!;
                tool.toolResult = event.result;
                tool.isComplete = true;
                
                // Parse extraction summary if this is an extraction tool
                if (tool.toolName.toLowerCase().includes('extract') && event.result) {
                  try {
                    const result = JSON.parse(event.result);
                    if (result.cards && Array.isArray(result.cards)) {
                      tool.extractionSummary = {
                        cards: result.cards,
                        sourceUrl: tool.toolInput?.url as string,
                        operationType: tool.toolName
                      };
                    }
                  } catch (e) {
                    // Not JSON or doesn't have cards, ignore
                  }
                }
                
                set({ toolExecutions: Array.from(toolExecutionsMap.values()) });
              }
              break;

            case 'progress':
              // Handle progress updates for long-running operations
              if (event.operation_id) {
                // Find the tool execution for this operation
                for (const [toolId, tool] of toolExecutionsMap.entries()) {
                  // Match by operation_id in tool result or create new progress
                  if (tool.toolInput?.operation_id === event.operation_id || 
                      toolId === event.operation_id) {
                    tool.progress = {
                      operation_id: event.operation_id,
                      operation_type: event.operation_type || 'unknown',
                      step: event.step || '',
                      progress: event.progress || 0,
                      message: event.message || '',
                      cards_created: event.cards_created || 0,
                      estimated_time: event.estimated_time,
                      can_cancel: event.can_cancel !== false
                    };
                    set({ toolExecutions: Array.from(toolExecutionsMap.values()) });
                    break;
                  }
                }
              }
              break;

            case 'complete':
              // Add final assistant message
              const assistantMessage: Message = {
                id: generateId(),
                role: 'assistant',
                content: assistantMessageContent,
                timestamp: new Date().toISOString(),
                toolExecutions: Array.from(toolExecutionsMap.values()),
                images: event.images || []
              };
              addMessage(assistantMessage);

              set({
                isTyping: false,
                currentStreamingMessage: '',
                toolExecutions: [],
                currentReasoning: null
              });
              
              // Reload canvas if cards were created via tools
              if (canvasId && toolExecutionsMap.size > 0) {
                // Check if any tool execution was a card creation tool
                const hasCardCreation = Array.from(toolExecutionsMap.values()).some(
                  tool => tool.toolName.toLowerCase().includes('extract') || 
                          tool.toolName.toLowerCase().includes('create') ||
                          tool.toolName.toLowerCase().includes('grow')
                );
                
                if (hasCardCreation) {
                  // Reload canvas to show new cards (use setTimeout to ensure it runs after state update)
                  setTimeout(async () => {
                    const { useCanvasStore } = await import('./canvasStore');
                    const loadCanvas = useCanvasStore.getState().loadCanvas;
                    await loadCanvas(canvasId);
                  }, 100);
                }
              }
              break;

            case 'error':
              set({
                error: event.message || 'An error occurred',
                isTyping: false,
                currentStreamingMessage: '',
                toolExecutions: [],
                currentReasoning: null
              });
              break;
          }
        },
        onError: (error) => {
          const chatError = ChatErrorHandler.handleError(error, 'Chat');
          set({
            error: chatError.message,
            errorType: chatError.type,
            isRetryable: chatError.retryable,
            lastFailedMessage: { message, canvasId },
            isTyping: false,
            currentStreamingMessage: '',
            toolExecutions: [],
            currentReasoning: null
          });
        }
      });
    } catch (error) {
      console.error('Error sending message:', error);
      const chatError = ChatErrorHandler.handleError(error, 'Chat');
      set({
        error: chatError.message,
        errorType: chatError.type,
        isRetryable: chatError.retryable,
        lastFailedMessage: { message, canvasId },
        isTyping: false,
        currentStreamingMessage: '',
        toolExecutions: [],
        currentReasoning: null
      });
    }
  },

  // Send multimodal message with files
  sendMultimodalMessage: async (message, files, canvasId) => {
    const { sessionId, addMessage, settings } = get();
    
    if (!message.trim() && files.length === 0) return;

    set({ error: null, isTyping: true, currentStreamingMessage: '', toolExecutions: [] });

    // Add user message with file info
    const userMessage: Message = {
      id: generateId(),
      role: 'user',
      content: message,
      timestamp: new Date().toISOString(),
      uploadedFiles: files.map(f => ({
        name: f.name,
        size: f.size,
        type: f.type
      }))
    };
    addMessage(userMessage);

    let assistantMessageContent = '';
    const toolExecutionsMap = new Map<string, ToolExecution>();

    try {
      await chatApi.uploadFiles({
        message,
        files,
        sessionId,
        canvasId,
        settings,
        onSessionId: (newSessionId) => {
          if (newSessionId !== sessionId) {
            get().setSessionId(newSessionId);
          }
        },
        onEvent: (event) => {
          switch (event.type) {
            case 'response':
              if (event.data) {
                assistantMessageContent += event.data;
                set({ currentStreamingMessage: assistantMessageContent });
              }
              break;

            case 'complete':
              const assistantMessage: Message = {
                id: generateId(),
                role: 'assistant',
                content: assistantMessageContent,
                timestamp: new Date().toISOString(),
                toolExecutions: Array.from(toolExecutionsMap.values()),
                images: event.images || []
              };
              addMessage(assistantMessage);

              set({
                isTyping: false,
                currentStreamingMessage: '',
                toolExecutions: [],
                selectedFiles: [] // Clear selected files after sending
              });
              break;

            case 'error':
              set({
                error: event.message || 'An error occurred',
                isTyping: false,
                currentStreamingMessage: '',
                toolExecutions: []
              });
              break;
          }
        },
        onError: (error) => {
          const chatError = ChatErrorHandler.handleError(error, 'File upload');
          set({
            error: chatError.message,
            errorType: chatError.type,
            isRetryable: chatError.retryable,
            lastFailedMessage: { message, files, canvasId },
            isTyping: false,
            currentStreamingMessage: '',
            toolExecutions: []
          });
        }
      });
    } catch (error) {
      console.error('Error sending multimodal message:', error);
      const chatError = ChatErrorHandler.handleError(error, 'File upload');
      set({
        error: chatError.message,
        errorType: chatError.type,
        isRetryable: chatError.retryable,
        lastFailedMessage: { message, files, canvasId },
        isTyping: false,
        currentStreamingMessage: '',
        toolExecutions: []
      });
    }
  },

  // Add message to state
  addMessage: (message) => {
    set((state) => ({
      messages: [...state.messages, message]
    }));
  },

  // Clear chat
  clearChat: async () => {
    const { sessionId } = get();

    try {
      if (sessionId) {
        await chatApi.clearSession(sessionId);
      }

      // Clear localStorage
      localStorage.removeItem('chat_session_id');

      // Reset state
      set({
        messages: [],
        sessionId: null,
        inputMessage: '',
        selectedFiles: [],
        isTyping: false,
        currentStreamingMessage: '',
        toolExecutions: [],
        currentReasoning: null,
        error: null
      });
    } catch (error) {
      console.error('Error clearing chat:', error);
      set({ error: 'Failed to clear chat' });
    }
  },

  // Set session ID
  setSessionId: (id) => {
    localStorage.setItem('chat_session_id', id);
    set({ sessionId: id });
  },

  // Set input message
  setInputMessage: (text) => {
    set({ inputMessage: text });
  },

  // Set selected files
  setSelectedFiles: (files) => {
    set({ selectedFiles: files });
  },

  // Add selected file
  addSelectedFile: (file) => {
    set((state) => ({
      selectedFiles: [...state.selectedFiles, file]
    }));
  },

  // Remove selected file
  removeSelectedFile: (index) => {
    set((state) => ({
      selectedFiles: state.selectedFiles.filter((_, i) => i !== index)
    }));
  },

  // Load chat history
  loadChatHistory: async (sessionId) => {
    try {
      const messages = await chatApi.getChatHistory(sessionId);
      set({ messages, sessionId });
    } catch (error) {
      console.error('Error loading chat history:', error);
      set({ error: 'Failed to load chat history' });
    }
  },

  // Create new session
  createNewSession: async (canvasId) => {
    try {
      const sessionId = await chatApi.createSession(canvasId);
      get().setSessionId(sessionId);
    } catch (error) {
      console.error('Error creating session:', error);
      set({ error: 'Failed to create session' });
    }
  },

  // Toggle sidebar
  toggleSidebar: () => {
    set((state) => ({ isSidebarOpen: !state.isSidebarOpen }));
  },

  // Open sidebar
  openSidebar: () => {
    set({ isSidebarOpen: true });
  },

  // Close sidebar
  closeSidebar: () => {
    set({ isSidebarOpen: false });
  },

  // Set error
  setError: (error) => {
    set({ error });
  },

  // Set chat error with type and retry info
  setChatError: (chatError) => {
    set({
      error: chatError.message,
      errorType: chatError.type,
      isRetryable: chatError.retryable
    });
  },

  // Clear error
  clearError: () => {
    set({
      error: null,
      errorType: null,
      isRetryable: false
    });
  },

  // Retry last failed message
  retryLastMessage: async () => {
    const { lastFailedMessage, sendMessage, sendMultimodalMessage } = get();
    
    if (!lastFailedMessage) return;

    // Clear error before retry
    set({ error: null, errorType: null, isRetryable: false });

    // Retry based on whether files were included
    if (lastFailedMessage.files && lastFailedMessage.files.length > 0) {
      await sendMultimodalMessage(
        lastFailedMessage.message,
        lastFailedMessage.files,
        lastFailedMessage.canvasId
      );
    } else {
      await sendMessage(lastFailedMessage.message, lastFailedMessage.canvasId);
    }
  },

  // Update settings
  updateSettings: (newSettings) => {
    // Save to localStorage
    localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(newSettings));
    // Update state
    set({ settings: newSettings });
  }
}));

// Helper to validate UUID format
const isValidUUID = (str: string): boolean => {
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  return uuidRegex.test(str);
};

// Initialize store with session from localStorage
const storedSessionId = localStorage.getItem('chat_session_id');
if (storedSessionId) {
  // Validate UUID format - clear if invalid (old format)
  if (isValidUUID(storedSessionId)) {
    useChatStore.getState().setSessionId(storedSessionId);
    useChatStore.getState().loadChatHistory(storedSessionId);
  } else {
    console.warn('Invalid session ID format detected, clearing:', storedSessionId);
    localStorage.removeItem('chat_session_id');
  }
}

