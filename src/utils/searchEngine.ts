import { Node, Edge } from 'reactflow';
import { CardType, RichTextData, TodoData, LinkData, ReminderData } from '../types/cardTypes';
import { CanvasSnapshot } from './snapshotManager';

export interface SearchQuery {
  text: string;
  filters: {
    cardTypes?: CardType[];
    tags?: string[];
    dateRange?: { start: string; end: string };
    connectionLevel?: number; // 0 = all, 1 = direct, 2 = second-degree, etc.
  };
  mode: 'keyword' | 'similarity' | 'relationship';
  sourceNodeId?: string; // For relationship search
}

export interface SearchResult {
  nodeId: string;
  score: number;
  matchType: 'title' | 'content' | 'tag' | 'connection';
  snippet: string;
  connectionPath?: string[]; // For relationship search
  node: Node; // Include full node for rendering
}

/**
 * Extract searchable text content from a node based on its card type
 */
function extractNodeContent(node: Node): string {
  const data = node.data;
  let content = '';

  // Add title
  if (data.title) {
    content += data.title + ' ';
  }

  // Add type-specific content
  switch (data.cardType) {
    case CardType.RICH_TEXT:
      content += (data as RichTextData).content || '';
      break;
    case CardType.TODO:
      const todoData = data as TodoData;
      content += todoData.items?.map(item => item.text).join(' ') || '';
      break;
    case CardType.LINK:
      const linkData = data as LinkData;
      content += (linkData.url || '') + ' ' + (linkData.description || '');
      break;
    case CardType.REMINDER:
      const reminderData = data as ReminderData;
      content += reminderData.description || '';
      break;
    case CardType.VIDEO:
      // Video nodes don't have much searchable text
      content += data.videoUrl || '';
      break;
  }

  // Add tags
  if (data.tags && Array.isArray(data.tags)) {
    content += ' ' + data.tags.join(' ');
  }

  return content.toLowerCase();
}

/**
 * Create a snippet from content with highlighted match
 */
function createSnippet(content: string, query: string, maxLength: number = 150): string {
  const lowerContent = content.toLowerCase();
  const lowerQuery = query.toLowerCase();
  const index = lowerContent.indexOf(lowerQuery);

  if (index === -1) {
    return content.substring(0, maxLength) + (content.length > maxLength ? '...' : '');
  }

  const start = Math.max(0, index - 50);
  const end = Math.min(content.length, index + query.length + 50);
  
  let snippet = content.substring(start, end);
  if (start > 0) snippet = '...' + snippet;
  if (end < content.length) snippet = snippet + '...';

  return snippet;
}

/**
 * Keyword search: Search through node titles, content, and tags
 * Also searches historical snapshots for deleted/modified content
 */
export function keywordSearch(
  query: string,
  nodes: Node[],
  snapshots: CanvasSnapshot[] = []
): SearchResult[] {
  if (!query.trim()) return [];

  const lowerQuery = query.toLowerCase();
  const results: SearchResult[] = [];
  const seenNodeIds = new Set<string>();

  // Search current nodes
  nodes.forEach(node => {
    const data = node.data;
    let score = 0;
    let matchType: SearchResult['matchType'] = 'content';
    let snippet = '';

    // Check title (highest priority)
    if (data.title && data.title.toLowerCase().includes(lowerQuery)) {
      score += 10;
      matchType = 'title';
      snippet = createSnippet(data.title, query);
    }

    // Check tags (high priority)
    if (data.tags && Array.isArray(data.tags)) {
      const tagMatch = data.tags.some((tag: string) => 
        tag.toLowerCase().includes(lowerQuery)
      );
      if (tagMatch) {
        score += 7;
        if (matchType !== 'title') {
          matchType = 'tag';
          snippet = `Tags: ${data.tags.join(', ')}`;
        }
      }
    }

    // Check content (medium priority)
    const content = extractNodeContent(node);
    if (content.includes(lowerQuery)) {
      score += 5;
      if (matchType === 'content') {
        snippet = createSnippet(content, query);
      }
    }

    if (score > 0) {
      seenNodeIds.add(node.id);
      results.push({
        nodeId: node.id,
        score,
        matchType,
        snippet: snippet || createSnippet(content, query),
        node
      });
    }
  });

  // Search historical snapshots
  snapshots.forEach(snapshot => {
    snapshot.nodes.forEach(historicalNode => {
      // Skip if we already found this node in current nodes
      if (seenNodeIds.has(historicalNode.id)) return;

      const data = historicalNode.data;
      let score = 0;
      let matchType: SearchResult['matchType'] = 'content';
      let snippet = '';

      // Check title
      if (data.title && data.title.toLowerCase().includes(lowerQuery)) {
        score += 8; // Slightly lower score for historical
        matchType = 'title';
        snippet = createSnippet(data.title, query) + ' (historical)';
      }

      // Check tags
      if (data.tags && Array.isArray(data.tags)) {
        const tagMatch = data.tags.some((tag: string) => 
          tag.toLowerCase().includes(lowerQuery)
        );
        if (tagMatch) {
          score += 5;
          if (matchType !== 'title') {
            matchType = 'tag';
            snippet = `Tags: ${data.tags.join(', ')} (historical)`;
          }
        }
      }

      // Check content
      const content = extractNodeContent(historicalNode);
      if (content.includes(lowerQuery)) {
        score += 3;
        if (matchType === 'content') {
          snippet = createSnippet(content, query) + ' (historical)';
        }
      }

      if (score > 0) {
        seenNodeIds.add(historicalNode.id);
        results.push({
          nodeId: historicalNode.id,
          score,
          matchType,
          snippet: snippet || createSnippet(content, query) + ' (historical)',
          node: historicalNode
        });
      }
    });
  });

  // Sort by score (descending)
  return results.sort((a, b) => b.score - a.score);
}

