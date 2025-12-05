/**
 * ToolExecutionContainer Component
 * 
 * Displays tool execution details in collapsible cards with input/output,
 * reasoning, and status indicators.
 */

import { useState } from 'react';
import { ChevronDown, ChevronRight, Wrench, CheckCircle, Clock, Brain, Download } from 'lucide-react';
import { JsonDisplay } from '../ui/JsonDisplay';
import { ToolExecution } from '../../store/chatStore';
import { ProgressIndicator } from './ProgressIndicator';
import { ExtractionProgress } from './ExtractionProgress';
import { CardsSummary } from './CardsSummary';

interface ToolExecutionContainerProps {
  toolExecutions: ToolExecution[];
  compact?: boolean;
  availableTools?: ToolInfo[];
  sessionId?: string;
}

interface ToolInfo {
  name: string;
  icon?: string;
  description?: string;
}

export const ToolExecutionContainer = ({
  toolExecutions,
  compact = false,
  availableTools = []
}: ToolExecutionContainerProps) => {
  if (!toolExecutions || toolExecutions.length === 0) {
    return null;
  }

  return (
    <div className="space-y-2">
      {toolExecutions.map((tool) => (
        <ToolExecutionCard
          key={tool.id}
          tool={tool}
          compact={compact}
          availableTools={availableTools}
        />
      ))}
    </div>
  );
};

interface ToolExecutionCardProps {
  tool: ToolExecution;
  compact: boolean;
  availableTools: ToolInfo[];
}

const ToolExecutionCard = ({ tool, compact, availableTools }: ToolExecutionCardProps) => {
  const [isExpanded, setIsExpanded] = useState(!compact);

  // Check if this is a code interpreter tool with file outputs
  const hasFileOutputs = () => {
    const codeInterpreterTools = ['code_interpreter', 'python_interpreter', 'execute_code'];
    return codeInterpreterTools.some(name => tool.toolName.toLowerCase().includes(name)) &&
           tool.toolResult;
  };

  // Download files as ZIP
  const handleDownloadFiles = async () => {
    try {
      // Parse tool result to extract file data
      const result = JSON.parse(tool.toolResult || '{}');
      
      // Check if result contains files
      if (!result.files || !Array.isArray(result.files)) {
        alert('No files found in tool output');
        return;
      }

      // For now, create a simple download of the result
      // In a real implementation, you'd use JSZip library
      const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${tool.toolName}_output.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error('Error downloading files:', e);
      alert('Failed to download files');
    }
  };

  // Get tool icon
  const getToolIcon = () => {
    const toolInfo = availableTools.find(t => t.name === tool.toolName);
    if (toolInfo?.icon) {
      return <span className="text-lg">{toolInfo.icon}</span>;
    }
    return <Wrench className="w-4 h-4" />;
  };

  // Get status badge
  const getStatusBadge = () => {
    if (tool.isComplete) {
      return (
        <div className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-green-500/20 text-green-400 text-xs">
          <CheckCircle className="w-3 h-3" />
          <span>Completed</span>
        </div>
      );
    }
    return (
      <div className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-400 text-xs animate-pulse">
        <Clock className="w-3 h-3" />
        <span>Running</span>
      </div>
    );
  };

  return (
    <div className="border border-slate-700 rounded-lg overflow-hidden bg-slate-800/50">
      {/* Header */}
      <div className="flex items-center">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex-1 flex items-center gap-3 px-4 py-3 hover:bg-slate-800 transition-colors"
        >
          <div className="flex items-center gap-2 flex-1">
            <div className="text-slate-400">
              {getToolIcon()}
            </div>
            <span className="font-medium text-slate-200">{tool.toolName}</span>
            {getStatusBadge()}
          </div>
          <div className="text-slate-400">
            {isExpanded ? (
              <ChevronDown className="w-4 h-4" />
            ) : (
              <ChevronRight className="w-4 h-4" />
            )}
          </div>
        </button>
        
        {/* Download button for file outputs */}
        {hasFileOutputs() && tool.isComplete && (
          <button
            onClick={handleDownloadFiles}
            className="px-3 py-3 hover:bg-slate-800 transition-colors text-slate-400 hover:text-blue-400"
            title="Download output files"
          >
            <Download className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Progress Indicator (shown when operation is in progress) */}
      {tool.progress && !tool.isComplete && (
        <div className="px-4 pt-3">
          {/* Use ExtractionProgress for extraction operations */}
          {tool.progress.operation_type.toLowerCase().includes('extract') ? (
            <ExtractionProgress 
              progress={tool.progress}
              url={tool.toolInput?.url as string | undefined}
            />
          ) : (
            <ProgressIndicator 
              progress={tool.progress}
              onCancel={(operationId) => {
                // TODO: Implement cancel operation
                console.log('Cancel operation:', operationId);
              }}
            />
          )}
        </div>
      )}

      {/* Extraction Summary (shown when extraction completes) */}
      {tool.extractionSummary && tool.isComplete && (
        <div className="px-4 pb-4">
          <CardsSummary
            cards={tool.extractionSummary.cards}
            sourceUrl={tool.extractionSummary.sourceUrl}
            operationType={tool.extractionSummary.operationType}
          />
        </div>
      )}

      {/* Expanded content */}
      {isExpanded && (
        <div className="px-4 pb-4 space-y-3">
          {/* Tool Input */}
          {tool.toolInput && Object.keys(tool.toolInput).length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span className="text-sm font-medium text-slate-300">Input</span>
              </div>
              <JsonDisplay
                data={tool.toolInput}
                maxLines={10}
                collapsible={true}
                defaultExpanded={false}
              />
            </div>
          )}

          {/* Reasoning */}
          {tool.reasoningText && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Brain className="w-4 h-4 text-purple-400" />
                <span className="text-sm font-medium text-slate-300">Reasoning</span>
              </div>
              <div className="bg-slate-900 rounded-lg p-3">
                <p className="text-sm text-slate-300">{tool.reasoningText}</p>
              </div>
            </div>
          )}

          {/* Tool Result */}
          {tool.toolResult && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span className="text-sm font-medium text-slate-300">Result</span>
              </div>
              {(() => {
                try {
                  const parsed = JSON.parse(tool.toolResult);
                  return (
                    <JsonDisplay
                      data={parsed}
                      maxLines={15}
                      collapsible={true}
                      defaultExpanded={true}
                    />
                  );
                } catch (e) {
                  return (
                    <div className="bg-slate-900 rounded-lg p-3">
                      <pre className="text-sm text-slate-300 whitespace-pre-wrap">
                        {tool.toolResult}
                      </pre>
                    </div>
                  );
                }
              })()}
            </div>
          )}

          {/* Images */}
          {tool.images && tool.images.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span className="text-sm font-medium text-slate-300">Generated Images</span>
              </div>
              <div className="grid grid-cols-2 gap-2">
                {tool.images.map((image, idx) => (
                  <div key={idx} className="relative group">
                    <img
                      src={image.url}
                      alt={image.alt || `Generated image ${idx + 1}`}
                      className="rounded border border-slate-600 w-full cursor-pointer hover:border-blue-500 transition-colors"
                      onClick={() => {
                        // TODO: Implement image modal/lightbox
                        window.open(image.url, '_blank');
                      }}
                    />
                    {image.format && (
                      <div className="absolute top-2 right-2 px-2 py-1 bg-slate-900/80 rounded text-xs text-slate-300 opacity-0 group-hover:opacity-100 transition-opacity">
                        {image.format}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
