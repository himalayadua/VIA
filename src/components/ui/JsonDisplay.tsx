/**
 * JsonDisplay Component
 * 
 * Displays JSON data with syntax highlighting and collapsible sections.
 */

import { useState } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';

interface JsonDisplayProps {
  data: any;
  maxLines?: number;
  collapsible?: boolean;
  defaultExpanded?: boolean;
}

export const JsonDisplay = ({
  data,
  maxLines = 20,
  collapsible = true,
  defaultExpanded = true
}: JsonDisplayProps) => {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  const [showAll, setShowAll] = useState(false);

  // Format JSON with syntax highlighting
  const formatJson = (obj: any): string => {
    try {
      return JSON.stringify(obj, null, 2);
    } catch (e) {
      return String(obj);
    }
  };

  const jsonString = formatJson(data);
  const lines = jsonString.split('\n');
  const shouldTruncate = lines.length > maxLines && !showAll;
  const displayLines = shouldTruncate ? lines.slice(0, maxLines) : lines;

  // Syntax highlighting for JSON
  const highlightJson = (json: string): JSX.Element[] => {
    return json.split('\n').map((line, i) => {
      // Colorize different parts of JSON
      let coloredLine = line
        // Keys
        .replace(/"([^"]+)":/g, '<span class="text-blue-400">"$1"</span>:')
        // String values
        .replace(/: "([^"]*)"/g, ': <span class="text-green-400">"$1"</span>')
        // Numbers
        .replace(/: (\d+\.?\d*)/g, ': <span class="text-purple-400">$1</span>')
        // Booleans
        .replace(/: (true|false)/g, ': <span class="text-yellow-400">$1</span>')
        // Null
        .replace(/: (null)/g, ': <span class="text-slate-500">$1</span>');

      return (
        <div
          key={i}
          className="leading-relaxed"
          dangerouslySetInnerHTML={{ __html: coloredLine }}
        />
      );
    });
  };

  if (!collapsible) {
    return (
      <div className="bg-slate-900 rounded-lg p-3 overflow-x-auto">
        <pre className="text-xs font-mono text-slate-200">
          {highlightJson(displayLines.join('\n'))}
        </pre>
        {shouldTruncate && (
          <button
            onClick={() => setShowAll(true)}
            className="mt-2 text-xs text-blue-400 hover:text-blue-300"
          >
            Show all {lines.length} lines
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="border border-slate-700 rounded-lg overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center gap-2 px-3 py-2 bg-slate-800 hover:bg-slate-750 transition-colors"
      >
        {isExpanded ? (
          <ChevronDown className="w-4 h-4 text-slate-400" />
        ) : (
          <ChevronRight className="w-4 h-4 text-slate-400" />
        )}
        <span className="text-sm font-medium text-slate-300">
          {isExpanded ? 'Hide' : 'Show'} JSON
        </span>
        <span className="text-xs text-slate-500 ml-auto">
          {lines.length} lines
        </span>
      </button>

      {isExpanded && (
        <div className="bg-slate-900 p-3 overflow-x-auto">
          <pre className="text-xs font-mono text-slate-200">
            {highlightJson(displayLines.join('\n'))}
          </pre>
          {shouldTruncate && (
            <button
              onClick={() => setShowAll(true)}
              className="mt-2 text-xs text-blue-400 hover:text-blue-300"
            >
              Show all {lines.length} lines
            </button>
          )}
        </div>
      )}
    </div>
  );
};
