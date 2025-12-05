/**
 * useChat Hook
 * 
 * Custom React hook that provides a clean interface to the chat store.
 * Simplifies component usage by exposing only relevant chat functionality.
 */

import { useChatStore } from '../store/chatStore';
import { groupMessagesByTurn } from '../utils/chatUtils';

/**
 * Custom hook for chat functionality
 * 
 * Provides access to chat state and actions with a clean API.
 * Includes message grouping for easier rendering of conversation turns.
 * 
 * @example
 * ```tsx
 * function ChatComponent() {
 *   const { messages, sendMessage, isTyping, groupedMessages } = useChat();
 *   
 *   return (
 *     <div>
 *       {groupedMessages.map(group => (
 *         <MessageGroup key={group.type} group={group} />
 *       ))}
 *     </div>
 *   );
 * }
 * ```
 */
export function useChat() {
  // Get all state and actions from store
  const messages = useChatStore((state) => state.messages);
  const inputMessage = useChatStore((state) => state.inputMessage);
  const selectedFiles = useChatStore((state) => state.selectedFiles);
  const isTyping = useChatStore((state) => state.isTyping);
  const sessionId = useChatStore((state) => state.sessionId);
  const isConnected = useChatStore((state) => state.isConnected);
  const isSidebarOpen = useChatStore((state) => state.isSidebarOpen);
  const currentStreamingMessage = useChatStore((state) => state.currentStreamingMessage);
  const toolExecutions = useChatStore((state) => state.toolExecutions);
  const currentReasoning = useChatStore((state) => state.currentReasoning);
  const error = useChatStore((state) => state.error);

  // Get actions
  const sendMessage = useChatStore((state) => state.sendMessage);
  const sendMultimodalMessage = useChatStore((state) => state.sendMultimodalMessage);
  const addMessage = useChatStore((state) => state.addMessage);
  const clearChat = useChatStore((state) => state.clearChat);
  const setSessionId = useChatStore((state) => state.setSessionId);
  const setInputMessage = useChatStore((state) => state.setInputMessage);
  const setSelectedFiles = useChatStore((state) => state.setSelectedFiles);
  const addSelectedFile = useChatStore((state) => state.addSelectedFile);
  const removeSelectedFile = useChatStore((state) => state.removeSelectedFile);
  const loadChatHistory = useChatStore((state) => state.loadChatHistory);
  const createNewSession = useChatStore((state) => state.createNewSession);
  const toggleSidebar = useChatStore((state) => state.toggleSidebar);
  const openSidebar = useChatStore((state) => state.openSidebar);
  const closeSidebar = useChatStore((state) => state.closeSidebar);
  const setError = useChatStore((state) => state.setError);
  const clearError = useChatStore((state) => state.clearError);

  // Compute grouped messages for easier rendering
  const groupedMessages = groupMessagesByTurn(messages);

  return {
    // Core state
    messages,
    inputMessage,
    selectedFiles,
    isTyping,
    sessionId,
    isConnected,
    isSidebarOpen,

    // Streaming state
    currentStreamingMessage,
    toolExecutions,
    currentReasoning,

    // Error state
    error,

    // Computed state
    groupedMessages,

    // Actions
    sendMessage,
    sendMultimodalMessage,
    addMessage,
    clearChat,
    setSessionId,
    setInputMessage,
    setSelectedFiles,
    addSelectedFile,
    removeSelectedFile,
    loadChatHistory,
    createNewSession,
    toggleSidebar,
    openSidebar,
    closeSidebar,
    setError,
    clearError,
  };
}
