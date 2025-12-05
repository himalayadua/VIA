import { Node, Edge } from 'reactflow';
import dagre from 'dagre';
import { forceSimulation, forceLink, forceManyBody, forceCenter, forceCollide } from 'd3-force';

export type LayoutAlgorithm = 'force' | 'tree' | 'circular';

export interface LayoutConfig {
  algorithm: LayoutAlgorithm;
  spacing?: number;
  direction?: 'TB' | 'LR' | 'BT' | 'RL'; // Tree layout only
  preventOverlap?: boolean;
  animationDuration?: number;
}

const DEFAULT_CONFIG: LayoutConfig = {
  algorithm: 'tree',
  spacing: 100,
  direction: 'TB',
  preventOverlap: true,
  animationDuration: 300
};

/**
 * Apply tree layout using dagre
 */
export function treeLayout(
  nodes: Node[],
  edges: Edge[],
  config: Partial<LayoutConfig> = {}
): Node[] {
  const { spacing = 100, direction = 'TB' } = { ...DEFAULT_CONFIG, ...config };

  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  dagreGraph.setGraph({
    rankdir: direction,
    nodesep: spacing,
    ranksep: spacing * 1.5,
    marginx: 50,
    marginy: 50
  });

  // Add nodes to dagre graph
  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, {
      width: node.width || 300,
      height: node.height || 150
    });
  });

  // Add edges to dagre graph
  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  // Calculate layout
  dagre.layout(dagreGraph);

  // Update node positions
  return nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    
    return {
      ...node,
      position: {
        x: nodeWithPosition.x - (node.width || 300) / 2,
        y: nodeWithPosition.y - (node.height || 150) / 2
      }
    };
  });
}

/**
 * Apply force-directed layout using d3-force
 * Creates organic, physics-based layouts with proper spacing and no overlaps
 */
export function forceDirectedLayout(
  nodes: Node[],
  edges: Edge[],
  config: Partial<LayoutConfig> = {}
): Node[] {
  const { spacing = 100 } = { ...DEFAULT_CONFIG, ...config };

  if (nodes.length === 0) return [];
  if (nodes.length === 1) {
    // Single node - center it
    return [{
      ...nodes[0],
      position: { x: 0, y: 0 }
    }];
  }

  // Create simulation nodes with current positions or initialize randomly
  const simulationNodes = nodes.map((node) => {
    // If node has no position or is at origin, give it a random starting position
    // This helps the simulation converge better
    const hasValidPosition = node.position.x !== 0 || node.position.y !== 0;
    
    return {
      id: node.id,
      x: hasValidPosition ? node.position.x : (Math.random() - 0.5) * 1000,
      y: hasValidPosition ? node.position.y : (Math.random() - 0.5) * 1000,
      width: node.width || 300,
      height: node.height || 150,
      // Store original node reference for later
      originalNode: node
    };
  });

  // Create simulation links with proper typing
  const simulationLinks = edges.map((edge) => ({
    source: edge.source,
    target: edge.target
  }));

  // Calculate optimal collision radius based on average node size
  const avgWidth = simulationNodes.reduce((sum, n) => sum + n.width, 0) / simulationNodes.length;
  const avgHeight = simulationNodes.reduce((sum, n) => sum + n.height, 0) / simulationNodes.length;
  const collisionRadius = Math.max(avgWidth, avgHeight) / 2 + spacing / 2;

  // Calculate link distance based on node count and spacing
  // More nodes = tighter layout, fewer nodes = more spread out
  const linkDistance = nodes.length > 20 
    ? spacing * 1.5 
    : nodes.length > 10 
      ? spacing * 2 
      : spacing * 2.5;

  // Calculate charge strength based on node count
  // More nodes = weaker repulsion to keep them together
  const chargeStrength = nodes.length > 20 
    ? -800 
    : nodes.length > 10 
      ? -1000 
      : -1200;

  // Run force simulation
  const simulation = forceSimulation(simulationNodes as any)
    // Link force - keeps connected nodes at desired distance
    .force('link', forceLink(simulationLinks)
      .id((d: any) => d.id)
      .distance(linkDistance)
      .strength(1) // Strong links to maintain structure
    )
    // Charge force - nodes repel each other
    .force('charge', forceManyBody()
      .strength(chargeStrength)
      .distanceMax(1000) // Limit repulsion range for performance
    )
    // Center force - keeps the graph centered
    .force('center', forceCenter(0, 0)
      .strength(0.05) // Gentle centering
    )
    // Collision force - prevents node overlaps
    .force('collision', forceCollide()
      .radius(collisionRadius)
      .strength(0.8) // Strong collision avoidance
      .iterations(3) // Multiple iterations for better collision resolution
    );

  // Run simulation synchronously with adaptive iterations
  // More nodes = more iterations needed for convergence
  const iterations = Math.min(500, Math.max(300, nodes.length * 5));
  
  simulation.stop();
  for (let i = 0; i < iterations; i++) {
    simulation.tick();
    
    // Early stopping if simulation has converged (alpha < threshold)
    if (simulation.alpha() < 0.001) {
      break;
    }
  }

  // Update node positions with the simulated positions
  return nodes.map((node) => {
    const simNode = simulationNodes.find((n) => n.id === node.id);
    
    if (!simNode) {
      console.warn(`Node ${node.id} not found in simulation results`);
      return node;
    }
    
    return {
      ...node,
      position: {
        x: Math.round(simNode.x), // Round to avoid sub-pixel rendering
        y: Math.round(simNode.y)
      }
    };
  });
}

