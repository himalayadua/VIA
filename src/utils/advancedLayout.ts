/**
 * @fileoverview Advanced layout algorithms for Via Canvas
 * @description Branch layout using Dagre while preserving root positions,
 * and utilities for managing node hierarchies and clusters
 */

import { Node, Edge, XYPosition } from 'reactflow';
import dagre from 'dagre';
import { LAYOUT_SPACING } from './layoutConstants';
import { getNodeHeight, getNodeLevel, getNodeWidth } from './nodeUtilities';
import { getNodeAbsolutePosition } from './smartPositioning';

export interface LayoutBranchOptions {
  fromRoot?: boolean; // whether to layout from root nodes
  direction?: 'TB' | 'LR';
  fixedNodeLevels?: boolean;
  spacing?: {
    x: number;
    y: number;
  };
}

/**
 * Get all nodes in a branch starting from specific nodes
 * Traverses the graph following outgoing edges
 */
export const getBranchNodes = (
  startNodeIds: string[],
  nodes: Node[],
  edges: Edge[],
  visited: Set<string> = new Set(),
): Node[] => {
  const branchNodes: Node[] = [];
  const queue = [...startNodeIds];

  while (queue.length > 0) {
    const currentId = queue.shift();
    if (!currentId || visited.has(currentId)) continue;
    visited.add(currentId);

    const node = nodes.find((n) => n.id === currentId);
    if (node) {
      branchNodes.push(node);

      // Only get outgoing connections to maintain hierarchy
      const outgoingIds = edges
        .filter((e) => e.source === currentId)
        .map((e) => e.target);

      queue.push(...outgoingIds);
    }
  }

  return branchNodes;
};

/**
 * Get nodes at a specific hierarchy level
 * Uses breadth-first search from root nodes
 */
export const getNodesAtLevel = (
  nodes: Node[],
  edges: Edge[],
  level: number,
  rootNodes: Node[],
): Node[] => {
  const result: Node[] = [];
  const visited = new Set<string>();
  const queue: Array<{ node: Node; level: number }> = rootNodes.map((node) => ({ 
    node, 
    level: 0 
  }));

  while (queue.length > 0) {
    const item = queue.shift();
    if (!item) continue;
    
    const { node, level: currentLevel } = item;

    if (!node || visited.has(node.id)) continue;
    visited.add(node.id);

    if (currentLevel === level) {
      result.push(node);
      continue;
    }

    // Add next level nodes to queue
    const nextNodes = edges
      .filter((edge) => edge.source === node.id)
      .map((edge) => nodes.find((n) => n.id === edge.target))
      .filter((n): n is Node => n !== undefined)
      .map((node) => ({ node, level: currentLevel + 1 }));

    queue.push(...nextNodes);
  }

  return result;
};

/**
 * Layout a branch using Dagre while preserving root positions
 * Provides intelligent hierarchical layout for connected node groups
 * 
 * @param branchNodes - Nodes in the branch to layout
 * @param edges - All edges in the canvas
 * @param rootNodes - Root nodes whose positions should be preserved
 * @param options - Layout configuration options
 * @returns Nodes with updated positions
 */
export const layoutBranch = (
  branchNodes: Node[],
  edges: Edge[],
  rootNodes: Node[],
  options: LayoutBranchOptions = {},
): Node[] => {
  const g = new dagre.graphlib.Graph().setDefaultEdgeLabel(() => ({}));

  // Configure the layout with consistent spacing
  g.setGraph({
    rankdir: 'LR',
    nodesep: LAYOUT_SPACING.Y,
    ranksep: LAYOUT_SPACING.X,
    marginx: 50,
    marginy: 50,
  });

  // Add all nodes to the graph with their actual dimensions
  for (const node of branchNodes) {
    const nodeWidth = getNodeWidth(node);
    const nodeHeight = getNodeHeight(node);
    g.setNode(node.id, {
      ...node,
      width: nodeWidth,
      height: nodeHeight,
      originalWidth: nodeWidth,
      originalHeight: nodeHeight,
    });
  }

  // Add edges
  for (const edge of edges) {
    if (
      branchNodes.some((n) => n.id === edge.source) &&
      branchNodes.some((n) => n.id === edge.target)
    ) {
      g.setEdge(edge.source, edge.target);
    }
  }

  // Get the maximum level in the branch
  const maxLevel = Math.max(
    ...branchNodes.map((node) => getNodeLevel(node.id, branchNodes, edges, rootNodes)),
  );

  // Fix positions based on mode
  for (const node of branchNodes) {
    const level = getNodeLevel(node.id, branchNodes, edges, rootNodes);
    const isRoot = rootNodes.some((root) => root.id === node.id);
    const shouldFixPosition = options.fromRoot ? isRoot : level < maxLevel;

    if (shouldFixPosition) {
      const nodeWidth = getNodeWidth(node);
      g.setNode(node.id, {
        ...g.node(node.id),
        x: node.position.x + nodeWidth / 2,
        y: node.position.y,
        fixed: true,
      });
    }
  }

  // Apply layout
  dagre.layout(g);

  // Return nodes with updated positions
  return branchNodes.map((node) => {
    const nodeWithPosition = g.node(node.id);
    const level = getNodeLevel(node.id, branchNodes, edges, rootNodes);
    const isRoot = rootNodes.some((root) => root.id === node.id);
    const shouldPreservePosition = options.fromRoot ? isRoot : level < maxLevel;

    if (shouldPreservePosition) {
      return node; // Keep original position for fixed nodes
    }

    // For non-fixed nodes, ensure they maintain relative Y position to their source nodes
    const sourceEdges = edges.filter((edge) => edge.target === node.id);
    if (sourceEdges.length > 0 && !options.fromRoot) {
      const sourceNodes = sourceEdges
        .map((edge) => branchNodes.find((n) => n.id === edge.source))
        .filter((n): n is Node => n !== undefined);

      if (sourceNodes.length > 0) {
        const avgSourceY =
          sourceNodes.reduce((sum, n) => sum + n.position.y, 0) / sourceNodes.length;
        const nodeWidth = getNodeWidth(node);
        return {
          ...node,
          position: {
            x: nodeWithPosition.x - nodeWidth / 2,
            y: avgSourceY,
          },
        };
      }
    }

    // For other nodes, adjust position based on node width
    const nodeWidth = getNodeWidth(node);
    return {
      ...node,
      position: {
        x: nodeWithPosition.x - nodeWidth / 2,
        y: nodeWithPosition.y,
      },
    };
  });
};

