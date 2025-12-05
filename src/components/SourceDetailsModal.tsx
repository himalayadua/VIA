/**
 * SourceDetailsModal Component
 * 
 * Displays detailed source attribution information for cards
 */

import { X, ExternalLink, Calendar, Wrench, AlertTriangle } from 'lucide-react';
import { 
  getSourceIcon, 
  getSourceDisplayName, 
  formatExtractionDate,
  type SourceType,
  type SourceInfo 
} from '../utils/sourceAttribution';

interface SourceDetailsModalProps {
  isOpen: boolean;
  onClose: () => void;
  cardTitle: string;
  sourceType?: SourceType;
  sourceUrl?: string;
  extractedAt?: string;
  extractionMethod?: string;
  sources?: SourceInfo[];
  hasConflict?: boolean;
  conflictDetails?: string;
}

export const SourceDetailsModal = ({
  isOpen,
  onClose,
  cardTitle,
  sourceType,
  sourceUrl,
  extractedAt,
  extractionMethod,
  sources = [],
  hasConflict,
  conflictDetails
}: SourceDetailsModalProps) => {
  if (!isOpen) return null;

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const handleOpenSource = (url: string) => {
    window.open(url, '_blank', 'noopener,noreferrer');
  };

  // Check if this is a merged card (multiple sources)
  const isMerged = sources.length > 1;

  return (
    <div
      className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4"
      onClick={handleBackdropClick}
    >
      <div className="bg-slate-900 border border-slate-700 rounded-lg shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-700">
          <div className="flex items-center gap-3">
            <div className="text-3xl">{sourceType && getSourceIcon(sourceType)}</div>
            <div>
              <h2 className="text-xl font-semibold text-slate-100">Source Details</h2>
              <p className="text-sm text-slate-400 mt-1">{cardTitle}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-800 rounded-lg transition-colors text-slate-400 hover:text-slate-200"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Conflict Warning */}
          {hasConflict && (
            <div className="bg-yellow-900/20 border border-yellow-700/50 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="text-sm font-semibold text-yellow-300 mb-1">
                    Conflicting Information Detected
                  </h3>
                  <p className="text-sm text-yellow-200/80">
                    {conflictDetails || 'This card contains information that conflicts with other cards on your canvas.'}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Single Source */}
          {!isMerged && sourceType && (
            <div className="space-y-4">
              {/* Source Type */}
              <div>
                <label className="text-xs font-medium text-slate-400 uppercase tracking-wide">
                  Source Type
                </label>
                <p className="text-sm text-slate-200 mt-1">
                  {getSourceDisplayName(sourceType)}
                </p>
              </div>

              {/* Source URL */}
              {sourceUrl && (
                <div>
                  <label className="text-xs font-medium text-slate-400 uppercase tracking-wide">
                    Source URL
                  </label>
                  <div className="mt-1 flex items-center gap-2">
                    <p className="text-sm text-blue-400 flex-1 break-all">
                      {sourceUrl}
                    </p>
                    <button
                      onClick={() => handleOpenSource(sourceUrl)}
                      className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm transition-colors flex-shrink-0"
                    >
                      <ExternalLink className="w-4 h-4" />
                      Open
                    </button>
                  </div>
                </div>
              )}

              {/* Extraction Date */}
              {extractedAt && (
                <div>
                  <label className="text-xs font-medium text-slate-400 uppercase tracking-wide">
                    Extracted
                  </label>
                  <div className="flex items-center gap-2 mt-1">
                    <Calendar className="w-4 h-4 text-slate-400" />
                    <p className="text-sm text-slate-200">
                      {formatExtractionDate(extractedAt)} ({new Date(extractedAt).toLocaleString()})
                    </p>
                  </div>
                </div>
              )}

              {/* Extraction Method */}
              {extractionMethod && (
                <div>
                  <label className="text-xs font-medium text-slate-400 uppercase tracking-wide">
                    Extraction Method
                  </label>
                  <div className="flex items-center gap-2 mt-1">
                    <Wrench className="w-4 h-4 text-slate-400" />
                    <p className="text-sm text-slate-200">{extractionMethod}</p>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Multiple Sources (Merged Card) */}
          {isMerged && (
            <div className="space-y-4">
              <div>
                <label className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-3 block">
                  Multiple Sources ({sources.length})
                </label>
                <p className="text-sm text-slate-300 mb-4">
                  This card was created by merging information from multiple sources.
                </p>
                <div className="space-y-3">
                  {sources.map((source, index) => (
                    <div
                      key={index}
                      className="bg-slate-800/50 border border-slate-700 rounded-lg p-4 space-y-2"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <span className="text-lg">{source.type && getSourceIcon(source.type as SourceType)}</span>
                            <span className="text-sm font-medium text-slate-200">
                              Source {index + 1}
                            </span>
                            {source.contribution && (
                              <span className="text-xs px-2 py-0.5 bg-blue-500/20 text-blue-300 rounded">
                                {Math.round(source.contribution * 100)}% contribution
                              </span>
                            )}
                          </div>
                          {source.url && (
                            <p className="text-sm text-blue-400 break-all">{source.url}</p>
                          )}
                          {source.extracted_at && (
                            <p className="text-xs text-slate-400 mt-1">
                              Extracted {formatExtractionDate(source.extracted_at)}
                            </p>
                          )}
                        </div>
                        {source.url && (
                          <button
                            onClick={() => handleOpenSource(source.url!)}
                            className="flex items-center gap-1 px-2 py-1 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded text-xs transition-colors flex-shrink-0"
                          >
                            <ExternalLink className="w-3 h-3" />
                            Open
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-6 border-t border-slate-700">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg transition-colors"
          >
            Close
          </button>
          {sourceUrl && !isMerged && (
            <button
              onClick={() => handleOpenSource(sourceUrl)}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
            >
              <ExternalLink className="w-4 h-4" />
              Open Source
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
