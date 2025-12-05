/**
 * @fileoverview Smart positioning utilities for Via Canvas
 * @description Advanced positioning algorithms including gap detection,
 * overlap prevention, and intelligent placement for new nodes
 */

import { Node, Edge, XYPosition } from 'reactflow';
import { LAYOUT_SPACING } from './layoutConstants';
import { getNodeWidth, getNodeHeight, getRootNodes } from './nodeUtilities';

/**
 * Get absolute position of a node accounting for parent groups
 * Recursively calculates position by adding parent offsets
 */
export const getNodeAbsolutePosition = (node: Node, nodes: Node[]): XYPosition => {
  if (!node) {
    return { x: 0, y: 0 };
  }

  if (!node.parentNode) {
    return node.position;
  }

  const parent = nodes.find((n) => n.id === node.parentNode);
  if (!parent) {
    return node.position;
  }

  const parentPos = getNodeAbsolutePosition(parent, nodes);
  return {
    x: parentPos.x + node.position.x,
    y: parentPos.y + node.position.y,
  };
};

/**
 * Get the rightmost position for a new node with smart gap detection
 * Intelligently positions new nodes to the right of source nodes
 * while detecting and utilizing gaps to prevent overlaps
 * 
 * @param sourceNodes - Nodes to position relative to
 * @param nodes - All nodes in the canvas
 * @param _edges - All edges (unused but kept for API compatibility)
 * @returns Optimal position for the new node
 */
export const getRightmostPosition = (
  sourceNodes: Node[],
  nodes: Node[],
  _edges: Edge[],
): XYPosition => {
  // Convert source nodes to absolute positions if they are in groups
  const sourceNodesAbsolute = sourceNodes.map((node) => ({
    ...node,
    position: getNodeAbsolutePosition(node, nodes),
    width: getNodeWidth(node),
  }));

  // Calculate X position considering node width
  const rightmostX = Math.max(...sourceNodesAbsolute.map((n) => n.position.x + n.width / 2));
  const targetX = rightmostX + LAYOUT_SPACING.X;

  // Get all nodes at the same X level
  const nodesAtTargetLevel = nodes
    .filter((node) => {
      const absPos = getNodeAbsolutePosition(node, nodes);
      return Math.abs(absPos.x - targetX) < LAYOUT_SPACING.X / 2;
    })
    .map((node) => ({
      ...node,
      position: getNodeAbsolutePosition(node, nodes),
    }))
    .sort((a, b) => a.position.y - b.position.y);

  // Calculate average Y of source nodes
  const avgSourceY =
    sourceNodesAbsolute.reduce((sum, n) => sum + n.position.y, 0) / sourceNodesAbsolute.length;

  // If no nodes at this level, place at average Y of source nodes
  if (nodesAtTargetLevel.length === 0) {
    return {
      x: targetX,
      y: avgSourceY,
    };
  }

  // Calculate the best position based on existing nodes
  const fixedSpacing = LAYOUT_SPACING.Y;

  // Calculate position for new node
  let bestY = avgSourceY;
  let minOverlap = Number.POSITIVE_INFINITY;

  // Try different Y positions around the average source Y
  const range = Math.max(fixedSpacing * 3, getNodeHeight(nodesAtTargetLevel[0]));
  const step = fixedSpacing / 4;

  for (let y = avgSourceY - range; y <= avgSourceY + range; y += step) {
    let hasOverlap = false;
    let totalOverlap = 0;

    // Check overlap with existing nodes considering node heights
    for (const node of nodesAtTargetLevel) {
      const nodeHeight = getNodeHeight(node);
      const newNodeHeight = 150; // Default height for new node in Via Canvas

      // Calculate the vertical overlap between the two nodes
      const nodeTop = node.position.y - nodeHeight / 2;
      const nodeBottom = node.position.y + nodeHeight / 2;
      const newNodeTop = y - newNodeHeight / 2;
      const newNodeBottom = y + newNodeHeight / 2;

      // Check if the nodes overlap vertically
      if (!(newNodeBottom < nodeTop - fixedSpacing || newNodeTop > nodeBottom + fixedSpacing)) {
        hasOverlap = true;
        // Calculate the amount of overlap
        const overlap = Math.min(
          Math.abs(newNodeBottom - nodeTop),
          Math.abs(newNodeTop - nodeBottom),
        );
        totalOverlap += overlap;
      }
    }

    // If this position has less overlap, use it
    if (totalOverlap < minOverlap) {
      minOverlap = totalOverlap;
      bestY = y;
    }

    // If we found a position with no overlap, use it immediately
    if (!hasOverlap) {
      bestY = y;
      break;
    }
  }

  // If we still have overlap, try to find the largest gap
  if (minOverlap > 0) {
    const gaps: { start: number; end: number }[] = [];
    const firstNode = nodesAtTargetLevel[0];
    const firstNodeHeight = getNodeHeight(firstNode);

    // Add gap before first node
    gaps.push({
      start: avgSourceY - range,
      end: firstNode.position.y - firstNodeHeight / 2 - fixedSpacing,
    });

    // Add gaps between nodes
    for (let i = 0; i < nodesAtTargetLevel.length - 1; i++) {
      const currentNode = nodesAtTargetLevel[i];
      const nextNode = nodesAtTargetLevel[i + 1];
      const currentNodeHeight = getNodeHeight(currentNode);
      const nextNodeHeight = getNodeHeight(nextNode);

      gaps.push({
        start: currentNode.position.y + currentNodeHeight / 2 + fixedSpacing,
        end: nextNode.position.y - nextNodeHeight / 2 - fixedSpacing,
      });
    }

    // Add gap after last node
    const lastNode = nodesAtTargetLevel[nodesAtTargetLevel.length - 1];
    const lastNodeHeight = getNodeHeight(lastNode);
    gaps.push({
      start: lastNode.position.y + lastNodeHeight / 2 + fixedSpacing,
      end: avgSourceY + range,
    });

    // Find the best gap
    let bestGap = { start: 0, end: 0, size: 0, distanceToAvg: Number.POSITIVE_INFINITY };
    for (const gap of gaps) {
      const size = gap.end - gap.start;
      if (size >= fixedSpacing + 150) {
        // Consider minimum space needed for new node
        const gapCenter = (gap.start + gap.end) / 2;
        const distanceToAvg = Math.abs(gapCenter - avgSourceY);
        if (distanceToAvg < bestGap.distanceToAvg) {
          bestGap = { ...gap, size, distanceToAvg };
        }
      }
    }

    if (bestGap.size > 0) {
      bestY = (bestGap.start + bestGap.end) / 2;
    }
  }

  return {
    x: targetX,
    y: bestY,
  };
};

