/**
 * ProgressIndicator Component
 * 
 * Displays real-time progress for long-running operations with:
 * - Progress bar with percentage
 * - Current step and message
 * - Cards created count
 * - Estimated time remaining
 * - Cancel button (if cancellable)
 */

import { Clock, X } from 'lucide-react';
import { OperationProgress } from '../../store/chatStore';

interface ProgressIndicatorProps {
  progress: OperationProgress;
  onCancel?: (operationId: string) => void;
}

export const ProgressIndicator = ({ progress, onCancel }: ProgressIndicatorProps) => {
  const percentage = Math.round(progress.progress * 100);
  
  // Format estimated time
  const formatTime = (seconds: number): string => {
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  return (
    <div className="border border-blue-500/30 rounded-lg p-3 bg-blue-500/10">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2 flex-1">
          <Clock className="w-4 h-4 text-blue-400 animate-spin" />
          <span className="text-sm font-medium text-blue-300 capitalize">
            {progress.step.replace(/_/g, ' ')}
          </span>
          <span className="text-xs text-slate-400">
            {percentage}%
          </span>
        </div>
        
        {progress.can_cancel && onCancel && (
          <button
            onClick={() => onCancel(progress.operation_id)}
            className="p-1 hover:bg-red-500/20 rounded transition-colors text-red-400 hover:text-red-300"
            title="Cancel operation"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
      
      {/* Progress Bar */}
      <div className="w-full bg-slate-700 rounded-full h-2 mb-2 overflow-hidden">
        <div
          className="bg-blue-500 h-2 rounded-full transition-all duration-300 ease-out"
          style={{ width: `${percentage}%` }}
        />
      </div>
      
      {/* Message */}
      {progress.message && (
        <div className="text-xs text-slate-300 mb-2">
          {progress.message}
        </div>
      )}
      
      {/* Stats */}
      <div className="flex items-center gap-4 text-xs text-slate-500">
        {progress.cards_created > 0 && (
          <span className="flex items-center gap-1">
            <span className="text-blue-400">{progress.cards_created}</span>
            <span>cards created</span>
          </span>
        )}
        {progress.estimated_time !== undefined && progress.estimated_time > 0 && (
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            <span>~{formatTime(progress.estimated_time)} remaining</span>
          </span>
        )}
      </div>
    </div>
  );
};
