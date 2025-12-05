/**
 * SuggestedQuestions Component
 * 
 * Displays suggested questions to help users get started with the chat.
 */

import { Sparkles } from 'lucide-react';

interface SuggestedQuestionsProps {
  onQuestionClick: (question: string) => void;
  enabledTools?: string[];
}

const DEFAULT_QUESTIONS = [
  {
    text: "What nodes are in my canvas?",
    tool: "get_canvas_titles",
    color: "blue"
  },
  {
    text: "Find nodes tagged with #project",
    tool: "get_canvas_tags",
    color: "emerald"
  },
  {
    text: "Search for 'meeting notes'",
    tool: "search_canvas_content",
    color: "purple"
  },
  {
    text: "Show me similar ideas",
    tool: "find_similar_nodes",
    color: "pink"
  }
];

export const SuggestedQuestions = ({ 
  onQuestionClick,
  enabledTools = []
}: SuggestedQuestionsProps) => {
  // Filter questions based on enabled tools (if provided)
  const questions = enabledTools.length > 0
    ? DEFAULT_QUESTIONS.filter(q => enabledTools.includes(q.tool))
    : DEFAULT_QUESTIONS;

  const getColorClasses = (color: string) => {
    const colors = {
      blue: 'border-blue-500/30 hover:border-blue-500/60 hover:bg-blue-500/5',
      emerald: 'border-emerald-500/30 hover:border-emerald-500/60 hover:bg-emerald-500/5',
      purple: 'border-purple-500/30 hover:border-purple-500/60 hover:bg-purple-500/5',
      pink: 'border-pink-500/30 hover:border-pink-500/60 hover:bg-pink-500/5'
    };
    return colors[color as keyof typeof colors] || colors.blue;
  };

  return (
    <div className="space-y-3 animate-fade-in">
      <p className="text-sm text-slate-400 text-center">
        Try asking:
      </p>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
        {questions.map((question, index) => (
          <button
            key={index}
            onClick={() => onQuestionClick(question.text)}
            className={`
              flex items-start gap-2 p-3 rounded-lg border-2 
              ${getColorClasses(question.color)}
              transition-all duration-200 text-left
              group
            `}
            style={{ animationDelay: `${index * 100}ms` }}
          >
            <Sparkles className="w-4 h-4 text-slate-400 group-hover:text-yellow-400 transition-colors flex-shrink-0 mt-0.5" />
            <span className="text-sm text-slate-300 group-hover:text-slate-100 transition-colors">
              {question.text}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
};