/**
 * Arrange child nodes in a circular pattern around parent
 */
export function arrangeChildrenCircular(
  parentNode: Node,
  childNodes: Node[],
  radius: number = 280
): Node[] {
  if (childNodes.length === 0) return [];

  const angleStep = (2 * Math.PI) / childNodes.length;

  return childNodes.map((child, index) => {
    const angle = index * angleStep - Math.PI / 2; // Start from top
    
    return {
      ...child,
      position: {
        x: parentNode.position.x + Math.cos(angle) * radius,
        y: parentNode.position.y + Math.sin(angle) * radius
      }
    };
  });
}

/**
 * Apply hierarchical radial (mind map) layout
 * Root node at center, children orbit around parents in concentric circles
 */
export function radialMindMapLayout(
  nodes: Node[],
  edges: Edge[],
  config: Partial<LayoutConfig> = {}
): Node[] {
  const { spacing = 100 } = { ...DEFAULT_CONFIG, ...config };
  
  // Find root nodes (nodes with no incoming edges)
  const rootNodes = nodes.filter(node => 
    !edges.some(edge => edge.target === node.id)
  );
  
  if (rootNodes.length === 0) {
    console.warn('No root nodes found for radial layout');
    return nodes;
  }
  
  // Build parent-child map
  const childrenMap = new Map<string, string[]>();
  edges.forEach(edge => {
    if (!childrenMap.has(edge.source)) {
      childrenMap.set(edge.source, []);
    }
    childrenMap.get(edge.source)!.push(edge.target);
  });
  
  // Calculate positions for each subtree
  const positionedNodes = new Map<string, { x: number; y: number }>();
  
  // If multiple roots, arrange them in a circle first
  const rootRadius = rootNodes.length > 1 ? 300 : 0;
  const rootAngleStep = rootNodes.length > 1 ? (2 * Math.PI) / rootNodes.length : 0;
  
  rootNodes.forEach((rootNode, rootIndex) => {
    const rootAngle = rootIndex * rootAngleStep;
    const rootX = rootNodes.length > 1 ? Math.cos(rootAngle) * rootRadius : 0;
    const rootY = rootNodes.length > 1 ? Math.sin(rootAngle) * rootRadius : 0;
    
    // Position root
    positionedNodes.set(rootNode.id, { x: rootX, y: rootY });
    
    // Recursively position children
    positionSubtree(rootNode.id, { x: rootX, y: rootY }, childrenMap, positionedNodes, spacing);
  });
  
  // Update node positions
  return nodes.map(node => {
    const position = positionedNodes.get(node.id);
    if (position) {
      return {
        ...node,
        position: { x: position.x, y: position.y }
      };
    }
    return node;
  });
}

