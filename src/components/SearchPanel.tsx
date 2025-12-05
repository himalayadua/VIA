import { useEffect, useRef, useState } from 'react';
import { 
  Search, 
  X, 
  Filter,
  FileText,
  CheckSquare,
  Video,
  Link as LinkIcon,
  Clock,
  Tag,
  Network
} from 'lucide-react';
import { useSearchStore } from '../store/searchStore';
import { useCanvasStore } from '../store/canvasStore';
import { CardType, CARD_THEMES, getCardTypeDisplayName } from '../types/cardTypes';
import { useReactFlow } from 'reactflow';

export const SearchPanel = () => {
  const {
    isOpen,
    searchQuery,
    searchMode,
    searchResults,
    selectedResultIndex,
    selectedCardTypes,
    selectedTags,
    connectionLevel,
    closeSearch,
    setSearchQuery,
    setSearchMode,
    performSearch,
    clearSearch,
    selectResult,
    toggleCardTypeFilter,
    toggleTagFilter,
    setConnectionLevel,
    clearFilters
  } = useSearchStore();

  const { nodes, edges } = useCanvasStore();
  const { setCenter } = useReactFlow();
  const inputRef = useRef<HTMLInputElement>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [availableTags, setAvailableTags] = useState<string[]>([]);

  // Focus input when panel opens
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  // Extract available tags from nodes
  useEffect(() => {
    const tags = new Set<string>();
    nodes.forEach(node => {
      if (node.data.tags && Array.isArray(node.data.tags)) {
        node.data.tags.forEach((tag: string) => tags.add(tag));
      }
    });
    setAvailableTags(Array.from(tags).sort());
  }, [nodes]);

  // Perform search when query or filters change
  useEffect(() => {
    if (searchQuery.trim() || searchMode === 'relationship') {
      const timeoutId = setTimeout(() => {
        performSearch(nodes, edges);
      }, 300); // Debounce search

      return () => clearTimeout(timeoutId);
    } else {
      clearSearch();
    }
  }, [searchQuery, searchMode, selectedCardTypes, selectedTags, connectionLevel, nodes, edges, performSearch, clearSearch]);

  const handleResultClick = (index: number) => {
    selectResult(index);
    const result = searchResults[index];
    
    // Pan and zoom to the node
    if (result.node) {
      setCenter(
        result.node.position.x + (result.node.width || 300) / 2,
        result.node.position.y + (result.node.height || 200) / 2,
        { zoom: 1.2, duration: 500 }
      );
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      closeSearch();
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      const nextIndex = Math.min(selectedResultIndex + 1, searchResults.length - 1);
      handleResultClick(nextIndex);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      const prevIndex = Math.max(selectedResultIndex - 1, 0);
      handleResultClick(prevIndex);
    } else if (e.key === 'Enter' && selectedResultIndex >= 0) {
      e.preventDefault();
      handleResultClick(selectedResultIndex);
    }
  };

  if (!isOpen) return null;

  const cardTypeIcons = {
    [CardType.RICH_TEXT]: FileText,
    [CardType.TODO]: CheckSquare,
    [CardType.VIDEO]: Video,
    [CardType.LINK]: LinkIcon,
    [CardType.REMINDER]: Clock
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-start justify-center pt-20">
      <div className="bg-slate-800 rounded-lg shadow-2xl w-full max-w-2xl max-h-[80vh] flex flex-col border border-slate-700">
        {/* Header */}
        <div className="p-4 border-b border-slate-700">
          <div className="flex items-center gap-2 mb-3">
            <Search className="w-5 h-5 text-slate-400" />
            <input
              ref={inputRef}
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={
                searchMode === 'keyword' ? 'Search nodes...' :
                searchMode === 'similarity' ? 'Find similar content...' :
                'Select a node to find connections...'
              }
              className="flex-1 bg-transparent text-slate-100 placeholder-slate-500 outline-none text-lg"
            />
            <button
              onClick={closeSearch}
              className="p-1 hover:bg-slate-700 rounded transition-colors"
            >
              <X className="w-5 h-5 text-slate-400" />
            </button>
          </div>

          {/* Mode Toggle */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setSearchMode('keyword')}
              className={`px-3 py-1.5 rounded text-sm transition-colors ${
                searchMode === 'keyword'
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              Keyword
            </button>
            <button
              onClick={() => setSearchMode('similarity')}
              className={`px-3 py-1.5 rounded text-sm transition-colors ${
                searchMode === 'similarity'
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              Similarity
            </button>
            <button
              onClick={() => setSearchMode('relationship')}
              className={`px-3 py-1.5 rounded text-sm transition-colors ${
                searchMode === 'relationship'
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              Connections
            </button>

            <div className="flex-1" />

            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`p-1.5 rounded transition-colors ${
                showFilters ? 'bg-slate-700' : 'hover:bg-slate-700'
              }`}
              title="Filters"
            >
              <Filter className="w-4 h-4 text-slate-400" />
            </button>
          </div>

          {/* Filters */}
          {showFilters && (
            <div className="mt-3 p-3 bg-slate-900/50 rounded space-y-3">
              {/* Card Type Filters */}
              <div>
                <label className="text-xs text-slate-400 mb-2 block">Card Types</label>
                <div className="flex flex-wrap gap-2">
                  {Object.values(CardType).map(type => {
                    const Icon = cardTypeIcons[type];
                    const isSelected = selectedCardTypes.includes(type);
                    return (
                      <button
                        key={type}
                        onClick={() => toggleCardTypeFilter(type)}
                        className={`px-2 py-1 rounded text-xs flex items-center gap-1 transition-colors ${
                          isSelected
                            ? 'bg-blue-600 text-white'
                            : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                        }`}
                      >
                        <Icon className="w-3 h-3" />
                        {getCardTypeDisplayName(type)}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Tag Filters */}
              {availableTags.length > 0 && (
                <div>
                  <label className="text-xs text-slate-400 mb-2 block">Tags</label>
                  <div className="flex flex-wrap gap-2 max-h-24 overflow-y-auto">
                    {availableTags.map(tag => {
                      const isSelected = selectedTags.includes(tag);
                      return (
                        <button
                          key={tag}
                          onClick={() => toggleTagFilter(tag)}
                          className={`px-2 py-1 rounded text-xs flex items-center gap-1 transition-colors ${
                            isSelected
                              ? 'bg-blue-600 text-white'
                              : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                          }`}
                        >
                          <Tag className="w-3 h-3" />
                          {tag}
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Connection Level (for relationship search) */}
              {searchMode === 'relationship' && (
                <div>
                  <label className="text-xs text-slate-400 mb-2 block">
                    Connection Degree: {connectionLevel}
                  </label>
                  <input
                    type="range"
                    min="1"
                    max="5"
                    value={connectionLevel}
                    onChange={(e) => setConnectionLevel(parseInt(e.target.value))}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-slate-500 mt-1">
                    <span>Direct</span>
                    <span>5 degrees</span>
                  </div>
                </div>
              )}

              <button
                onClick={clearFilters}
                className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
              >
                Clear Filters
              </button>
            </div>
          )}
        </div>

        {/* Results */}
        <div className="flex-1 overflow-y-auto">
          {searchResults.length === 0 ? (
            <div className="p-8 text-center text-slate-500">
              {searchQuery.trim() || searchMode === 'relationship' ? (
                <>
                  <Search className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p>No results found</p>
                </>
              ) : (
                <>
                  <Search className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p>Start typing to search</p>
                  <p className="text-sm mt-2">
                    Use <kbd className="px-2 py-1 bg-slate-700 rounded text-xs">↑</kbd>{' '}
                    <kbd className="px-2 py-1 bg-slate-700 rounded text-xs">↓</kbd> to navigate
                  </p>
                </>
              )}
            </div>
          ) : (
            <div className="divide-y divide-slate-700">
              {searchResults.map((result, index) => {
                const cardType = result.node.data.cardType as CardType;
                const Icon = cardTypeIcons[cardType] || FileText;
                const theme = CARD_THEMES[cardType];
                const isSelected = index === selectedResultIndex;

                return (
                  <button
                    key={result.nodeId}
                    onClick={() => handleResultClick(index)}
                    className={`w-full p-4 text-left hover:bg-slate-700/50 transition-colors ${
                      isSelected ? 'bg-slate-700/70' : ''
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className={`p-2 rounded ${theme.background} flex-shrink-0`}>
                        <Icon className="w-4 h-4 text-white" />
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="text-slate-100 font-medium truncate">
                            {result.node.data.title || 'Untitled'}
                          </h3>
                          <span className="text-xs text-slate-500 flex-shrink-0">
                            {Math.round(result.score)}% match
                          </span>
                        </div>
                        
                        <p className="text-sm text-slate-400 line-clamp-2">
                          {result.snippet}
                        </p>

                        {result.connectionPath && result.connectionPath.length > 1 && (
                          <div className="flex items-center gap-1 mt-2 text-xs text-slate-500">
                            <Network className="w-3 h-3" />
                            <span>{result.connectionPath.length - 1} degree connection</span>
                          </div>
                        )}

                        {result.node.data.tags && result.node.data.tags.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-2">
                            {result.node.data.tags.slice(0, 3).map((tag: string) => (
                              <span
                                key={tag}
                                className="px-2 py-0.5 bg-slate-700 text-slate-300 rounded text-xs"
                              >
                                {tag}
                              </span>
                            ))}
                            {result.node.data.tags.length > 3 && (
                              <span className="text-xs text-slate-500">
                                +{result.node.data.tags.length - 3} more
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        {searchResults.length > 0 && (
          <div className="p-3 border-t border-slate-700 text-xs text-slate-500 flex items-center justify-between">
            <span>{searchResults.length} result{searchResults.length !== 1 ? 's' : ''}</span>
            <span>
              Press <kbd className="px-1.5 py-0.5 bg-slate-700 rounded">ESC</kbd> to close
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
