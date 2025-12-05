import { create } from 'zustand';
import { Node, Edge } from 'reactflow';
import { CardType } from '../types/cardTypes';
import { SearchQuery, SearchResult, search } from '../utils/searchEngine';
import { CanvasSnapshot } from '../utils/snapshotManager';

interface SearchState {
    isOpen: boolean;
    searchQuery: string;
    searchMode: 'keyword' | 'similarity' | 'relationship';
    searchResults: SearchResult[];
    highlightedNodes: Set<string>;
    selectedResultIndex: number;

    // Filters
    selectedCardTypes: CardType[];
    selectedTags: string[];
    dateRange: { start: string; end: string } | null;
    connectionLevel: number;
    sourceNodeId: string | null;

    // Actions
    openSearch: () => void;
    closeSearch: () => void;
    setSearchQuery: (query: string) => void;
    setSearchMode: (mode: 'keyword' | 'similarity' | 'relationship') => void;
    setSourceNodeId: (nodeId: string | null) => void;
    setConnectionLevel: (level: number) => void;
    toggleCardTypeFilter: (cardType: CardType) => void;
    toggleTagFilter: (tag: string) => void;
    setDateRange: (range: { start: string; end: string } | null) => void;
    clearFilters: () => void;

    performSearch: (nodes: Node[], edges: Edge[], snapshots?: CanvasSnapshot[]) => void;
    clearSearch: () => void;
    selectResult: (index: number) => void;
    selectNextResult: () => void;
    selectPreviousResult: () => void;
    highlightNodes: (nodeIds: string[]) => void;
    clearHighlights: () => void;
}

export const useSearchStore = create<SearchState>((set, get) => ({
    isOpen: false,
    searchQuery: '',
    searchMode: 'keyword',
    searchResults: [],
    highlightedNodes: new Set(),
    selectedResultIndex: -1,

    selectedCardTypes: [],
    selectedTags: [],
    dateRange: null,
    connectionLevel: 3,
    sourceNodeId: null,

    openSearch: () => set({ isOpen: true }),

    closeSearch: () => {
        set({
            isOpen: false,
            searchQuery: '',
            searchResults: [],
            highlightedNodes: new Set(),
            selectedResultIndex: -1
        });
    },

    setSearchQuery: (query) => set({ searchQuery: query }),

    setSearchMode: (mode) => {
        set({ searchMode: mode, searchResults: [], selectedResultIndex: -1 });
    },

    setSourceNodeId: (nodeId) => set({ sourceNodeId: nodeId }),

    setConnectionLevel: (level) => set({ connectionLevel: level }),

    toggleCardTypeFilter: (cardType) => {
        set((state) => {
            const selected = state.selectedCardTypes;
            const index = selected.indexOf(cardType);

            if (index > -1) {
                return { selectedCardTypes: selected.filter(t => t !== cardType) };
            } else {
                return { selectedCardTypes: [...selected, cardType] };
            }
        });
    },

    toggleTagFilter: (tag) => {
        set((state) => {
            const selected = state.selectedTags;
            const index = selected.indexOf(tag);

            if (index > -1) {
                return { selectedTags: selected.filter(t => t !== tag) };
            } else {
                return { selectedTags: [...selected, tag] };
            }
        });
    },

    setDateRange: (range) => set({ dateRange: range }),

    clearFilters: () => {
        set({
            selectedCardTypes: [],
            selectedTags: [],
            dateRange: null,
            connectionLevel: 3
        });
    },

    performSearch: (nodes, edges, snapshots = []) => {
        const state = get();

        // Build search query
        const query: SearchQuery = {
            text: state.searchQuery,
            mode: state.searchMode,
            sourceNodeId: state.sourceNodeId || undefined,
            filters: {
                cardTypes: state.selectedCardTypes.length > 0 ? state.selectedCardTypes : undefined,
                tags: state.selectedTags.length > 0 ? state.selectedTags : undefined,
                dateRange: state.dateRange || undefined,
                connectionLevel: state.connectionLevel
            }
        };

        // Perform search
        const results = search(query, nodes, edges, snapshots);

        // Update state
        set({
            searchResults: results,
            selectedResultIndex: results.length > 0 ? 0 : -1,
            highlightedNodes: new Set(results.map(r => r.nodeId))
        });
    },

    clearSearch: () => {
        set({
            searchQuery: '',
            searchResults: [],
            highlightedNodes: new Set(),
            selectedResultIndex: -1
        });
    },

    selectResult: (index) => {
        const { searchResults } = get();
        if (index >= 0 && index < searchResults.length) {
            set({ selectedResultIndex: index });
        }
    },

    selectNextResult: () => {
        const { searchResults, selectedResultIndex } = get();
        if (searchResults.length > 0) {
            const nextIndex = (selectedResultIndex + 1) % searchResults.length;
            set({ selectedResultIndex: nextIndex });
        }
    },

    selectPreviousResult: () => {
        const { searchResults, selectedResultIndex } = get();
        if (searchResults.length > 0) {
            const prevIndex = selectedResultIndex <= 0
                ? searchResults.length - 1
                : selectedResultIndex - 1;
            set({ selectedResultIndex: prevIndex });
        }
    },

    highlightNodes: (nodeIds) => {
        set({ highlightedNodes: new Set(nodeIds) });
    },

    clearHighlights: () => {
        set({ highlightedNodes: new Set() });
    }
}));
