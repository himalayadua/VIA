/**
 * Markdown Component
 * 
 * Renders markdown content with GitHub-flavored markdown support,
 * syntax highlighting, and custom parsing for chart/image references.
 */

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/github-dark.css';
import { Copy, Check } from 'lucide-react';
import { useState } from 'react';
import { ChartRenderer } from './ChartRenderer';
import { ImageRenderer } from './ImageRenderer';
import { CardReference } from '../chat/CardReference';
import { parseTextWithCardReferences } from '../../utils/cardReferenceUtils';

interface MarkdownProps {
  children: string;
  size?: 'sm' | 'base' | 'lg' | 'xl';
  preserveLineBreaks?: boolean;
  sessionId?: string;
  toolUseId?: string;
}

// Code block component with copy button
const CodeBlock = ({ children, className }: { children: string; className?: string }) => {
  const [copied, setCopied] = useState(false);
  
  const handleCopy = () => {
    navigator.clipboard.writeText(children);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative group">
      <button
        onClick={handleCopy}
        className="absolute right-2 top-2 p-1.5 rounded bg-slate-700 hover:bg-slate-600 opacity-0 group-hover:opacity-100 transition-opacity"
        title="Copy code"
      >
        {copied ? (
          <Check className="w-4 h-4 text-green-400" />
        ) : (
          <Copy className="w-4 h-4 text-slate-300" />
        )}
      </button>
      <pre className={`${className} p-4 rounded-lg overflow-x-auto bg-slate-900`}>
        <code className={className}>{children}</code>
      </pre>
    </div>
  );
};

export const Markdown = ({
  children,
  size = 'base',
  preserveLineBreaks = false
}: MarkdownProps) => {
  // Process content to handle special patterns
  const processedContent = children
    // Preserve line breaks if needed
    .replace(/\n/g, preserveLineBreaks ? '  \n' : '\n');

  const sizeClasses = {
    sm: 'text-sm',
    base: 'text-base',
    lg: 'text-lg',
    xl: 'text-xl'
  };

  return (
    <div className={`markdown-content ${sizeClasses[size]}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={{
          // Custom code block rendering
          code({ className, children, ...props }: any) {
            const content = String(children).replace(/\n$/, '');
            const isInline = !className;
            
            // Check for chart code block
            if (!isInline && className?.includes('language-chart')) {
              try {
                const chartData = JSON.parse(content);
                return <ChartRenderer data={chartData} />;
              } catch (e) {
                return <CodeBlock className={className}>{content}</CodeBlock>;
              }
            }

            // Inline code
            if (isInline) {
              return (
                <code
                  className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-200 font-mono text-sm"
                  {...props}
                >
                  {children}
                </code>
              );
            }

            // Block code
            return <CodeBlock className={className}>{content}</CodeBlock>;
          },

          // Custom paragraph rendering to handle chart/image/card references
          p({ children }) {
            const text = String(children);
            
            // Parse [CHART:chart_id] pattern
            const chartMatch = text.match(/\[CHART:([^\]]+)\]/);
            if (chartMatch) {
              const chartId = chartMatch[1];
              // In a real implementation, fetch chart data from backend
              return <ChartRenderer chartId={chartId} data={{ type: 'placeholder', title: `Chart ${chartId}` }} />;
            }

            // Parse [IMAGE:image_id:alt_text] pattern
            const imageMatch = text.match(/\[IMAGE:([^:]+):([^\]]+)\]/);
            if (imageMatch) {
              const [, imageId, altText] = imageMatch;
              return <ImageRenderer imageId={imageId} alt={altText} />;
            }

            // Parse card references
            const segments = parseTextWithCardReferences(text);
            if (segments.length > 1 || segments[0]?.type === 'card') {
              return (
                <p className="mb-2">
                  {segments.map((segment, index) => {
                    if (segment.type === 'text') {
                      return <span key={index}>{segment.content as string}</span>;
                    } else {
                      const ref = segment.content as any;
                      return (
                        <CardReference
                          key={index}
                          cardId={ref.cardId}
                          displayText={ref.displayText}
                        />
                      );
                    }
                  })}
                </p>
              );
            }

            return <p className="mb-2">{children}</p>;
          },

          // Style headings
          h1: ({ children }) => (
            <h1 className="text-2xl font-bold mb-3 mt-4">{children}</h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-xl font-bold mb-2 mt-3">{children}</h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-lg font-bold mb-2 mt-2">{children}</h3>
          ),

          // Style lists
          ul: ({ children }) => (
            <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>
          ),
          ol: ({ children }) => (
            <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>
          ),
          li: ({ children }) => (
            <li className="ml-4">{children}</li>
          ),

          // Style links
          a: ({ href, children }) => (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-400 hover:text-blue-300 underline"
            >
              {children}
            </a>
          ),

          // Style blockquotes
          blockquote: ({ children }) => (
            <blockquote className="border-l-4 border-slate-600 pl-4 italic my-2 text-slate-300">
              {children}
            </blockquote>
          ),

          // Style tables
          table: ({ children }) => (
            <div className="overflow-x-auto my-2">
              <table className="min-w-full border border-slate-700 rounded-lg">
                {children}
              </table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className="bg-slate-800">{children}</thead>
          ),
          tbody: ({ children }) => (
            <tbody className="divide-y divide-slate-700">{children}</tbody>
          ),
          tr: ({ children }) => (
            <tr className="hover:bg-slate-800/50">{children}</tr>
          ),
          th: ({ children }) => (
            <th className="px-4 py-2 text-left font-semibold">{children}</th>
          ),
          td: ({ children }) => (
            <td className="px-4 py-2">{children}</td>
          ),

          // Style horizontal rules
          hr: () => (
            <hr className="my-4 border-slate-700" />
          ),

          // Style strong/bold
          strong: ({ children }) => (
            <strong className="font-bold">{children}</strong>
          ),

          // Style emphasis/italic
          em: ({ children }) => (
            <em className="italic">{children}</em>
          ),
        }}
      >
        {processedContent}
      </ReactMarkdown>
    </div>
  );
};
