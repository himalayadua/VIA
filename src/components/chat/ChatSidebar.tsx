/**
 * ChatSidebar Component
 * 
 * Main chat interface component with dark theme, resize functionality,
 * and real-time AI chat integration.
 */

import { useState, useRef, useEffect } from 'react';
import { Send, Minimize2, Maximize2, Wifi, WifiOff, Paperclip, X, AlertCircle, RefreshCw, Settings, Brain } from 'lucide-react';
import { useChatStore } from '../../store/chatStore';
import { ChatMessage } from './ChatMessage';
import { AssistantTurn } from './AssistantTurn';
import { TypingIndicator } from './TypingIndicator';
import { Greeting } from './Greeting';
import { SuggestedQuestions } from './SuggestedQuestions';
import { SettingsModal } from './SettingsModal';
import { KnowledgeProfileModal } from './KnowledgeProfileModal';
import { groupMessagesByTurn } from '../../utils/chatUtils';
import { FILE_VALIDATION } from '../../utils/chatErrorHandler';

interface ChatSidebarProps {
  width: number;
  onResize: (width: number) => void;
  canvasId: string | null;
}

export const ChatSidebar = ({ width, onResize, canvasId }: ChatSidebarProps) => {
  const {
    messages,
    inputMessage,
    isTyping,
    isConnected,
    currentStreamingMessage,
    currentReasoning,
    selectedFiles,
    sessionId,
    error,
    isRetryable,
    settings,
    sendMessage,
    sendMultimodalMessage,
    setInputMessage,
    addSelectedFile,
    removeSelectedFile,
    clearError,
    retryLastMessage,
    updateSettings
  } = useChatStore();

  const [isResizing, setIsResizing] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isComposing, setIsComposing] = useState(false);
  const [fileUploadError, setFileUploadError] = useState<string | null>(null);
  const [showSettings, setShowSettings] = useState(false);
  const [showKnowledgeProfile, setShowKnowledgeProfile] = useState(false);
  const sidebarRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Handle resize
  const handleMouseDown = () => {
    setIsResizing(true);
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (isResizing && sidebarRef.current) {
        const newWidth = window.innerWidth - e.clientX;
        if (newWidth >= 250 && newWidth <= 600) {
          onResize(newWidth);
        }
      }
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing, onResize]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping, currentStreamingMessage]);

  // Keyboard navigation - Escape to close sidebar
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !showSettings) {
        // Only close sidebar if settings modal is not open
        setIsCollapsed(true);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [showSettings]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      const newHeight = Math.min(textareaRef.current.scrollHeight, 96); // Max 4 lines
      textareaRef.current.style.height = `${newHeight}px`;
    }
  }, [inputMessage]);

  // Handle send message
  const handleSend = async () => {
    if (!inputMessage.trim() && selectedFiles.length === 0) return;
    if (!canvasId) return;

    try {
      if (selectedFiles.length > 0) {
        await sendMultimodalMessage(inputMessage, selectedFiles, canvasId);
      } else {
        await sendMessage(inputMessage, canvasId);
      }
      setInputMessage('');
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  // Handle key press
  const handleKeyDown = (e: React.KeyboardEvent) => {
    // Don't submit during IME composition (for Asian languages)
    if (e.key === 'Enter' && !e.shiftKey && !isComposing) {
      e.preventDefault();
      handleSend();
    }
  };

  // Handle IME composition events
  const handleCompositionStart = () => {
    setIsComposing(true);
  };

  const handleCompositionEnd = () => {
    setIsComposing(false);
  };

  // Handle file selection
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    
    // Clear previous file upload error
    setFileUploadError(null);
    
    // Validate all files first
    const validation = FILE_VALIDATION.validateFiles(files);
    if (!validation.valid && validation.error) {
      setFileUploadError(validation.error.message);
      // Reset input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      return;
    }
    
    // All files valid, add them
    files.forEach(file => addSelectedFile(file));
    
    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Collapsed state
  if (isCollapsed) {
    return (
      <div className="fixed right-0 top-0 h-full w-12 bg-slate-900 border-l border-slate-700 flex items-center justify-center z-10">
        <button
          onClick={() => setIsCollapsed(false)}
          className="p-2 hover:bg-slate-800 rounded transition-colors"
          title="Expand sidebar"
          aria-label="Expand chat sidebar"
        >
          <Maximize2 className="w-5 h-5 text-slate-400" aria-hidden="true" />
        </button>
      </div>
    );
  }

  return (
    <>
      <div
        ref={sidebarRef}
        className="fixed right-0 top-0 bg-slate-900 border-l border-slate-700 flex flex-col z-10"
        style={{ width: `${width}px`, height: '100vh', paddingTop: '57px' }}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-700">
          <h2 className="text-lg font-semibold text-slate-100">Via</h2>
          
          <div className="flex items-center gap-3">
            {/* Connection Status */}
            <div className="flex items-center gap-2">
              {isConnected ? (
                <>
                  <Wifi className="w-4 h-4 text-green-500" />
                  <span className="text-xs text-slate-400">Connected</span>
                </>
              ) : (
                <>
                  <WifiOff className="w-4 h-4 text-red-500" />
                  <span className="text-xs text-slate-400">Disconnected</span>
                </>
              )}
            </div>

            {/* Knowledge Profile Button */}
            <button
              onClick={() => setShowKnowledgeProfile(true)}
              className="p-1 hover:bg-slate-800 rounded transition-colors"
              title="View knowledge profile"
              aria-label="Open knowledge profile"
            >
              <Brain className="w-4 h-4 text-slate-400" aria-hidden="true" />
            </button>

            {/* Settings Button */}
            <button
              onClick={() => setShowSettings(true)}
              className="p-1 hover:bg-slate-800 rounded transition-colors"
              title="Chat settings"
              aria-label="Open chat settings"
            >
              <Settings className="w-4 h-4 text-slate-400" aria-hidden="true" />
            </button>

            {/* Collapse Button */}
            <button
              onClick={() => setIsCollapsed(true)}
              className="p-1 hover:bg-slate-800 rounded transition-colors"
              title="Collapse sidebar"
              aria-label="Collapse chat sidebar"
            >
              <Minimize2 className="w-4 h-4 text-slate-400" aria-hidden="true" />
            </button>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-900/20 border-b border-red-800 p-3" role="alert" aria-live="assertive">
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-start gap-2 flex-1">
                <AlertCircle className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" aria-hidden="true" />
                <div className="flex-1">
                  <p className="text-sm text-red-400">{error}</p>
                  {isRetryable && (
                    <button
                      onClick={retryLastMessage}
                      className="mt-2 text-xs text-red-300 hover:text-red-200 underline flex items-center gap-1"
                      aria-label="Retry sending message"
                    >
                      <RefreshCw className="w-3 h-3" aria-hidden="true" />
                      Retry
                    </button>
                  )}
                </div>
              </div>
              <button
                onClick={clearError}
                className="text-red-400 hover:text-red-300 flex-shrink-0"
                aria-label="Dismiss error"
              >
                <X className="w-4 h-4" aria-hidden="true" />
              </button>
            </div>
          </div>
        )}

        {/* Messages */}
        <div 
          className="flex-1 overflow-y-auto p-4 space-y-4"
          role="log"
          aria-live="polite"
          aria-relevant="additions"
          aria-label="Chat messages"
        >
          {messages.length === 0 && !isTyping && (
            <div className="mt-8">
              <Greeting />
              <SuggestedQuestions 
                onQuestionClick={(question) => setInputMessage(question)}
                enabledTools={['search_canvas_content', 'get_canvas_titles', 'get_canvas_tags', 'find_similar_nodes']}
              />
            </div>
          )}

          {/* Render grouped messages */}
          {groupMessagesByTurn(messages).map((group, groupIndex) => (
            <div key={`group-${groupIndex}`}>
              {group.type === 'user' ? (
                // Render user messages individually
                group.messages.map((message) => (
                  <div key={message.id} className="mb-3">
                    <ChatMessage message={message} sessionId={sessionId || undefined} />
                  </div>
                ))
              ) : (
                // Render assistant messages as a single turn
                <AssistantTurn
                  messages={group.messages}
                  currentReasoning={
                    groupIndex === groupMessagesByTurn(messages).length - 1 && isTyping
                      ? currentReasoning
                      : null
                  }
                  availableTools={[
                    { name: 'search_canvas_content', icon: '🔍', description: 'Search canvas nodes' },
                    { name: 'get_canvas_titles', icon: '📋', description: 'Get all node titles' },
                    { name: 'get_canvas_tags', icon: '🏷️', description: 'Extract tags' },
                    { name: 'find_similar_nodes', icon: '🔗', description: 'Find similar nodes' }
                  ]}
                  sessionId={sessionId || undefined}
                />
              )}
            </div>
          ))}

          {/* Streaming message */}
          {isTyping && currentStreamingMessage && (
            <div className="flex justify-start gap-2">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center flex-shrink-0">
                <span className="text-white text-sm">🤖</span>
              </div>
              <div className="max-w-[85%] rounded-lg p-3 bg-slate-800 text-slate-100">
                <p className="text-sm whitespace-pre-wrap">{currentStreamingMessage}</p>
                <span className="inline-block w-2 h-4 bg-slate-400 animate-pulse ml-1" />
              </div>
            </div>
          )}

          {/* Typing indicator */}
          {isTyping && !currentStreamingMessage && (
            <TypingIndicator />
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-4 border-t border-slate-700">
          {/* Selected Files */}
          {selectedFiles.length > 0 && (
            <div className="mb-2 flex flex-wrap gap-2">
              {selectedFiles.map((file, index) => (
                <div
                  key={index}
                  className="flex items-center gap-2 bg-slate-800 px-2 py-1 rounded text-xs text-slate-300"
                >
                  <span className="truncate max-w-[150px]">{file.name}</span>
                  <button
                    onClick={() => removeSelectedFile(index)}
                    className="text-slate-400 hover:text-slate-200"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* File Upload Error */}
          {fileUploadError && (
            <div className="mb-2 flex items-start gap-2 bg-red-900/20 border border-red-800 rounded px-3 py-2">
              <AlertCircle className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-xs text-red-400">{fileUploadError}</p>
              </div>
              <button
                onClick={() => setFileUploadError(null)}
                className="text-red-400 hover:text-red-300 flex-shrink-0"
                aria-label="Dismiss file upload error"
              >
                <X className="w-3 h-3" aria-hidden="true" />
              </button>
            </div>
          )}

          <div className="flex gap-2">
            {/* File Upload Button */}
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept="image/*,application/pdf"
              onChange={handleFileSelect}
              className="hidden"
              aria-label="Upload files (images or PDFs)"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              className="bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg p-2 transition-colors"
              title="Attach files"
              aria-label="Attach files"
            >
              <Paperclip className="w-5 h-5" aria-hidden="true" />
            </button>

            {/* Textarea */}
            <textarea
              ref={textareaRef}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              onCompositionStart={handleCompositionStart}
              onCompositionEnd={handleCompositionEnd}
              placeholder="Ask about your canvas..."
              className="flex-1 bg-slate-800 text-slate-100 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none min-h-[40px] max-h-[96px]"
              disabled={isTyping}
              rows={1}
              aria-label="Type your message"
              aria-describedby="message-hint"
            />

            {/* Send Button */}
            <button
              onClick={handleSend}
              className="bg-blue-600 hover:bg-blue-700 text-white rounded-lg px-4 transition-colors self-end disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={(!inputMessage.trim() && selectedFiles.length === 0) || isTyping || !canvasId}
              aria-label="Send message"
              aria-disabled={(!inputMessage.trim() && selectedFiles.length === 0) || isTyping || !canvasId}
              title={!canvasId ? 'Open a canvas first' : 'Send message'}
            >
              <Send className="w-5 h-5" />
            </button>
          </div>

          <p className="text-xs text-slate-500 mt-2">
            Press Enter to send, Shift+Enter for new line
          </p>
        </div>
      </div>

      {/* Resize Handle */}
      <div
        className="fixed top-0 bottom-0 w-1 cursor-col-resize hover:bg-blue-500 transition-colors z-20"
        style={{ right: `${width}px` }}
        onMouseDown={handleMouseDown}
      />

      {/* Knowledge Profile Modal */}
      <KnowledgeProfileModal
        isOpen={showKnowledgeProfile}
        onClose={() => setShowKnowledgeProfile(false)}
      />

      {/* Settings Modal */}
      <SettingsModal
        isOpen={showSettings}
        onClose={() => setShowSettings(false)}
        currentSettings={settings}
        onSave={updateSettings}
      />
    </>
  );
};

