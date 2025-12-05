/**
 * Unit tests for ChatStore (Zustand store)
 * 
 * Tests chat state management, message handling, and settings persistence.
 */
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { act } from '@testing-library/react';
import { useChatStore } from '../../../src/store/chatStore';
import type { ChatSettings } from '../../../src/components/chat/SettingsModal';

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => { store[key] = value; },
    removeItem: (key: string) => { delete store[key]; },
    clear: () => { store = {}; }
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock
});

// Mock chatApi
vi.mock('../../../src/lib/chatApi', () => ({
  streamChat: vi.fn(),
  uploadFiles: vi.fn(),
  getChatHistory: vi.fn(),
  createSession: vi.fn(),
  clearSession: vi.fn()
}));

describe('ChatStore', () => {
  beforeEach(() => {
    // Reset store state before each test
    useChatStore.setState({
      messages: [],
      inputMessage: '',
      selectedFiles: [],
      sessionId: null,
      isTyping: false,
      isConnected: false,
      isSidebarOpen: false,
      currentStreamingMessage: '',
      toolExecutions: [],
      currentReasoning: null,
      error: null,
      errorType: null,
      isRetryable: false,
      lastFailedMessage: null,
      settings: {
        model: 'meta/llama-3.3-70b-instruct',
        apiKey: '',
        temperature: 0.7,
        maxTokens: 2048
      }
    });
    
    // Clear localStorage
    localStorageMock.clear();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Message Management', () => {
    it('should add message to messages array', () => {
      // Arrange
      const message = {
        id: 'msg_1',
        role: 'user' as const,
        content: 'Hello',
        timestamp: new Date().toISOString()
      };

      // Act
      act(() => {
        useChatStore.getState().addMessage(message);
      });

      // Assert
      const state = useChatStore.getState();
      expect(state.messages).toHaveLength(1);
      expect(state.messages[0]).toEqual(message);
    });

    it('should clear all messages', () => {
      // Arrange
      const messages = [
        { id: 'msg_1', role: 'user' as const, content: 'Hello', timestamp: new Date().toISOString() },
        { id: 'msg_2', role: 'assistant' as const, content: 'Hi', timestamp: new Date().toISOString() }
      ];
      act(() => {
        messages.forEach(msg => useChatStore.getState().addMessage(msg));
      });

      // Act
      act(() => {
        useChatStore.getState().clearChat();
      });

      // Assert
      const state = useChatStore.getState();
      expect(state.messages).toHaveLength(0);
      expect(state.sessionId).toBeNull();
      expect(state.currentStreamingMessage).toBe('');
      expect(state.toolExecutions).toHaveLength(0);
    });

    it('should update input message', () => {
      // Arrange
      const newMessage = 'What nodes do I have?';

      // Act
      act(() => {
        useChatStore.getState().setInputMessage(newMessage);
      });

      // Assert
      const state = useChatStore.getState();
      expect(state.inputMessage).toBe(newMessage);
    });
  });

  describe('File Management', () => {
    it('should add selected file', () => {
      // Arrange
      const file = new File(['test'], 'test.png', { type: 'image/png' });

      // Act
      act(() => {
        useChatStore.getState().addSelectedFile(file);
      });

      // Assert
      const state = useChatStore.getState();
      expect(state.selectedFiles).toHaveLength(1);
      expect(state.selectedFiles[0]).toBe(file);
    });

    it('should remove selected file by index', () => {
      // Arrange
      const files = [
        new File(['test1'], 'test1.png', { type: 'image/png' }),
        new File(['test2'], 'test2.png', { type: 'image/png' })
      ];
      act(() => {
        files.forEach(file => useChatStore.getState().addSelectedFile(file));
      });

      // Act
      act(() => {
        useChatStore.getState().removeSelectedFile(0);
      });

      // Assert
      const state = useChatStore.getState();
      expect(state.selectedFiles).toHaveLength(1);
      expect(state.selectedFiles[0].name).toBe('test2.png');
    });

    it('should set selected files', () => {
      // Arrange
      const files = [
        new File(['test1'], 'test1.png', { type: 'image/png' }),
        new File(['test2'], 'test2.png', { type: 'image/png' })
      ];

      // Act
      act(() => {
        useChatStore.getState().setSelectedFiles(files);
      });

      // Assert
      const state = useChatStore.getState();
      expect(state.selectedFiles).toHaveLength(2);
      expect(state.selectedFiles).toEqual(files);
    });
  });

  describe('Session Management', () => {
    it('should set session ID', () => {
      // Arrange
      const sessionId = 'session_123';

      // Act
      act(() => {
        useChatStore.getState().setSessionId(sessionId);
      });

      // Assert
      const state = useChatStore.getState();
      expect(state.sessionId).toBe(sessionId);
    });

    it('should persist session ID to localStorage', () => {
      // Arrange
      const sessionId = 'session_123';

      // Act
      act(() => {
        useChatStore.getState().setSessionId(sessionId);
      });

      // Assert
      expect(localStorageMock.getItem('chat_session_id')).toBe(sessionId);
    });

    it('should clear session ID on clearChat', async () => {
      // Arrange
      const sessionId = 'session_123';
      act(() => {
        useChatStore.getState().setSessionId(sessionId);
      });

      // Act
      await act(async () => {
        await useChatStore.getState().clearChat();
      });

      // Assert
      const state = useChatStore.getState();
      expect(state.sessionId).toBeNull();
      expect(localStorageMock.getItem('chat_session_id')).toBeNull();
    });
  });

  describe('Streaming State', () => {
    it('should set typing state', () => {
      // Act
      act(() => {
        useChatStore.setState({ isTyping: true });
      });

      // Assert
      const state = useChatStore.getState();
      expect(state.isTyping).toBe(true);
    });

    it('should update streaming message', () => {
      // Arrange
      const streamingText = 'I can help you with';

      // Act
      act(() => {
        useChatStore.setState({ currentStreamingMessage: streamingText });
      });

      // Assert
      const state = useChatStore.getState();
      expect(state.currentStreamingMessage).toBe(streamingText);
    });

    it('should set connection status', () => {
      // Act
      act(() => {
        useChatStore.setState({ isConnected: true });
      });

      // Assert
      const state = useChatStore.getState();
      expect(state.isConnected).toBe(true);
    });
  });

  describe('Tool Execution Tracking', () => {
    it('should track tool executions', () => {
      // Arrange
      const toolExecution = {
        id: 'tool_123',
        toolName: 'search_canvas_content',
        toolInput: { query: 'nodes' },
        isComplete: false
      };

      // Act
      act(() => {
        useChatStore.setState({
          toolExecutions: [toolExecution]
        });
      });

      // Assert
      const state = useChatStore.getState();
      expect(state.toolExecutions).toHaveLength(1);
      expect(state.toolExecutions[0]).toEqual(toolExecution);
    });

    it('should clear tool executions', () => {
      // Arrange
      const toolExecution = {
        id: 'tool_123',
        toolName: 'search_canvas_content',
        toolInput: { query: 'nodes' },
        isComplete: false
      };
      act(() => {
        useChatStore.setState({ toolExecutions: [toolExecution] });
      });

      // Act
      act(() => {
        useChatStore.setState({ toolExecutions: [] });
      });

      // Assert
      const state = useChatStore.getState();
      expect(state.toolExecutions).toHaveLength(0);
    });
  });

  describe('Reasoning State', () => {
    it('should set current reasoning', () => {
      // Arrange
      const reasoning = {
        text: 'I need to search for nodes in the canvas',
        isActive: true
      };

      // Act
      act(() => {
        useChatStore.setState({ currentReasoning: reasoning });
      });

      // Assert
      const state = useChatStore.getState();
      expect(state.currentReasoning).toEqual(reasoning);
    });

    it('should clear reasoning', () => {
      // Arrange
      const reasoning = {
        text: 'Thinking...',
        isActive: true
      };
      act(() => {
        useChatStore.setState({ currentReasoning: reasoning });
      });

      // Act
      act(() => {
        useChatStore.setState({ currentReasoning: null });
      });

      // Assert
      const state = useChatStore.getState();
      expect(state.currentReasoning).toBeNull();
    });
  });

  describe('Error Handling', () => {
    it('should set error message', () => {
      // Arrange
      const errorMessage = 'Connection failed';

      // Act
      act(() => {
        useChatStore.getState().setError(errorMessage);
      });

      // Assert
      const state = useChatStore.getState();
      expect(state.error).toBe(errorMessage);
    });

    it('should clear error', () => {
      // Arrange
      act(() => {
        useChatStore.getState().setError('Some error');
      });

      // Act
      act(() => {
        useChatStore.getState().clearError();
      });

      // Assert
      const state = useChatStore.getState();
      expect(state.error).toBeNull();
      expect(state.errorType).toBeNull();
      expect(state.isRetryable).toBe(false);
    });
  });

  describe('Sidebar State', () => {
    it('should toggle sidebar', () => {
      // Arrange
      const initialState = useChatStore.getState().isSidebarOpen;

      // Act
      act(() => {
        useChatStore.getState().toggleSidebar();
      });

      // Assert
      const state = useChatStore.getState();
      expect(state.isSidebarOpen).toBe(!initialState);
    });

    it('should open sidebar', () => {
      // Act
      act(() => {
        useChatStore.getState().openSidebar();
      });

      // Assert
      const state = useChatStore.getState();
      expect(state.isSidebarOpen).toBe(true);
    });

    it('should close sidebar', () => {
      // Arrange
      act(() => {
        useChatStore.getState().openSidebar();
      });

      // Act
      act(() => {
        useChatStore.getState().closeSidebar();
      });

      // Assert
      const state = useChatStore.getState();
      expect(state.isSidebarOpen).toBe(false);
    });
  });

  describe('Settings Management', () => {
    it('should update settings', () => {
      // Arrange
      const newSettings: ChatSettings = {
        model: 'meta/llama-3.1-405b-instruct',
        apiKey: 'test-key',
        temperature: 0.9,
        maxTokens: 4096
      };

      // Act
      act(() => {
        useChatStore.getState().updateSettings(newSettings);
      });

      // Assert
      const state = useChatStore.getState();
      expect(state.settings).toEqual(newSettings);
    });

    it('should persist settings to localStorage', () => {
      // Arrange
      const newSettings: ChatSettings = {
        model: 'meta/llama-3.1-405b-instruct',
        apiKey: 'test-key',
        temperature: 0.9,
        maxTokens: 4096
      };

      // Act
      act(() => {
        useChatStore.getState().updateSettings(newSettings);
      });

      // Assert
      const stored = localStorageMock.getItem('chat_settings');
      expect(stored).toBeTruthy();
      expect(JSON.parse(stored!)).toEqual(newSettings);
    });
  });
});