/**
 * Tokenize text into words
 */
function tokenize(text: string): string[] {
  return text
    .toLowerCase()
    .replace(/[^\w\s]/g, ' ')
    .split(/\s+/)
    .filter(word => word.length > 2); // Filter out very short words
}

/**
 * Calculate TF-IDF vectors for similarity search
 */
function calculateTFIDF(documents: string[]): Map<number, Map<string, number>> {
  const docCount = documents.length;
  const termDocCount = new Map<string, number>();
  const docTerms = documents.map(doc => tokenize(doc));

  // Calculate document frequency for each term
  docTerms.forEach(terms => {
    const uniqueTerms = new Set(terms);
    uniqueTerms.forEach(term => {
      termDocCount.set(term, (termDocCount.get(term) || 0) + 1);
    });
  });

  // Calculate TF-IDF for each document
  const tfidfVectors = new Map<number, Map<string, number>>();

  docTerms.forEach((terms, docIndex) => {
    const termFreq = new Map<string, number>();
    terms.forEach(term => {
      termFreq.set(term, (termFreq.get(term) || 0) + 1);
    });

    const tfidf = new Map<string, number>();
    termFreq.forEach((tf, term) => {
      const df = termDocCount.get(term) || 1;
      const idf = Math.log(docCount / df);
      tfidf.set(term, tf * idf);
    });

    tfidfVectors.set(docIndex, tfidf);
  });

  return tfidfVectors;
}

/**
 * Calculate cosine similarity between two TF-IDF vectors
 */
function cosineSimilarity(vec1: Map<string, number>, vec2: Map<string, number>): number {
  let dotProduct = 0;
  let mag1 = 0;
  let mag2 = 0;

  // Calculate dot product and magnitude of vec1
  vec1.forEach((value, term) => {
    mag1 += value * value;
    const vec2Value = vec2.get(term) || 0;
    dotProduct += value * vec2Value;
  });

  // Calculate magnitude of vec2
  vec2.forEach(value => {
    mag2 += value * value;
  });

  mag1 = Math.sqrt(mag1);
  mag2 = Math.sqrt(mag2);

  if (mag1 === 0 || mag2 === 0) return 0;

  return dotProduct / (mag1 * mag2);
}

/**
 * Similarity search: Find nodes with similar content using TF-IDF and cosine similarity
 */
export function similaritySearch(
  query: string,
  nodes: Node[]
): SearchResult[] {
  if (!query.trim() || nodes.length === 0) return [];

  // Extract content from all nodes
  const documents = nodes.map(node => extractNodeContent(node));
  
  // Add query as the first document
  const allDocuments = [query.toLowerCase(), ...documents];

  // Calculate TF-IDF vectors
  const tfidfVectors = calculateTFIDF(allDocuments);
  const queryVector = tfidfVectors.get(0)!;

  // Calculate similarity scores
  const results: SearchResult[] = [];

  nodes.forEach((node, index) => {
    const docVector = tfidfVectors.get(index + 1)!;
    const similarity = cosineSimilarity(queryVector, docVector);

    if (similarity > 0.1) { // Threshold to filter out very low similarities
      const content = extractNodeContent(node);
      results.push({
        nodeId: node.id,
        score: similarity * 100, // Scale to 0-100
        matchType: 'content',
        snippet: createSnippet(content, query),
        node
      });
    }
  });

  // Sort by similarity score (descending)
  return results.sort((a, b) => b.score - a.score);
}