/**
 * Get the branch cluster that a node belongs to
 * Finds all connected nodes (both upstream and downstream)
 */
export const getBranchCluster = (nodeId: string, nodes: Node[], edges: Edge[]): Node[] => {
  const visited = new Set<string>();
  const cluster = new Set<string>();
  const queue = [nodeId];

  // First traverse upwards to find root
  while (queue.length > 0) {
    const currentId = queue.shift();
    if (!currentId || visited.has(currentId)) continue;
    visited.add(currentId);
    cluster.add(currentId);

    // Add parent nodes
    const parentIds = edges
      .filter((edge) => edge.target === currentId)
      .map((edge) => edge.source);
    queue.push(...parentIds);
  }

  // Then traverse downwards from all found nodes
  const downQueue = Array.from(cluster);
  visited.clear();

  while (downQueue.length > 0) {
    const currentId = downQueue.shift();
    if (!currentId || visited.has(currentId)) continue;
    visited.add(currentId);

    // Add child nodes
    const childIds = edges
      .filter((edge) => edge.source === currentId)
      .map((edge) => edge.target);
    downQueue.push(...childIds);
    for (const id of childIds) {
      cluster.add(id);
    }
  }

  return nodes.filter((node) => cluster.has(node.id));
};

/**
 * Get position updates for laying out a branch
 * Calculates optimal positions for all nodes in a branch
 */
export const getLayoutBranchPositionUpdates = (
  sourceNodes: Node[],
  allNodes: Node[],
  edges: Edge[],
): Map<string, XYPosition> => {
  // Collect all source nodes including children of group nodes
  const sourceNodesAbsolute = sourceNodes.map((node) => ({
    ...node,
    position: getNodeAbsolutePosition(node, allNodes),
    width: getNodeWidth(node),
  }));
  
  if (sourceNodesAbsolute.length === 0) return new Map();

  // Find all nodes directly connected to source nodes
  const targetNodeIds = new Set<string>();
  const queue = [...sourceNodes.map((n) => n.id)];
  const visited = new Set<string>();

  while (queue.length > 0) {
    const currentId = queue.shift();
    if (!currentId || visited.has(currentId)) continue;
    visited.add(currentId);

    for (const edge of edges) {
      if (edge.source === currentId && !sourceNodes.some((n) => n.id === edge.target)) {
        targetNodeIds.add(edge.target);
        queue.push(edge.target);
      }
    }
  }

  const targetNodes = allNodes.filter((node) => targetNodeIds.has(node.id));
  if (targetNodes.length === 0) return new Map();

  // Group nodes by their level
  const nodeLevels = new Map<number, Node[]>();
  const nodeLevel = new Map<string, number>();

  const calculateLevels = (nodeId: string, level: number) => {
    if (nodeLevel.has(nodeId)) return;
    nodeLevel.set(nodeId, level);

    const levelNodes = nodeLevels.get(level) || [];
    const node = allNodes.find((n) => n.id === nodeId);
    if (node) {
      levelNodes.push(node);
      nodeLevels.set(level, levelNodes);
    }

    // Process children
    for (const edge of edges) {
      if (edge.source === nodeId) {
        calculateLevels(edge.target, level + 1);
      }
    }
  };

  // Start level calculation from source nodes
  for (const node of sourceNodesAbsolute) {
    calculateLevels(node.id, 0);
  }

  // Calculate positions for each level
  const nodePositions = new Map<string, XYPosition>();
  const fixedSpacing = LAYOUT_SPACING.Y;

  for (const [level, nodes] of Array.from(nodeLevels.entries())) {
    const levelX =
      level === 0
        ? Math.max(...sourceNodesAbsolute.map((n) => n.position.x + getNodeWidth(n) / 2))
        : Math.max(
            ...Array.from(nodeLevels.get(level - 1) || []).map((n) => {
              const nodeWidth = getNodeWidth(n);
              const pos = n.position;
              return pos.x + nodeWidth / 2;
            }),
          ) + LAYOUT_SPACING.X;

    const avgSourceY =
      sourceNodesAbsolute.reduce((sum, n) => sum + n.position.y, 0) / sourceNodesAbsolute.length;
    
    let currentY = avgSourceY;

    nodes.forEach((node) => {
      const nodeHeight = getNodeHeight(node);
      nodePositions.set(node.id, {
        x: levelX,
        y: currentY + nodeHeight / 2,
      });
      currentY += nodeHeight + fixedSpacing;
    });
  }

  // Filter to only target nodes
  const filteredPositions = new Map<string, XYPosition>();
  for (const [nodeId, position] of nodePositions.entries()) {
    if (targetNodeIds.has(nodeId)) {
      filteredPositions.set(nodeId, position);
    }
  }

  return filteredPositions;
};
