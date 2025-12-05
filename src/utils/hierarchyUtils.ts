import { Node, Edge } from 'reactflow';

export interface NodeHierarchy {
  nodeId: string;
  children: NodeHierarchy[];
}

/**
 * Build a hierarchy map from nodes and edges
 */
export function buildHierarchy(nodes: Node[], edges: Edge[]): Map<string, NodeHierarchy> {
  const hierarchyMap = new Map<string, NodeHierarchy>();

  // Initialize hierarchy for all nodes
  nodes.forEach(node => {
    hierarchyMap.set(node.id, {
      nodeId: node.id,
      children: []
    });
  });

  // Build parent-child relationships from edges
  edges.forEach(edge => {
    const parent = hierarchyMap.get(edge.source);
    const child = hierarchyMap.get(edge.target);

    if (parent && child) {
      parent.children.push(child);
    }
  });

  return hierarchyMap;
}

/**
 * Get all descendant node IDs recursively
 */
export function getDescendants(nodeId: string, hierarchyMap: Map<string, NodeHierarchy>): string[] {
  const descendants: string[] = [];
  const node = hierarchyMap.get(nodeId);

  if (!node) return descendants;

  const traverse = (hierarchy: NodeHierarchy) => {
    hierarchy.children.forEach(child => {
      descendants.push(child.nodeId);
      traverse(child);
    });
  };

  traverse(node);
  return descendants;
}

/**
 * Get all descendant edges recursively
 */
export function getDescendantEdges(nodeId: string, edges: Edge[], hierarchyMap: Map<string, NodeHierarchy>): string[] {
  const descendants = getDescendants(nodeId, hierarchyMap);
  const descendantSet = new Set([nodeId, ...descendants]);

  return edges
    .filter(edge => descendantSet.has(edge.source) && descendantSet.has(edge.target))
    .map(edge => edge.id);
}

/**
 * Move a node and all its descendants by a delta
 */
export function moveNodeWithChildren(
  nodeId: string,
  delta: { x: number; y: number },
  hierarchyMap: Map<string, NodeHierarchy>,
  nodes: Node[]
): Node[] {
  const descendants = getDescendants(nodeId, hierarchyMap);
  const nodesToMove = new Set([nodeId, ...descendants]);

  return nodes.map(node => {
    if (nodesToMove.has(node.id)) {
      return {
        ...node,
        position: {
          x: node.position.x + delta.x,
          y: node.position.y + delta.y
        }
      };
    }
    return node;
  });
}

/**
 * Check if a node has children
 */
export function hasChildren(nodeId: string, edges: Edge[]): boolean {
  return edges.some(edge => edge.source === nodeId);
}

/**
 * Get direct children of a node
 */
export function getDirectChildren(nodeId: string, edges: Edge[]): string[] {
  return edges
    .filter(edge => edge.source === nodeId)
    .map(edge => edge.target);
}

/**
 * Get parent of a node
 */
export function getParent(nodeId: string, edges: Edge[]): string | null {
  const parentEdge = edges.find(edge => edge.target === nodeId);
  return parentEdge ? parentEdge.source : null;
}

/**
 * Count total descendants
 */
export function countDescendants(nodeId: string, hierarchyMap: Map<string, NodeHierarchy>): number {
  return getDescendants(nodeId, hierarchyMap).length;
}
