/**
 * @fileoverview Canvas node utilities for Via Canvas
 * @description Helper functions for working with canvas nodes including
 * dimension calculations, hierarchy analysis, and metadata generation
 */

import { Node, Edge } from 'reactflow';
import { CardType } from '../types/cardTypes';

/**
 * Gets the measured height of a canvas node
 * Falls back to default if not measured yet
 */
export const getNodeHeight = (node: Node): number => {
  return node.height || 150; // Via Canvas default height
};

/**
 * Gets the measured width of a canvas node
 * Falls back to default if not measured yet
 */
export const getNodeWidth = (node: Node): number => {
  return node.width || 300; // Via Canvas default width
};

/**
 * Calculates the hierarchical level of a node from the root nodes
 * Uses breadth-first search to determine depth in the graph
 * 
 * @param nodeId - The ID of the node to find the level for
 * @param _nodes - Array of all nodes (unused but kept for API compatibility)
 * @param edges - Array of all edges defining node connections
 * @param rootNodes - Array of root nodes to start the level calculation from
 * @returns The level number (0 for root nodes), or -1 if node not found
 */
export const getNodeLevel = (
  nodeId: string,
  _nodes: Node[],
  edges: Edge[],
  rootNodes: Node[],
): number => {
  const visited = new Set<string>();
  const queue: Array<{ id: string; level: number }> = rootNodes.map((node) => ({
    id: node.id,
    level: 0,
  }));

  while (queue.length > 0) {
    const item = queue.shift();
    if (!item) continue;
    
    const { id, level } = item;

    if (id === nodeId) return level;
    if (visited.has(id) || !id) continue;
    visited.add(id);

    // Find all nodes directly connected from this node
    const nextIds = edges
      .filter((edge) => edge.source === id)
      .map((edge) => ({ id: edge.target, level: level + 1 }));

    queue.push(...nextIds);
  }

  return -1; // Node not found
};

/**
 * Identifies root nodes in a canvas graph (nodes with no incoming edges)
 * Root nodes are starting points with no dependencies
 * 
 * @param nodes - Array of all nodes in the canvas
 * @param edges - Array of all edges defining node connections
 * @returns Array of root nodes
 */
export const getRootNodes = (nodes: Node[], edges: Edge[]): Node[] => {
  return nodes.filter((node) => !edges.some((edge) => edge.target === node.id));
};

/**
 * Generates default metadata for a canvas node based on its type
 * Provides sensible defaults for Via Canvas card types
 * 
 * @param nodeType - The type of canvas node
 * @returns Default metadata object appropriate for the node type
 */
export const getNodeDefaultMetadata = (nodeType: CardType) => {
  if (!nodeType) {
    return {};
  }

  const baseMetadata = {
    sizeMode: 'adaptive' as const,
  };

  switch (nodeType) {
    case CardType.RICH_TEXT:
      return {
        ...baseMetadata,
        content: '',
        title: '',
        lastModified: new Date().toISOString(),
      };

    case CardType.TODO:
      return {
        ...baseMetadata,
        completed: false,
        items: [],
      };

    case CardType.VIDEO:
      return {
        ...baseMetadata,
        url: '',
        title: '',
        thumbnail: '',
      };

    case CardType.LINK:
      return {
        ...baseMetadata,
        url: '',
        title: '',
        description: '',
      };

    case CardType.REMINDER:
      return {
        ...baseMetadata,
        text: '',
        dueDate: null,
        completed: false,
      };

    default:
      return baseMetadata;
  }
};