/**
 * Build adjacency list from edges
 */
function buildAdjacencyList(edges: Edge[]): Map<string, Set<string>> {
  const adjacency = new Map<string, Set<string>>();

  edges.forEach(edge => {
    // Add forward edge
    if (!adjacency.has(edge.source)) {
      adjacency.set(edge.source, new Set());
    }
    adjacency.get(edge.source)!.add(edge.target);

    // Add backward edge (for undirected traversal)
    if (!adjacency.has(edge.target)) {
      adjacency.set(edge.target, new Set());
    }
    adjacency.get(edge.target)!.add(edge.source);
  });

  return adjacency;
}

/**
 * Relationship search: Find nodes connected to a source node using BFS
 */
export function relationshipSearch(
  sourceNodeId: string,
  maxDegree: number,
  nodes: Node[],
  edges: Edge[]
): SearchResult[] {
  if (!sourceNodeId || maxDegree < 1) return [];

  const adjacency = buildAdjacencyList(edges);
  const nodeMap = new Map(nodes.map(node => [node.id, node]));
  
  // BFS to find connected nodes
  const visited = new Set<string>();
  const queue: Array<{ nodeId: string; degree: number; path: string[] }> = [];
  const results: SearchResult[] = [];

  // Start with source node
  queue.push({ nodeId: sourceNodeId, degree: 0, path: [sourceNodeId] });
  visited.add(sourceNodeId);

  while (queue.length > 0) {
    const current = queue.shift()!;

    // Skip if we've exceeded max degree
    if (current.degree >= maxDegree) continue;

    // Get neighbors
    const neighbors = adjacency.get(current.nodeId) || new Set();

    neighbors.forEach(neighborId => {
      if (!visited.has(neighborId)) {
        visited.add(neighborId);
        const path = [...current.path, neighborId];
        const degree = current.degree + 1;

        queue.push({ nodeId: neighborId, degree, path });

        // Add to results (exclude source node itself)
        if (neighborId !== sourceNodeId) {
          const node = nodeMap.get(neighborId);
          if (node) {
            const content = extractNodeContent(node);
            results.push({
              nodeId: neighborId,
              score: 100 - (degree * 10), // Closer nodes have higher scores
              matchType: 'connection',
              snippet: createSnippet(content, '', 100),
              connectionPath: path,
              node
            });
          }
        }
      }
    });
  }

  // Sort by score (closer connections first)
  return results.sort((a, b) => b.score - a.score);
}

/**
 * Apply filters to search results
 */
export function applyFilters(
  results: SearchResult[],
  filters: SearchQuery['filters']
): SearchResult[] {
  let filtered = results;

  // Filter by card types
  if (filters.cardTypes && filters.cardTypes.length > 0) {
    filtered = filtered.filter(result => 
      filters.cardTypes!.includes(result.node.data.cardType)
    );
  }

  // Filter by tags
  if (filters.tags && filters.tags.length > 0) {
    filtered = filtered.filter(result => {
      const nodeTags = result.node.data.tags || [];
      return filters.tags!.some(tag => nodeTags.includes(tag));
    });
  }

  // Filter by date range
  if (filters.dateRange) {
    const { start, end } = filters.dateRange;
    filtered = filtered.filter(result => {
      const createdAt = result.node.data.createdAt;
      if (!createdAt) return false;
      return createdAt >= start && createdAt <= end;
    });
  }

  return filtered;
}

/**
 * Main search function that routes to appropriate search algorithm
 */
export function search(
  query: SearchQuery,
  nodes: Node[],
  edges: Edge[],
  snapshots: CanvasSnapshot[] = []
): SearchResult[] {
  let results: SearchResult[] = [];

  switch (query.mode) {
    case 'keyword':
      results = keywordSearch(query.text, nodes, snapshots);
      break;
    
    case 'similarity':
      results = similaritySearch(query.text, nodes);
      break;
    
    case 'relationship':
      if (query.sourceNodeId) {
        const maxDegree = query.filters.connectionLevel || 3;
        results = relationshipSearch(query.sourceNodeId, maxDegree, nodes, edges);
      }
      break;
  }

  // Apply filters
  results = applyFilters(results, query.filters);

  return results;
}