/**
 * Calculate optimal position for a new node
 * Supports viewport-aware positioning and smart placement
 * 
 * @param params - Configuration for position calculation
 * @returns Optimal position for the new node
 */
export interface CalculateNodePositionParams {
  nodes: Node[];
  sourceNodes?: Node[];
  defaultPosition?: XYPosition;
  edges?: Edge[];
  viewport?: {
    x: number;
    y: number;
    zoom: number;
  };
  autoLayout?: boolean;
}

export const calculateNodePosition = ({
  nodes,
  sourceNodes,
  defaultPosition,
  edges = [],
  viewport,
  autoLayout = false,
}: CalculateNodePositionParams): XYPosition => {
  // If position is provided, use it
  if (defaultPosition) {
    return defaultPosition;
  }

  // Case 1: No nodes exist or no source nodes - place in viewport center if available
  if (nodes.length === 0 || !sourceNodes?.length) {
    if (viewport) {
      // Center the node in the user's current visible area
      return {
        x: -viewport.x / viewport.zoom + window.innerWidth / 2 / viewport.zoom,
        y: -viewport.y / viewport.zoom + window.innerHeight / 2 / viewport.zoom,
      };
    }

    // Fallback to initial position
    if (nodes.length === 0) {
      return {
        x: LAYOUT_SPACING.INITIAL_X,
        y: LAYOUT_SPACING.INITIAL_Y,
      };
    }
  }

  // Case 2: Connected to existing nodes
  if (sourceNodes && sourceNodes.length > 0 && autoLayout) {
    const sourceNodesAbsolute = sourceNodes.map((node) => ({
      ...node,
      position: getNodeAbsolutePosition(node, nodes),
      width: getNodeWidth(node),
    }));

    return getRightmostPosition(sourceNodesAbsolute, nodes, edges);
  }

  // Case 3: No specific connections - add to a new branch
  const rootNodes = getRootNodes(nodes, edges);

  if (rootNodes.length > 0) {
    const sortedRootNodes = [...rootNodes].sort((a, b) => a.position.y - b.position.y);

    // Try to find a gap between root nodes
    for (let i = 0; i < sortedRootNodes.length - 1; i++) {
      const gap = sortedRootNodes[i + 1].position.y - sortedRootNodes[i].position.y;
      if (gap >= 30) {
        return {
          x: sortedRootNodes[i].position.x,
          y: sortedRootNodes[i].position.y + gap / 2,
        };
      }
    }

    // Place below the last root node
    const lastNode = sortedRootNodes[sortedRootNodes.length - 1];
    return {
      x: lastNode.position.x,
      y: lastNode.position.y + LAYOUT_SPACING.Y + (lastNode.height || 150),
    };
  }

  // Final fallback
  return {
    x: LAYOUT_SPACING.INITIAL_X,
    y: LAYOUT_SPACING.INITIAL_Y,
  };
};
