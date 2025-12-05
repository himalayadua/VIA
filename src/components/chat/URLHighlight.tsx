/**
 * URLHighlight Component
 * 
 * Displays text with detected URLs highlighted and classified by type
 */

import { ExternalLink } from 'lucide-react';
import { highlightURLs, getURLTypeIcon, getURLTypeColor } from '../../utils/urlDetection';

interface URLHighlightProps {
  text: string;
  className?: string;
}

export const URLHighlight = ({ text, className = '' }: URLHighlightProps) => {
  const parts = highlightURLs(text);

  return (
    <span className={className}>
      {parts.map((part, index) => {
        if (part.type === 'text') {
          return <span key={index}>{part.content}</span>;
        }

        // URL part
        const urlData = part.urlData!;
        const icon = getURLTypeIcon(urlData.type);
        const colorClass = getURLTypeColor(urlData.type);

        return (
          <span
            key={index}
            className={`inline-flex items-center gap-1 ${colorClass} hover:underline cursor-pointer group`}
            onClick={(e) => {
              e.stopPropagation();
              window.open(urlData.url, '_blank', 'noopener,noreferrer');
            }}
            title={`${urlData.type}: ${urlData.displayName}`}
          >
            <span className="text-sm">{icon}</span>
            <span className="font-medium">{urlData.displayName || urlData.url}</span>
            <ExternalLink className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
          </span>
        );
      })}
    </span>
  );
};
