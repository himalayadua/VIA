/**
 * Unit tests for useChat hook
 * 
 * Tests hook functionality, message grouping, and state selectors.
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useChat } from '../../../src/hooks/useChat';
import { useChatStore } from '../../../src/store/chatStore';

// Mock chatUtils
vi.mock('../../../src/utils/chatUtils', () => ({
  groupMessagesByTurn: vi.fn((messages) => {
    // Simple mock implementation
    const groups: any[] = [];
    let currentGroup: any = null;

    messages.forEach((msg: any) => {
      if (msg.role === 'user') {
        if (currentGroup) {
          groups.push(currentGroup);
        }
        currentGroup = { type: 'user', messages: [msg] };
      } else if (msg.role === 'assistant') {
        if (!currentGroup || currentGroup.type !== 'assistant') {
          if (currentGroup) {
            groups.push(currentGroup);
          }
          currentGroup = { type: 'assistant', messages: [msg] };
        } else {
          currentGroup.messages.push(msg);
        }
      }
    });

    if (currentGroup) {
      groups.push(currentGroup);
    }

    return groups;
  })
}));

describe('useChat', () => {
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
  });

  describe('State Selectors', () => {
    it('should expose messages from store', () => {
      // Arrange
      const messages = [
        { id: 'msg_1', role: 'user' as const, content: 'Hello', timestamp: new Date().toISOString() }
      ];
      act(() => {
        useChatStore.setState({ messages });
      });

      // Act
      const { result } = renderHook(() => useChat());

      // Assert
      expect(result.current.messages).toEqual(messages);
    });

    it('should expose inputMessage from store', () => {
      // Arrange
      const inputMessage = 'Test message';
      act(() => {
        useChatStore.setState({ inputMessage });
      });

      // Act
      const { result } = renderHook(() => useChat());

      // Assert
      expect(result.current.inputMessage).toBe(inputMessage);
    });

    it('should expose selectedFiles from store', () => {
      // Arrange
      const selectedFiles = [new File(['test'], 'test.png', { type: 'image/png' })];
      act(() => {
        useChatStore.setState({ selectedFiles });
      });

      // Act
      const { result } = renderHook(() => useChat());

      // Assert
      expect(result.current.selectedFiles).toEqual(selectedFiles);
    });

    it('should expose isTyping from store', () => {
      // Arrange
      act(() => {
        useChatStore.setState({ isTyping: true });
      });

      // Act
      const { result } = renderHook(() => useChat());

      // Assert
      expect(result.current.isTyping).toBe(true);
    });

    it('should expose sessionId from store', () => {
      // Arrange
      const sessionId = 'session_123';
      act(() => {
        useChatStore.setState({ sessionId });
      });

      // Act
      const { result } = renderHook(() => useChat());

      // Assert
      expect(result.current.sessionId).toBe(sessionId);
    });

    it('should expose isConnected from store', () => {
      // Arrange
      act(() => {
        useChatStore.setState({ isConnected: true });
      });

      // Act
      const { result } = renderHook(() => useChat());

      // Assert
      expect(result.current.isConnected).toBe(true);
    });

    it('should expose isSidebarOpen from store', () => {
      // Arrange
      act(() => {
        useChatStore.setState({ isSidebarOpen: true });
      });

      // Act
      const { result } = renderHook(() => useChat());

      // Assert
      expect(result.current.isSidebarOpen).toBe(true);
    });
  });

  describe('Streaming State', () => {
    it('should expose currentStreamingMessage', () => {
      // Arrange
      const streamingMessage = 'I can help you...';
      act(() => {
        useChatStore.setState({ currentStreamingMessage: streamingMessage });
      });

      // Act
      const { result } = renderHook(() => useChat());

      // Assert
      expect(result.current.currentStreamingMessage).toBe(streamingMessage);
    });

    it('should expose toolExecutions', () => {
      // Arrange
      const toolExecutions = [
        {
          id: 'tool_123',
          toolName: 'search_canvas_content',
          toolInput: { query: 'nodes' },
          isComplete: false
        }
      ];
      act(() => {
        useChatStore.setState({ toolExecutions });
      });

      // Act
      const { result } = renderHook(() => useChat());

      // Assert
      expect(result.current.toolExecutions).toEqual(toolExecutions);
    });

    it('should expose currentReasoning', () => {
      // Arrange
      const reasoning = {
        text: 'Searching for nodes...',
        isActive: true
      };
      act(() => {
        useChatStore.setState({ currentReasoning: reasoning });
      });

      // Act
      const { result } = renderHook(() => useChat());

      // Assert
      expect(result.current.currentReasoning).toEqual(reasoning);
    });
  });

  describe('Error State', () => {
    it('should expose error from store', () => {
      // Arrange
      const error = 'Connection failed';
      act(() => {
        useChatStore.setState({ error });
      });

      // Act
      const { result } = renderHook(() => useChat());

      // Assert
      expect(result.current.error).toBe(error);
    });
  });

  describe('Actions', () => {
    it('should expose sendMessage action', () => {
      // Act
      const { result } = renderHook(() => useChat());

      // Assert
      expect(typeof result.current.sendMessage).toBe('function');
    });

    it('should expose sendMultimodalMessage action', () => {
      // Act
      const { result } = renderHook(() => useChat());

      // Assert
      expect(typeof result.current.sendMultimodalMessage).toBe('function');
    });

    it('should expose addMessage action', () => {
      // Act
      const { result } = renderHook(() => useChat());

      // Assert
      expect(typeof result.current.addMessage).toBe('function');
    });

    it('should expose clearChat action', () => {
      // Act
      const { result } = renderHook(() => useChat());

      // Assert
      expect(typeof result.current.clearChat).toBe('function');
    });

    it('should expose setInputMessage action', () => {
      // Act
      const { result } = renderHook(() => useChat());

      // Assert
      expect(typeof result.current.setInputMessage).toBe('function');
    });

    it('should expose sidebar actions', () => {
      // Act
      const { result } = renderHook(() => useChat());

      // Assert
      expect(typeof result.current.toggleSidebar).toBe('function');
      expect(typeof result.current.openSidebar).toBe('function');
      expect(typeof result.current.closeSidebar).toBe('function');
    });
  });

  describe('Message Grouping', () => {
    it('should group consecutive assistant messages', () => {
      // Arrange
      const messages = [
        { id: 'msg_1', role: 'user' as const, content: 'Hello', timestamp: '2024-01-01T10:00:00Z' },
        { id: 'msg_2', role: 'assistant' as const, content: 'Hi', timestamp: '2024-01-01T10:01:00Z' },
        { id: 'msg_3', role: 'assistant' as const, content: 'How can I help?', timestamp: '2024-01-01T10:02:00Z' }
      ];
      act(() => {
        useChatStore.setState({ messages });
      });

      // Act
      const { result } = renderHook(() => useChat());

      // Assert
      expect(result.current.groupedMessages).toBeDefined();
      expect(Array.isArray(result.current.groupedMessages)).toBe(true);
      // Should have 2 groups: 1 user, 1 assistant (with 2 messages)
      expect(result.current.groupedMessages.length).toBe(2);
      expect(result.current.groupedMessages[0].type).toBe('user');
      expect(result.current.groupedMessages[1].type).toBe('assistant');
      expect(result.current.groupedMessages[1].messages.length).toBe(2);
    });

    it('should handle alternating user and assistant messages', () => {
      // Arrange
      const messages = [
        { id: 'msg_1', role: 'user' as const, content: 'Hello', timestamp: '2024-01-01T10:00:00Z' },
        { id: 'msg_2', role: 'assistant' as const, content: 'Hi', timestamp: '2024-01-01T10:01:00Z' },
        { id: 'msg_3', role: 'user' as const, content: 'How are you?', timestamp: '2024-01-01T10:02:00Z' },
        { id: 'msg_4', role: 'assistant' as const, content: 'Good!', timestamp: '2024-01-01T10:03:00Z' }
      ];
      act(() => {
        useChatStore.setState({ messages });
      });

      // Act
      const { result } = renderHook(() => useChat());

      // Assert
      expect(result.current.groupedMessages.length).toBe(4);
    });

    it('should handle empty messages array', () => {
      // Arrange
      act(() => {
        useChatStore.setState({ messages: [] });
      });

      // Act
      const { result } = renderHook(() => useChat());

      // Assert
      expect(result.current.groupedMessages).toBeDefined();
      expect(result.current.groupedMessages.length).toBe(0);
    });
  });

  describe('Hook Updates', () => {
    it('should update when store state changes', () => {
      // Arrange
      const { result } = renderHook(() => useChat());
      expect(result.current.messages.length).toBe(0);

      // Act
      act(() => {
        useChatStore.getState().addMessage({
          id: 'msg_1',
          role: 'user',
          content: 'Test',
          timestamp: new Date().toISOString()
        });
      });

      // Assert
      expect(result.current.messages.length).toBe(1);
    });

    it('should update groupedMessages when messages change', () => {
      // Arrange
      const { result } = renderHook(() => useChat());
      expect(result.current.groupedMessages.length).toBe(0);

      // Act
      act(() => {
        useChatStore.setState({
          messages: [
            { id: 'msg_1', role: 'user' as const, content: 'Hello', timestamp: new Date().toISOString() }
          ]
        });
      });

      // Assert
      expect(result.current.groupedMessages.length).toBeGreaterThan(0);
    });
  });
});
