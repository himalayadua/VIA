/**
 * TypingIndicator Component
 * 
 * Shows animated typing indicator when AI is thinking.
 */

import { Bot } from 'lucide-react';

export const TypingIndicator = () => {
  return (
    <div className="flex justify-start gap-2 animate-fade-in">
      {/* Avatar */}
      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center flex-shrink-0">
        <Bot className="w-5 h-5 text-white" />
      </div>

      {/* Typing animation */}
      <div className="bg-slate-800 rounded-lg p-3">
        <div className="flex items-center gap-2">
          <div className="flex gap-1">
            <div 
              className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" 
              style={{ animationDelay: '0ms' }} 
            />
            <div 
              className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" 
              style={{ animationDelay: '150ms' }} 
            />
            <div 
              className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" 
              style={{ animationDelay: '300ms' }} 
            />
          </div>
          <span className="text-xs text-slate-400 ml-1">AI is thinking...</span>
        </div>
      </div>
    </div>
  );
};
