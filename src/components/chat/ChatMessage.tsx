/**
 * ChatMessage Component
 * 
 * Renders individual chat messages with support for user/assistant roles,
 * file attachments, tool executions, markdown formatting, and avatars.
 */

import { Bot, FileText, Image as ImageIcon } from 'lucide-react';
import { Message } from '../../store/chatStore';
import { Markdown } from '../ui/Markdown';
import { ToolExecutionContainer } from './ToolExecutionContainer';
import { URLHighlight } from './URLHighlight';
import { detectURLs } from '../../utils/urlDetection';

interface ChatMessageProps {
  message: Message;
  sessionId?: string;
}

export const ChatMessage = ({ message, sessionId }: ChatMessageProps) => {
  const isUser = message.role === 'user';

  // Get file icon based on type
  const getFileIcon = (type: string) => {
    if (type.startsWith('image/')) {
      return <ImageIcon className="w-3 h-3" />;
    }
    if (type === 'application/pdf') {
      return <FileText className="w-3 h-3" />;
    }
    return <FileText className="w-3 h-3" />;
  };

  // If this is a tool message, render it differently
  if (message.isToolMessage && message.toolExecutions) {
    return (
      <div className="flex justify-start gap-2">
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center flex-shrink-0">
          <Bot className="w-5 h-5 text-white" />
        </div>
        <div className="max-w-[85%]">
          <ToolExecutionContainer
            toolExecutions={message.toolExecutions}
            sessionId={sessionId}
          />
        </div>
      </div>
    );
  }

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} gap-2`}>
      {/* Avatar for assistant messages */}
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center flex-shrink-0">
          <Bot className="w-5 h-5 text-white" />
        </div>
      )}

      <div
        className={`max-w-[85%] rounded-lg p-3 ${
          isUser
            ? 'bg-blue-600 text-white'
            : 'bg-slate-800 text-slate-100'
        }`}
      >
        {/* File badges (shown above message text) */}
        {message.uploadedFiles && message.uploadedFiles.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-2">
            {message.uploadedFiles.map((file, idx) => (
              <div
                key={idx}
                className={`flex items-center gap-1 px-2 py-1 rounded text-xs ${
                  isUser ? 'bg-blue-700' : 'bg-slate-700'
                }`}
              >
                {getFileIcon(file.type)}
                <span className="truncate max-w-[120px]" title={file.name}>
                  {file.name}
                </span>
                {file.size && (
                  <span className="text-xs opacity-70">
                    ({(file.size / 1024).toFixed(1)}KB)
                  </span>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Message content with URL highlighting for user messages */}
        {message.content && (
          <div className={isUser ? 'text-white' : 'text-slate-100'}>
            {isUser && detectURLs(message.content).length > 0 ? (
              <URLHighlight text={message.content} />
            ) : (
              <Markdown
                size="sm"
                sessionId={sessionId}
                toolUseId={message.toolUseId}
              >
                {message.content}
              </Markdown>
            )}
          </div>
        )}

        {/* Tool executions (inline display for non-tool messages) */}
        {message.toolExecutions && message.toolExecutions.length > 0 && !message.isToolMessage && (
          <div className="mt-3">
            <ToolExecutionContainer
              toolExecutions={message.toolExecutions}
              compact={true}
              sessionId={sessionId}
            />
          </div>
        )}

        {/* Images from message */}
        {message.images && message.images.length > 0 && (
          <div className="mt-2 grid grid-cols-2 gap-2">
            {message.images.map((image) => (
              <img
                key={image.id}
                src={image.url}
                alt={image.alt || 'Generated image'}
                className="rounded border border-slate-600 cursor-pointer hover:border-blue-500 transition-colors"
                onClick={() => window.open(image.url, '_blank')}
              />
            ))}
          </div>
        )}

        {/* Timestamp */}
        <p className={`text-xs mt-2 ${isUser ? 'opacity-70' : 'opacity-50'}`}>
          {new Date(message.timestamp).toLocaleTimeString()}
        </p>
      </div>
    </div>
  );
};

