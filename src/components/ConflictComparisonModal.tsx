/**
 * ConflictComparisonModal Component
 * 
 * Displays side-by-side comparison of conflicting cards with merge functionality
 */

import { X, AlertTriangle, ArrowRight, Merge } from 'lucide-react';
import { useState } from 'react';

interface ConflictCard {
  id: string;
  title: string;
  content: string;
  tags: string[];
  sourceUrl?: string;
  sourceType?: string;
}

interface ConflictComparisonModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentCard: ConflictCard;
  conflictingCards: ConflictCard[];
  conflictType?: 'duplicate' | 'contradiction' | 'similar';
  similarity?: number;
  onMerge?: (cardId1: string, cardId2: string) => void;
}

export const ConflictComparisonModal = ({
  isOpen,
  onClose,
  currentCard,
  conflictingCards,
  conflictType = 'contradiction',
  similarity = 0.7,
  onMerge
}: ConflictComparisonModalProps) => {
  const [selectedConflictIndex, setSelectedConflictIndex] = useState(0);
  const [showMergePreview, setShowMergePreview] = useState(false);

  if (!isOpen || conflictingCards.length === 0) return null;

  const selectedConflict = conflictingCards[selectedConflictIndex];

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const getConflictTypeInfo = () => {
    switch (conflictType) {
      case 'duplicate':
        return {
          label: 'Duplicate Content',
          color: 'text-blue-400',
          bgColor: 'bg-blue-900/20',
          borderColor: 'border-blue-700/50',
          description: 'These cards contain very similar information and should likely be merged.'
        };
      case 'contradiction':
        return {
          label: 'Conflicting Information',
          color: 'text-red-400',
          bgColor: 'bg-red-900/20',
          borderColor: 'border-red-700/50',
          description: 'These cards contain contradictory information about the same topic.'
        };
      case 'similar':
        return {
          label: 'Similar Content',
          color: 'text-yellow-400',
          bgColor: 'bg-yellow-900/20',
          borderColor: 'border-yellow-700/50',
          description: 'These cards have overlapping content that might benefit from merging.'
        };
    }
  };

  const conflictInfo = getConflictTypeInfo();

  // Simple diff highlighting (highlights words that differ)
  const highlightDifferences = (text1: string, text2: string) => {
    const words1 = text1.toLowerCase().split(/\s+/);
    const words2 = text2.toLowerCase().split(/\s+/);
    const words2Set = new Set(words2);
    
    return text1.split(/\s+/).map((word, i) => {
      const isUnique = !words2Set.has(word.toLowerCase());
      return (
        <span
          key={i}
          className={isUnique ? 'bg-yellow-500/30 px-0.5 rounded' : ''}
        >
          {word}{' '}
        </span>
      );
    });
  };

  const handleMerge = () => {
    if (onMerge) {
      onMerge(currentCard.id, selectedConflict.id);
      onClose();
    }
  };

  return (
    <div
      className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4"
      onClick={handleBackdropClick}
    >
      <div className="bg-slate-900 border border-slate-700 rounded-lg shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-700">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-6 h-6 text-yellow-400" />
            <div>
              <h2 className="text-xl font-semibold text-slate-100">Conflict Detection</h2>
              <p className="text-sm text-slate-400 mt-1">
                {conflictingCards.length} conflicting card{conflictingCards.length !== 1 ? 's' : ''} found
              </p>
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

        {/* Conflict Type Banner */}
        <div className={`${conflictInfo.bgColor} border-b ${conflictInfo.borderColor} p-4`}>
          <div className="flex items-start gap-3">
            <AlertTriangle className={`w-5 h-5 ${conflictInfo.color} flex-shrink-0 mt-0.5`} />
            <div className="flex-1">
              <h3 className={`text-sm font-semibold ${conflictInfo.color} mb-1`}>
                {conflictInfo.label} ({Math.round(similarity * 100)}% similar)
              </h3>
              <p className="text-sm text-slate-300">{conflictInfo.description}</p>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Conflict Selector (if multiple conflicts) */}
          {conflictingCards.length > 1 && (
            <div className="mb-6">
              <label className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-2 block">
                Select Conflict to Compare
              </label>
              <div className="flex gap-2 flex-wrap">
                {conflictingCards.map((card, index) => (
                  <button
                    key={card.id}
                    onClick={() => setSelectedConflictIndex(index)}
                    className={`px-3 py-2 rounded-lg text-sm transition-colors ${
                      selectedConflictIndex === index
                        ? 'bg-blue-600 text-white'
                        : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                    }`}
                  >
                    {card.title || `Card ${index + 1}`}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Side-by-Side Comparison */}
          <div className="grid grid-cols-2 gap-6">
            {/* Current Card */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-slate-100">Current Card</h3>
                <span className="text-xs px-2 py-1 bg-blue-500/20 text-blue-300 rounded">
                  This Card
                </span>
              </div>
              
              <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4 space-y-3">
                <div>
                  <label className="text-xs font-medium text-slate-400 uppercase tracking-wide">
                    Title
                  </label>
                  <p className="text-sm text-slate-200 mt-1 font-medium">
                    {currentCard.title}
                  </p>
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-400 uppercase tracking-wide">
                    Content
                  </label>
                  <div className="text-sm text-slate-200 mt-1 leading-relaxed">
                    {highlightDifferences(currentCard.content, selectedConflict.content)}
                  </div>
                </div>

                {currentCard.tags.length > 0 && (
                  <div>
                    <label className="text-xs font-medium text-slate-400 uppercase tracking-wide">
                      Tags
                    </label>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {currentCard.tags.map((tag, i) => (
                        <span
                          key={i}
                          className="px-2 py-0.5 bg-slate-700 text-slate-300 rounded text-xs"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Conflicting Card */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-slate-100">Conflicting Card</h3>
                <span className="text-xs px-2 py-1 bg-yellow-500/20 text-yellow-300 rounded">
                  Conflict
                </span>
              </div>
              
              <div className="bg-slate-800/50 border border-yellow-700/50 rounded-lg p-4 space-y-3">
                <div>
                  <label className="text-xs font-medium text-slate-400 uppercase tracking-wide">
                    Title
                  </label>
                  <p className="text-sm text-slate-200 mt-1 font-medium">
                    {selectedConflict.title}
                  </p>
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-400 uppercase tracking-wide">
                    Content
                  </label>
                  <div className="text-sm text-slate-200 mt-1 leading-relaxed">
                    {highlightDifferences(selectedConflict.content, currentCard.content)}
                  </div>
                </div>

                {selectedConflict.tags.length > 0 && (
                  <div>
                    <label className="text-xs font-medium text-slate-400 uppercase tracking-wide">
                      Tags
                    </label>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {selectedConflict.tags.map((tag, i) => (
                        <span
                          key={i}
                          className="px-2 py-0.5 bg-slate-700 text-slate-300 rounded text-xs"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* AI Suggestions */}
          <div className="mt-6 bg-purple-900/20 border border-purple-700/50 rounded-lg p-4">
            <h4 className="text-sm font-semibold text-purple-300 mb-2">AI Suggestion</h4>
            <p className="text-sm text-slate-300">
              {conflictType === 'duplicate' && 
                'These cards appear to be duplicates. Consider merging them to maintain a clean canvas.'}
              {conflictType === 'contradiction' && 
                'These cards contain contradictory information. Review both carefully and merge or keep separate based on which is more accurate.'}
              {conflictType === 'similar' && 
                'These cards have overlapping content. Merging them would consolidate related information in one place.'}
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between gap-3 p-6 border-t border-slate-700">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg transition-colors"
          >
            Keep Separate
          </button>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowMergePreview(!showMergePreview)}
              className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-lg transition-colors flex items-center gap-2"
            >
              <ArrowRight className="w-4 h-4" />
              {showMergePreview ? 'Hide' : 'Preview'} Merge
            </button>
            {onMerge && (
              <button
                onClick={handleMerge}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
              >
                <Merge className="w-4 h-4" />
                Merge Cards
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
