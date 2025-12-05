/**
 * CanvasAwareIndicator Component
 * 
 * Visual indicator showing when AI is using canvas knowledge
 */

import { Brain, Sparkles, Network } from 'lucide-react';

interface CanvasAwareIndicatorProps {
  type: 'canvas-query' | 'recommendation' | 'gap-analysis';
  cardCount?: number;
}

export const CanvasAwareIndicator = ({ type, cardCount }: CanvasAwareIndicatorProps) => {
  const config = {
    'canvas-query': {
      icon: Brain,
      text: 'Based on your canvas',
      color: 'text-blue-400',
      bgColor: 'bg-blue-600/10',
      borderColor: 'border-blue-500/30'
    },
    'recommendation': {
      icon: Sparkles,
      text: 'AI Recommendation',
      color: 'text-purple-400',
      bgColor: 'bg-purple-600/10',
      borderColor: 'border-purple-500/30'
    },
    'gap-analysis': {
      icon: Network,
      text: 'Knowledge Gap Identified',
      color: 'text-orange-400',
      bgColor: 'bg-orange-600/10',
      borderColor: 'border-orange-500/30'
    }
  };
  
  const { icon: Icon, text, color, bgColor, borderColor } = config[type];
  
  return (
    <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border ${bgColor} ${borderColor} mb-2`}>
      <Icon className={`w-4 h-4 ${color}`} />
      <span className={`text-xs font-medium ${color}`}>{text}</span>
      {cardCount !== undefined && cardCount > 0 && (
        <span className="text-xs text-slate-400">
          ({cardCount} card{cardCount !== 1 ? 's' : ''})
        </span>
      )}
    </div>
  );
};
