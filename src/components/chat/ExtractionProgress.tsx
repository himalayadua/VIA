/**
 * ExtractionProgress Component
 * 
 * Displays real-time progress for URL content extraction operations
 */

import { Loader2, FileText, Github, Youtube, FileType } from 'lucide-react';
import { OperationProgress } from '../../store/chatStore';

interface ExtractionProgressProps {
  progress: OperationProgress;
  url?: string;
}

export const ExtractionProgress = ({ progress, url }: ExtractionProgressProps) => {
  // Get icon based on operation type
  const getIcon = () => {
    const type = progress.operation_type.toLowerCase();
    if (type.includes('github')) return <Github className="w-4 h-4" />;
    if (type.includes('youtube') || type.includes('video')) return <Youtube className="w-4 h-4" />;
    if (type.includes('pdf')) return <FileType className="w-4 h-4" />;
    if (type.includes('doc')) return <FileText className="w-4 h-4" />;
    return <FileText className="w-4 h-4" />;
  };

  // Get color based on progress
  const getProgressColor = () => {
    if (progress.progress < 0.33) return 'bg-blue-500';
    if (progress.progress < 0.66) return 'bg-purple-500';
    return 'bg-green-500';
  };

  const percentage = Math.round(progress.progress * 100);

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 space-y-3">
      {/* Header */}
      <div className="flex items-center gap-2">
        <div className="text-blue-400">
          {getIcon()}
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />
            <span className="text-sm font-medium text-slate-200">
              Extracting Content
            </span>
          </div>
          {url && (
            <p className="text-xs text-slate-400 mt-1 truncate">
              {url}
            </p>
          )}
        </div>
        <span className="text-sm font-semibold text-slate-300">
          {percentage}%
        </span>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-slate-700 rounded-full h-2 overflow-hidden">
        <div
          className={`h-full ${getProgressColor()} transition-all duration-300 ease-out`}
          style={{ width: `${percentage}%` }}
        />
      </div>

      {/* Status Message */}
      <div className="space-y-1">
        <p className="text-sm text-slate-300">
          {progress.message}
        </p>
        
        {/* Additional Info */}
        <div className="flex items-center gap-4 text-xs text-slate-400">
          {progress.cards_created > 0 && (
            <span>
              📝 {progress.cards_created} card{progress.cards_created !== 1 ? 's' : ''} created
            </span>
          )}
          {progress.estimated_time && progress.estimated_time > 0 && (
            <span>
              ⏱️ ~{Math.ceil(progress.estimated_time)}s remaining
            </span>
          )}
        </div>
      </div>

      {/* Current Step */}
      {progress.step && (
        <div className="text-xs text-slate-500 italic">
          Step: {progress.step}
        </div>
      )}
    </div>
  );
};
