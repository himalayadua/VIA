/**
 * AssistantTurn Component
 * 
 * Groups consecutive assistant messages into a single turn with one avatar.
 * Displays reasoning state and renders messages chronologically.
 */

import { Bot, Brain } from 'lucide-react';
import { Message, ReasoningState } from '../../store/chatStore';
import { Markdown } from '../ui/Markdown';
import { ToolExecutionContainer } from './ToolExecutionContainer';
import { CanvasAwareIndicator } from './CanvasAwareIndicator';
import { extractCardIds } from '../../utils/cardReferenceUtils';

interface AssistantTurnProps {
  messages: Message[];
  currentReasoning?: ReasoningState | null;
  availableTools?: ToolInfo[];
  sessionId?: string;
}

interface ToolInfo {
  name: string;
  icon?: string;
  description?: string;
}

export const AssistantTurn = ({
  messages,
  currentReasoning,
  availableTools,
  sessionId
}: AssistantTurnProps) => {
  if (messages.length === 0) {
    return null;
  }

  // Sort messages chronologically
  const sortedMessages = [...messages].sort((a, b) => 
    new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );

  return (
    <div className="flex justify-start gap-2">
      {/* Single avatar for entire turn */}
      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center flex-shrink-0">
        <Bot className="w-5 h-5 text-white" />
      </div>

      {/* Messages container */}
      <div className="flex-1 max-w-[85%] space-y-3">
        {/* Reasoning indicator (if active) */}
        {currentReasoning && currentReasoning.isActive && (
          <div className="bg-purple-900/20 border border-purple-700/50 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-2">
              <Brain className="w-4 h-4 text-purple-400 animate-pulse" />
              <span className="text-sm font-medium text-purple-300">Thinking...</span>
            </div>
            <p className="text-sm text-slate-300 italic">
              {currentReasoning.text}
            </p>
          </div>
        )}

        {/* Render each message without its own avatar */}
        {sortedMessages.map((message) => (
          <div key={message.id}>
            <MessageContent 
              message={message} 
              sessionId={sessionId}
              availableTools={availableTools}
            />
          </div>
        ))}
      </div>
    </div>
  );
};

/**
 * MessageContent - Renders message content without avatar
 * (since avatar is shown once for the entire turn)
 */
interface MessageContentProps {
  message: Message;
  sessionId?: string;
  availableTools?: ToolInfo[];
}

const MessageContent = ({ message, sessionId, availableTools }: MessageContentProps) => {
  // Detect if message references canvas cards
  const cardIds = message.content ? extractCardIds(message.content) : [];
  const hasCardReferences = cardIds.length > 0;
  
  // Detect if message is a recommendation or gap analysis
  const isRecommendation = message.content?.toLowerCase().includes('recommend') || 
                          message.content?.toLowerCase().includes('suggest');
  const isGapAnalysis = message.content?.toLowerCase().includes('gap') || 
                       message.content?.toLowerCase().includes('missing');
  
  return (
    <div className="bg-slate-800 text-slate-100 rounded-lg p-3">
      {/* Canvas-aware indicator */}
      {hasCardReferences && (
        <CanvasAwareIndicator 
          type="canvas-query" 
          cardCount={cardIds.length}
        />
      )}
      {!hasCardReferences && isRecommendation && (
        <CanvasAwareIndicator type="recommendation" />
      )}
      {!hasCardReferences && isGapAnalysis && (
        <CanvasAwareIndicator type="gap-analysis" />
      )}
      
      {/* File badges */}
      {message.uploadedFiles && message.uploadedFiles.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-2">
          {message.uploadedFiles.map((file, idx) => (
            <div
              key={idx}
              className="flex items-center gap-1 px-2 py-1 rounded text-xs bg-slate-700"
            >
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

      {/* Message content with Markdown */}
      {message.content && (
        <div className="text-slate-100">
          <Markdown size="sm" sessionId={sessionId} toolUseId={message.toolUseId}>
            {message.content}
          </Markdown>
        </div>
      )}

      {/* Tool executions - use ToolExecutionContainer for rich display */}
      {message.toolExecutions && message.toolExecutions.length > 0 && (
        <div className="mt-3">
          <ToolExecutionContainer
            toolExecutions={message.toolExecutions}
            compact={false}
            availableTools={availableTools}
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
      <p className="text-xs opacity-50 mt-2">
        {new Date(message.timestamp).toLocaleTimeString()}
      </p>
    </div>
  );
};