/**
 * Recursively position a subtree in radial layout
 */
function positionSubtree(
  nodeId: string,
  parentPos: { x: number; y: number },
  childrenMap: Map<string, string[]>,
  positionedNodes: Map<string, { x: number; y: number }>,
  baseSpacing: number,
  level: number = 1
): void {
  const children = childrenMap.get(nodeId) || [];
  if (children.length === 0) return;
  
  // Calculate radius for this level (increases with depth)
  const radius = baseSpacing * 2.5 * level;
  
  // Calculate angle range for this subtree
  // For root level, use full circle; for deeper levels, use a sector
  const angleRange = level === 1 ? 2 * Math.PI : Math.PI * 1.5;
  const angleStep = angleRange / Math.max(children.length, 1);
  
  // Calculate starting angle based on parent position
  const parentAngle = Math.atan2(parentPos.y, parentPos.x);
  const startAngle = level === 1 ? -Math.PI / 2 : parentAngle - angleRange / 2;
  
  children.forEach((childId, index) => {
    const angle = startAngle + index * angleStep;
    
    const childX = parentPos.x + Math.cos(angle) * radius;
    const childY = parentPos.y + Math.sin(angle) * radius;
    
    positionedNodes.set(childId, { x: childX, y: childY });
    
    // Recursively position grandchildren
    positionSubtree(childId, { x: childX, y: childY }, childrenMap, positionedNodes, baseSpacing, level + 1);
  });
}

/**
 * Apply layout algorithm to nodes
 */
export function applyLayout(
  nodes: Node[],
  edges: Edge[],
  config: LayoutConfig = DEFAULT_CONFIG
): Node[] {
  try {
    switch (config.algorithm) {
      case 'force':
        return forceDirectedLayout(nodes, edges, config);
      case 'tree':
        return treeLayout(nodes, edges, config);
      case 'circular':
        return radialMindMapLayout(nodes, edges, config);
      default:
        return nodes;
    }
  } catch (error) {
    console.error('Layout failed:', error);
    return nodes; // Return original positions on error
  }
}

/**
 * Check if nodes overlap
 */
export function detectOverlap(node1: Node, node2: Node): boolean {
  const padding = 20;
  const width1 = node1.width || 300;
  const height1 = node1.height || 150;
  const width2 = node2.width || 300;
  const height2 = node2.height || 150;

  return !(
    node1.position.x + width1 + padding < node2.position.x ||
    node1.position.x > node2.position.x + width2 + padding ||
    node1.position.y + height1 + padding < node2.position.y ||
    node1.position.y > node2.position.y + height2 + padding
  );
}

/**
 * Get bounding box of all nodes
 */
export function getNodesBoundingBox(nodes: Node[]): {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
  width: number;
  height: number;
} {
  if (nodes.length === 0) {
    return { minX: 0, minY: 0, maxX: 0, maxY: 0, width: 0, height: 0 };
  }

  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;

  nodes.forEach((node) => {
    const width = node.width || 300;
    const height = node.height || 150;
    
    minX = Math.min(minX, node.position.x);
    minY = Math.min(minY, node.position.y);
    maxX = Math.max(maxX, node.position.x + width);
    maxY = Math.max(maxY, node.position.y + height);
  });

  return {
    minX,
    minY,
    maxX,
    maxY,
    width: maxX - minX,
    height: maxY - minY
  };
}
