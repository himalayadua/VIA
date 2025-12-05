/**
 * Unit tests for Refly Layout Utilities
 * 
 * Tests smart positioning, hierarchical layouts, and node utilities
 * for the Via Canvas layout system.
 */
import { describe, it, expect, beforeEach } from 'vitest';
import { Node, Edge } from 'reactflow';
import { getRightmostPosition, getNodeAbsolutePosition } from '../../../src/utils/smartPositioning';
import { layoutBranch } from '../../../src/utils/advancedLayout';
import { getNodeLevel, getRootNodes, getNodeDefaultMetadata } from '../../../src/utils/nodeUtilities';
import { CardType } from '../../../src/types/cardTypes';
import { radialMindMapLayout, forceDirectedLayout } from '../../../src/utils/layoutAlgorithms';

describe('Smart Positioning', () => {
  describe('getRightmostPosition', () => {
    it('should position first card at default location', () => {
      const sourceNodes: Node[] = [];
      const allNodes: Node[] = [];
      const edges: Edge[] = [];

      const position = getRightmostPosition(sourceNodes, allNodes, edges);

      expect(position.x).toBeGreaterThan(0);
      expect(position.y).toBeGreaterThan(0);
    });

    it('should position card to the right of source card', () => {
      const sourceNode: Node = {
        id: '1',
        type: 'richText',
        position: { x: 100, y: 100 },
        data: { label: 'Source' }
      };

      const position = getRightmostPosition([sourceNode], [sourceNode], []);

      expect(position.x).toBeGreaterThan(sourceNode.position.x);
      expect(position.y).toBe(sourceNode.position.y);
    });

    it('should prevent overlaps with existing cards', () => {
      const sourceNode: Node = {
        id: '1',
        type: 'richText',
        position: { x: 100, y: 100 },
        data: { label: 'Source' }
      };

      const existingNode: Node = {
        id: '2',
        type: 'richText',
        position: { x: 500, y: 100 },
        data: { label: 'Existing' }
      };

      const position = getRightmostPosition(
        [sourceNode],
        [sourceNode, existingNode],
        []
      );

      // Should be positioned after the existing node
      expect(position.x).toBeGreaterThan(existingNode.position.x);
    });

    it('should detect and use gaps between cards', () => {
      const sourceNode: Node = {
        id: '1',
        type: 'richText',
        position: { x: 100, y: 100 },
        data: { label: 'Source' }
      };

      const farNode: Node = {
        id: '2',
        type: 'richText',
        position: { x: 1000, y: 100 }, // Large gap
        data: { label: 'Far' }
      };

      const position = getRightmostPosition(
        [sourceNode],
        [sourceNode, farNode],
        []
      );

      // Should use gap instead of going all the way to the right
      expect(position.x).toBeLessThan(farNode.position.x);
      expect(position.x).toBeGreaterThan(sourceNode.position.x);
    });

    it('should handle multiple source nodes', () => {
      const sourceNodes: Node[] = [
        {
          id: '1',
          type: 'richText',
          position: { x: 100, y: 100 },
          data: { label: 'Source 1' }
        },
        {
          id: '2',
          type: 'richText',
          position: { x: 100, y: 300 },
          data: { label: 'Source 2' }
        }
      ];

      const position = getRightmostPosition(sourceNodes, sourceNodes, []);

      // Should position relative to rightmost source
      expect(position.x).toBeGreaterThan(100);
    });

    it('should handle empty canvas', () => {
      const position = getRightmostPosition([], [], []);

      expect(position.x).toBeGreaterThan(0);
      expect(position.y).toBeGreaterThan(0);
    });
  });

  describe('getNodeAbsolutePosition', () => {
    it('should return node position for root node', () => {
      const node: Node = {
        id: '1',
        type: 'richText',
        position: { x: 100, y: 200 },
        data: { label: 'Root' }
      };

      const position = getNodeAbsolutePosition(node, [node]);

      expect(position.x).toBe(100);
      expect(position.y).toBe(200);
    });

    it('should calculate absolute position for child node', () => {
      const parentNode: Node = {
        id: '1',
        type: 'richText',
        position: { x: 100, y: 100 },
        data: { label: 'Parent' }
      };

      const childNode: Node = {
        id: '2',
        type: 'richText',
        position: { x: 50, y: 50 }, // Relative to parent
        data: { label: 'Child', parentId: '1' }
      };

      const position = getNodeAbsolutePosition(childNode, [parentNode, childNode]);

      expect(position.x).toBe(150); // 100 + 50
      expect(position.y).toBe(150); // 100 + 50
    });
  });
});

describe('Hierarchical Layout', () => {
  describe('layoutBranch', () => {
    it('should layout single node', () => {
      const node: Node = {
        id: '1',
        type: 'richText',
        position: { x: 0, y: 0 },
        data: { label: 'Single' }
      };

      const rootNode: Node = {
        id: 'root',
        type: 'richText',
        position: { x: 100, y: 100 },
        data: { label: 'Root' }
      };

      const layouted = layoutBranch([node], [], [rootNode]);

      expect(layouted).toHaveLength(1);
      expect(layouted[0].position.x).toBeGreaterThan(0);
      expect(layouted[0].position.y).toBeGreaterThan(0);
    });

    it('should layout linear hierarchy', () => {
      const nodes: Node[] = [
        {
          id: '1',
          type: 'richText',
          position: { x: 0, y: 0 },
          data: { label: 'Node 1' }
        },
        {
          id: '2',
          type: 'richText',
          position: { x: 0, y: 0 },
          data: { label: 'Node 2' }
        },
        {
          id: '3',
          type: 'richText',
          position: { x: 0, y: 0 },
          data: { label: 'Node 3' }
        }
      ];

      const edges: Edge[] = [
        { id: 'e1-2', source: '1', target: '2' },
        { id: 'e2-3', source: '2', target: '3' }
      ];

      const rootNode: Node = {
        id: 'root',
        type: 'richText',
        position: { x: 100, y: 100 },
        data: { label: 'Root' }
      };

      const layouted = layoutBranch(nodes, edges, [rootNode]);

      expect(layouted).toHaveLength(3);
      
      // Nodes should be positioned horizontally
      expect(layouted[1].position.x).toBeGreaterThan(layouted[0].position.x);
      expect(layouted[2].position.x).toBeGreaterThan(layouted[1].position.x);
    });

    it('should layout tree hierarchy', () => {
      const nodes: Node[] = [
        {
          id: '1',
          type: 'richText',
          position: { x: 0, y: 0 },
          data: { label: 'Parent' }
        },
        {
          id: '2',
          type: 'richText',
          position: { x: 0, y: 0 },
          data: { label: 'Child 1' }
        },
        {
          id: '3',
          type: 'richText',
          position: { x: 0, y: 0 },
          data: { label: 'Child 2' }
        },
        {
          id: '4',
          type: 'richText',
          position: { x: 0, y: 0 },
          data: { label: 'Child 3' }
        }
      ];

      const edges: Edge[] = [
        { id: 'e1-2', source: '1', target: '2' },
        { id: 'e1-3', source: '1', target: '3' },
        { id: 'e1-4', source: '1', target: '4' }
      ];

      const rootNode: Node = {
        id: 'root',
        type: 'richText',
        position: { x: 100, y: 100 },
        data: { label: 'Root' }
      };

      const layouted = layoutBranch(nodes, edges, [rootNode]);

      expect(layouted).toHaveLength(4);
      
      // Children should be spread vertically
      const childPositions = layouted.slice(1).map(n => n.position.y);
      const uniqueYPositions = new Set(childPositions);
      expect(uniqueYPositions.size).toBeGreaterThan(1);
    });

    it('should handle empty node list', () => {
      const layouted = layoutBranch([], [], []);
      expect(layouted).toHaveLength(0);
    });

    it('should preserve node data', () => {
      const node: Node = {
        id: '1',
        type: 'richText',
        position: { x: 0, y: 0 },
        data: { 
          label: 'Test',
          title: 'Test Title',
          content: 'Test Content'
        }
      };

      const rootNode: Node = {
        id: 'root',
        type: 'richText',
        position: { x: 100, y: 100 },
        data: { label: 'Root' }
      };

      const layouted = layoutBranch([node], [], [rootNode]);

      expect(layouted[0].data.label).toBe('Test');
      expect(layouted[0].data.title).toBe('Test Title');
      expect(layouted[0].data.content).toBe('Test Content');
    });
  });
});

describe('Node Utilities', () => {
  describe('getNodeLevel', () => {
    it('should return 0 for root nodes', () => {
      const rootNode: Node = {
        id: '1',
        type: 'richText',
        position: { x: 100, y: 100 },
        data: { label: 'Root' }
      };

      const level = getNodeLevel('1', [rootNode], [], [rootNode]);

      expect(level).toBe(0);
    });

    it('should return 1 for direct children', () => {
      const rootNode: Node = {
        id: '1',
        type: 'richText',
        position: { x: 100, y: 100 },
        data: { label: 'Root' }
      };

      const childNode: Node = {
        id: '2',
        type: 'richText',
        position: { x: 500, y: 100 },
        data: { label: 'Child' }
      };

      const edge: Edge = {
        id: 'e1-2',
        source: '1',
        target: '2'
      };

      const level = getNodeLevel('2', [rootNode, childNode], [edge], [rootNode]);

      expect(level).toBe(1);
    });

    it('should return correct level for deep hierarchy', () => {
      const nodes: Node[] = [
        {
          id: '1',
          type: 'richText',
          position: { x: 100, y: 100 },
          data: { label: 'Root' }
        },
        {
          id: '2',
          type: 'richText',
          position: { x: 500, y: 100 },
          data: { label: 'Level 1' }
        },
        {
          id: '3',
          type: 'richText',
          position: { x: 900, y: 100 },
          data: { label: 'Level 2' }
        },
        {
          id: '4',
          type: 'richText',
          position: { x: 1300, y: 100 },
          data: { label: 'Level 3' }
        }
      ];

      const edges: Edge[] = [
        { id: 'e1-2', source: '1', target: '2' },
        { id: 'e2-3', source: '2', target: '3' },
        { id: 'e3-4', source: '3', target: '4' }
      ];

      const level = getNodeLevel('4', nodes, edges, [nodes[0]]);

      expect(level).toBe(3);
    });

    it('should return -1 for non-existent node', () => {
      const rootNode: Node = {
        id: '1',
        type: 'richText',
        position: { x: 100, y: 100 },
        data: { label: 'Root' }
      };

      const level = getNodeLevel('999', [rootNode], [], [rootNode]);

      expect(level).toBe(-1);
    });

    it('should handle disconnected nodes', () => {
      const rootNode: Node = {
        id: '1',
        type: 'richText',
        position: { x: 100, y: 100 },
        data: { label: 'Root' }
      };

      const disconnectedNode: Node = {
        id: '2',
        type: 'richText',
        position: { x: 500, y: 100 },
        data: { label: 'Disconnected' }
      };

      const level = getNodeLevel('2', [rootNode, disconnectedNode], [], [rootNode]);

      expect(level).toBe(-1);
    });
  });

  describe('getRootNodes', () => {
    it('should return all nodes when no edges', () => {
      const nodes: Node[] = [
        {
          id: '1',
          type: 'richText',
          position: { x: 100, y: 100 },
          data: { label: 'Node 1' }
        },
        {
          id: '2',
          type: 'richText',
          position: { x: 500, y: 100 },
          data: { label: 'Node 2' }
        }
      ];

      const roots = getRootNodes(nodes, []);

      expect(roots).toHaveLength(2);
    });

    it('should return only nodes with no incoming edges', () => {
      const nodes: Node[] = [
        {
          id: '1',
          type: 'richText',
          position: { x: 100, y: 100 },
          data: { label: 'Root' }
        },
        {
          id: '2',
          type: 'richText',
          position: { x: 500, y: 100 },
          data: { label: 'Child' }
        }
      ];

      const edges: Edge[] = [
        { id: 'e1-2', source: '1', target: '2' }
      ];

      const roots = getRootNodes(nodes, edges);

      expect(roots).toHaveLength(1);
      expect(roots[0].id).toBe('1');
    });

    it('should handle multiple root nodes', () => {
      const nodes: Node[] = [
        {
          id: '1',
          type: 'richText',
          position: { x: 100, y: 100 },
          data: { label: 'Root 1' }
        },
        {
          id: '2',
          type: 'richText',
          position: { x: 100, y: 300 },
          data: { label: 'Root 2' }
        },
        {
          id: '3',
          type: 'richText',
          position: { x: 500, y: 100 },
          data: { label: 'Child of 1' }
        },
        {
          id: '4',
          type: 'richText',
          position: { x: 500, y: 300 },
          data: { label: 'Child of 2' }
        }
      ];

      const edges: Edge[] = [
        { id: 'e1-3', source: '1', target: '3' },
        { id: 'e2-4', source: '2', target: '4' }
      ];

      const roots = getRootNodes(nodes, edges);

      expect(roots).toHaveLength(2);
      expect(roots.map(n => n.id)).toContain('1');
      expect(roots.map(n => n.id)).toContain('2');
    });

    it('should handle empty node list', () => {
      const roots = getRootNodes([], []);
      expect(roots).toHaveLength(0);
    });
  });

  describe('getNodeDefaultMetadata', () => {
    it('should return metadata for rich_text type', () => {
      const metadata = getNodeDefaultMetadata(CardType.RICH_TEXT);

      expect(metadata).toHaveProperty('sizeMode');
      expect(metadata.sizeMode).toBe('adaptive');
      expect(metadata).toHaveProperty('content');
      expect(metadata).toHaveProperty('title');
    });

    it('should return metadata for todo type', () => {
      const metadata = getNodeDefaultMetadata(CardType.TODO);

      expect(metadata).toHaveProperty('sizeMode');
      expect(metadata).toHaveProperty('completed');
      expect(metadata.completed).toBe(false);
      expect(metadata).toHaveProperty('items');
      expect(Array.isArray(metadata.items)).toBe(true);
    });

    it('should return metadata for video type', () => {
      const metadata = getNodeDefaultMetadata(CardType.VIDEO);

      expect(metadata).toHaveProperty('sizeMode');
      expect(metadata).toHaveProperty('url');
      expect(metadata).toHaveProperty('title');
      expect(metadata).toHaveProperty('thumbnail');
    });

    it('should return metadata for link type', () => {
      const metadata = getNodeDefaultMetadata(CardType.LINK);

      expect(metadata).toHaveProperty('sizeMode');
      expect(metadata).toHaveProperty('url');
      expect(metadata).toHaveProperty('title');
      expect(metadata).toHaveProperty('description');
    });

    it('should return metadata for reminder type', () => {
      const metadata = getNodeDefaultMetadata(CardType.REMINDER);

      expect(metadata).toHaveProperty('sizeMode');
      expect(metadata).toHaveProperty('text');
      expect(metadata).toHaveProperty('dueDate');
      expect(metadata).toHaveProperty('completed');
      expect(metadata.completed).toBe(false);
    });

    it('should return base metadata for unknown type', () => {
      const metadata = getNodeDefaultMetadata(null as any);

      expect(metadata).toEqual({});
    });
  });
});

describe('Performance Tests', () => {
  it('should calculate position for single card in <10ms', () => {
    const sourceNode: Node = {
      id: '1',
      type: 'richText',
      position: { x: 100, y: 100 },
      data: { label: 'Source' }
    };

    const start = performance.now();
    getRightmostPosition([sourceNode], [sourceNode], []);
    const end = performance.now();

    expect(end - start).toBeLessThan(10);
  });

  it('should calculate position with 100 cards in <100ms', () => {
    const nodes: Node[] = Array.from({ length: 100 }, (_, i) => ({
      id: `${i}`,
      type: 'richText',
      position: { x: i * 400, y: 100 },
      data: { label: `Node ${i}` }
    }));

    const start = performance.now();
    getRightmostPosition([nodes[0]], nodes, []);
    const end = performance.now();

    expect(end - start).toBeLessThan(100);
  });

  it('should layout 20 nodes in <50ms', () => {
    const nodes: Node[] = Array.from({ length: 20 }, (_, i) => ({
      id: `${i}`,
      type: 'richText',
      position: { x: 0, y: 0 },
      data: { label: `Node ${i}` }
    }));

    const edges: Edge[] = Array.from({ length: 19 }, (_, i) => ({
      id: `e${i}-${i + 1}`,
      source: `${i}`,
      target: `${i + 1}`
    }));

    const rootNode: Node = {
      id: 'root',
      type: 'richText',
      position: { x: 100, y: 100 },
      data: { label: 'Root' }
    };

    const start = performance.now();
    layoutBranch(nodes, edges, [rootNode]);
    const end = performance.now();

    expect(end - start).toBeLessThan(50);
  });

  it('should find root nodes in large graph in <10ms', () => {
    const nodes: Node[] = Array.from({ length: 100 }, (_, i) => ({
      id: `${i}`,
      type: 'richText',
      position: { x: i * 400, y: 100 },
      data: { label: `Node ${i}` }
    }));

    const edges: Edge[] = Array.from({ length: 99 }, (_, i) => ({
      id: `e${i}-${i + 1}`,
      source: `${i}`,
      target: `${i + 1}`
    }));

    const start = performance.now();
    getRootNodes(nodes, edges);
    const end = performance.now();

    expect(end - start).toBeLessThan(10);
  });
});

describe('Edge Cases', () => {
  it('should handle nodes with same position', () => {
    const nodes: Node[] = [
      {
        id: '1',
        type: 'richText',
        position: { x: 100, y: 100 },
        data: { label: 'Node 1' }
      },
      {
        id: '2',
        type: 'richText',
        position: { x: 100, y: 100 }, // Same position
        data: { label: 'Node 2' }
      }
    ];

    const position = getRightmostPosition([nodes[0]], nodes, []);

    expect(position.x).toBeGreaterThan(100);
  });

  it('should handle negative positions', () => {
    const node: Node = {
      id: '1',
      type: 'richText',
      position: { x: -100, y: -100 },
      data: { label: 'Negative' }
    };

    const position = getRightmostPosition([node], [node], []);

    expect(position.x).toBeGreaterThan(-100);
  });

  it('should handle very large positions', () => {
    const node: Node = {
      id: '1',
      type: 'richText',
      position: { x: 10000, y: 10000 },
      data: { label: 'Far' }
    };

    const position = getRightmostPosition([node], [node], []);

    expect(position.x).toBeGreaterThan(10000);
  });

  it('should handle circular references in hierarchy', () => {
    const nodes: Node[] = [
      {
        id: '1',
        type: 'richText',
        position: { x: 100, y: 100 },
        data: { label: 'Node 1' }
      },
      {
        id: '2',
        type: 'richText',
        position: { x: 500, y: 100 },
        data: { label: 'Node 2' }
      }
    ];

    const edges: Edge[] = [
      { id: 'e1-2', source: '1', target: '2' },
      { id: 'e2-1', source: '2', target: '1' } // Circular
    ];

    // Should not crash or hang
    const level = getNodeLevel('2', nodes, edges, [nodes[0]]);
    expect(level).toBeGreaterThanOrEqual(-1);
  });

  it('should handle nodes without data', () => {
    const node: Node = {
      id: '1',
      type: 'richText',
      position: { x: 100, y: 100 },
      data: {}
    };

    const position = getRightmostPosition([node], [node], []);

    expect(position).toBeDefined();
    expect(position.x).toBeGreaterThan(0);
    expect(position.y).toBeGreaterThan(0);
  });
});


describe('Force-Directed Layout', () => {
  it('should handle single node', () => {
    const nodes: Node[] = [
      {
        id: '1',
        type: 'richText',
        position: { x: 100, y: 100 },
        data: { label: 'Single' }
      }
    ];

    const layouted = forceDirectedLayout(nodes, []);

    expect(layouted).toHaveLength(1);
    // Single node should be centered
    expect(layouted[0].position.x).toBe(0);
    expect(layouted[0].position.y).toBe(0);
  });

  it('should prevent node overlaps', () => {
    const nodes: Node[] = Array.from({ length: 10 }, (_, i) => ({
      id: `${i + 1}`,
      type: 'richText',
      position: { x: 0, y: 0 }, // All start at same position
      data: { label: `Node ${i + 1}` },
      width: 300,
      height: 150
    }));

    const edges: Edge[] = Array.from({ length: 9 }, (_, i) => ({
      id: `e${i}-${i + 1}`,
      source: `${i + 1}`,
      target: `${i + 2}`
    }));

    const layouted = forceDirectedLayout(nodes, edges);

    // Check that no two nodes overlap
    for (let i = 0; i < layouted.length; i++) {
      for (let j = i + 1; j < layouted.length; j++) {
        const node1 = layouted[i];
        const node2 = layouted[j];
        
        const distance = Math.sqrt(
          Math.pow(node1.position.x - node2.position.x, 2) +
          Math.pow(node1.position.y - node2.position.y, 2)
        );
        
        // Nodes should be at least 150px apart (collision radius)
        expect(distance).toBeGreaterThan(100);
      }
    }
  });

  it('should keep connected nodes closer together', () => {
    const nodes: Node[] = [
      { id: '1', type: 'richText', position: { x: 0, y: 0 }, data: { label: 'Node 1' } },
      { id: '2', type: 'richText', position: { x: 0, y: 0 }, data: { label: 'Node 2' } },
      { id: '3', type: 'richText', position: { x: 0, y: 0 }, data: { label: 'Node 3' } },
      { id: '4', type: 'richText', position: { x: 0, y: 0 }, data: { label: 'Node 4' } }
    ];

    const edges: Edge[] = [
      { id: 'e1-2', source: '1', target: '2' },
      { id: 'e2-3', source: '2', target: '3' }
      // Node 4 is disconnected
    ];

    const layouted = forceDirectedLayout(nodes, edges);

    // Calculate distances
    const dist12 = Math.sqrt(
      Math.pow(layouted[0].position.x - layouted[1].position.x, 2) +
      Math.pow(layouted[0].position.y - layouted[1].position.y, 2)
    );

    const dist14 = Math.sqrt(
      Math.pow(layouted[0].position.x - layouted[3].position.x, 2) +
      Math.pow(layouted[0].position.y - layouted[3].position.y, 2)
    );

    // Connected nodes (1-2) should be closer than disconnected nodes (1-4)
    expect(dist12).toBeLessThan(dist14);
  });

  it('should center the graph around origin', () => {
    const nodes: Node[] = Array.from({ length: 5 }, (_, i) => ({
      id: `${i + 1}`,
      type: 'richText',
      position: { x: 0, y: 0 },
      data: { label: `Node ${i + 1}` }
    }));

    const edges: Edge[] = [
      { id: 'e1-2', source: '1', target: '2' },
      { id: 'e1-3', source: '1', target: '3' },
      { id: 'e1-4', source: '1', target: '4' },
      { id: 'e1-5', source: '1', target: '5' }
    ];

    const layouted = forceDirectedLayout(nodes, edges);

    // Calculate center of mass
    const centerX = layouted.reduce((sum, n) => sum + n.position.x, 0) / layouted.length;
    const centerY = layouted.reduce((sum, n) => sum + n.position.y, 0) / layouted.length;

    // Center should be close to origin
    expect(Math.abs(centerX)).toBeLessThan(100);
    expect(Math.abs(centerY)).toBeLessThan(100);
  });

  it('should handle empty node list', () => {
    const layouted = forceDirectedLayout([], []);
    expect(layouted).toHaveLength(0);
  });

  it('should preserve node data', () => {
    const nodes: Node[] = [
      {
        id: '1',
        type: 'richText',
        position: { x: 0, y: 0 },
        data: { 
          label: 'Test',
          title: 'Test Title',
          customField: 'Custom Value'
        }
      }
    ];

    const layouted = forceDirectedLayout(nodes, []);

    expect(layouted[0].data.label).toBe('Test');
    expect(layouted[0].data.title).toBe('Test Title');
    expect(layouted[0].data.customField).toBe('Custom Value');
  });

  it('should handle nodes with different sizes', () => {
    const nodes: Node[] = [
      {
        id: '1',
        type: 'richText',
        position: { x: 0, y: 0 },
        data: { label: 'Small' },
        width: 200,
        height: 100
      },
      {
        id: '2',
        type: 'richText',
        position: { x: 0, y: 0 },
        data: { label: 'Large' },
        width: 400,
        height: 300
      }
    ];

    const edges: Edge[] = [
      { id: 'e1-2', source: '1', target: '2' }
    ];

    const layouted = forceDirectedLayout(nodes, edges);

    expect(layouted).toHaveLength(2);
    // Should not overlap despite different sizes
    const distance = Math.sqrt(
      Math.pow(layouted[0].position.x - layouted[1].position.x, 2) +
      Math.pow(layouted[0].position.y - layouted[1].position.y, 2)
    );
    expect(distance).toBeGreaterThan(100);
  });

  it('should handle complex graph structures', () => {
    // Create a more complex graph with multiple clusters
    const nodes: Node[] = Array.from({ length: 15 }, (_, i) => ({
      id: `${i + 1}`,
      type: 'richText',
      position: { x: 0, y: 0 },
      data: { label: `Node ${i + 1}` }
    }));

    const edges: Edge[] = [
      // Cluster 1 (nodes 1-5)
      { id: 'e1-2', source: '1', target: '2' },
      { id: 'e1-3', source: '1', target: '3' },
      { id: 'e1-4', source: '1', target: '4' },
      { id: 'e1-5', source: '1', target: '5' },
      // Cluster 2 (nodes 6-10)
      { id: 'e6-7', source: '6', target: '7' },
      { id: 'e6-8', source: '6', target: '8' },
      { id: 'e6-9', source: '6', target: '9' },
      { id: 'e6-10', source: '6', target: '10' },
      // Bridge between clusters
      { id: 'e5-6', source: '5', target: '6' },
      // Cluster 3 (nodes 11-15)
      { id: 'e11-12', source: '11', target: '12' },
      { id: 'e11-13', source: '11', target: '13' },
      { id: 'e11-14', source: '11', target: '14' },
      { id: 'e11-15', source: '11', target: '15' },
      // Bridge to cluster 3
      { id: 'e10-11', source: '10', target: '11' }
    ];

    const layouted = forceDirectedLayout(nodes, edges);

    expect(layouted).toHaveLength(15);
    
    // All nodes should have valid positions
    layouted.forEach(node => {
      expect(isFinite(node.position.x)).toBe(true);
      expect(isFinite(node.position.y)).toBe(true);
    });

    // No overlaps
    for (let i = 0; i < layouted.length; i++) {
      for (let j = i + 1; j < layouted.length; j++) {
        const distance = Math.sqrt(
          Math.pow(layouted[i].position.x - layouted[j].position.x, 2) +
          Math.pow(layouted[i].position.y - layouted[j].position.y, 2)
        );
        expect(distance).toBeGreaterThan(50);
      }
    }
  });

  it('should adapt to different node counts', () => {
    // Test with small graph
    const smallNodes: Node[] = Array.from({ length: 5 }, (_, i) => ({
      id: `${i + 1}`,
      type: 'richText',
      position: { x: 0, y: 0 },
      data: { label: `Node ${i + 1}` }
    }));

    const smallEdges: Edge[] = [
      { id: 'e1-2', source: '1', target: '2' },
      { id: 'e2-3', source: '2', target: '3' },
      { id: 'e3-4', source: '3', target: '4' },
      { id: 'e4-5', source: '4', target: '5' }
    ];

    const smallLayouted = forceDirectedLayout(smallNodes, smallEdges);
    expect(smallLayouted).toHaveLength(5);

    // Test with large graph
    const largeNodes: Node[] = Array.from({ length: 30 }, (_, i) => ({
      id: `${i + 1}`,
      type: 'richText',
      position: { x: 0, y: 0 },
      data: { label: `Node ${i + 1}` }
    }));

    const largeEdges: Edge[] = Array.from({ length: 29 }, (_, i) => ({
      id: `e${i}-${i + 1}`,
      source: `${i + 1}`,
      target: `${i + 2}`
    }));

    const largeLayouted = forceDirectedLayout(largeNodes, largeEdges);
    expect(largeLayouted).toHaveLength(30);

    // Both should produce valid layouts
    smallLayouted.forEach(node => {
      expect(isFinite(node.position.x)).toBe(true);
      expect(isFinite(node.position.y)).toBe(true);
    });

    largeLayouted.forEach(node => {
      expect(isFinite(node.position.x)).toBe(true);
      expect(isFinite(node.position.y)).toBe(true);
    });
  });
});

describe('Radial Mind Map Layout', () => {
  it('should position root node at center', () => {
    const nodes: Node[] = [
      {
        id: '1',
        type: 'richText',
        position: { x: 0, y: 0 },
        data: { label: 'Root' }
      }
    ];

    const layouted = radialMindMapLayout(nodes, []);

    expect(layouted[0].position.x).toBe(0);
    expect(layouted[0].position.y).toBe(0);
  });

  it('should arrange children in circle around parent', () => {
    const nodes: Node[] = [
      {
        id: '1',
        type: 'richText',
        position: { x: 0, y: 0 },
        data: { label: 'Parent' }
      },
      {
        id: '2',
        type: 'richText',
        position: { x: 0, y: 0 },
        data: { label: 'Child 1' }
      },
      {
        id: '3',
        type: 'richText',
        position: { x: 0, y: 0 },
        data: { label: 'Child 2' }
      },
      {
        id: '4',
        type: 'richText',
        position: { x: 0, y: 0 },
        data: { label: 'Child 3' }
      }
    ];

    const edges: Edge[] = [
      { id: 'e1-2', source: '1', target: '2' },
      { id: 'e1-3', source: '1', target: '3' },
      { id: 'e1-4', source: '1', target: '4' }
    ];

    const layouted = radialMindMapLayout(nodes, edges);

    // Parent should be at center
    expect(layouted[0].position.x).toBe(0);
    expect(layouted[0].position.y).toBe(0);

    // Children should be arranged in circle
    const children = layouted.slice(1);
    children.forEach(child => {
      const distance = Math.sqrt(
        Math.pow(child.position.x, 2) + Math.pow(child.position.y, 2)
      );
      // All children should be approximately same distance from parent
      expect(distance).toBeGreaterThan(200);
      expect(distance).toBeLessThan(300);
    });

    // Children should have different positions
    const positions = children.map(c => `${c.position.x},${c.position.y}`);
    const uniquePositions = new Set(positions);
    expect(uniquePositions.size).toBe(3);
  });

  it('should create concentric circles for multiple levels', () => {
    const nodes: Node[] = [
      {
        id: '1',
        type: 'richText',
        position: { x: 0, y: 0 },
        data: { label: 'Root' }
      },
      {
        id: '2',
        type: 'richText',
        position: { x: 0, y: 0 },
        data: { label: 'Level 1 - Child 1' }
      },
      {
        id: '3',
        type: 'richText',
        position: { x: 0, y: 0 },
        data: { label: 'Level 1 - Child 2' }
      },
      {
        id: '4',
        type: 'richText',
        position: { x: 0, y: 0 },
        data: { label: 'Level 2 - Grandchild 1' }
      },
      {
        id: '5',
        type: 'richText',
        position: { x: 0, y: 0 },
        data: { label: 'Level 2 - Grandchild 2' }
      }
    ];

    const edges: Edge[] = [
      { id: 'e1-2', source: '1', target: '2' },
      { id: 'e1-3', source: '1', target: '3' },
      { id: 'e2-4', source: '2', target: '4' },
      { id: 'e2-5', source: '2', target: '5' }
    ];

    const layouted = radialMindMapLayout(nodes, edges);

    // Calculate distances from root
    const distances = layouted.slice(1).map(node => 
      Math.sqrt(Math.pow(node.position.x, 2) + Math.pow(node.position.y, 2))
    );

    // Level 1 children (nodes 2, 3)
    const level1Distances = distances.slice(0, 2);
    expect(level1Distances[0]).toBeGreaterThan(200);
    expect(level1Distances[0]).toBeLessThan(300);
    expect(Math.abs(level1Distances[0] - level1Distances[1])).toBeLessThan(50);

    // Level 2 children (nodes 4, 5) should be further from root
    const level2Distances = distances.slice(2);
    expect(level2Distances[0]).toBeGreaterThan(level1Distances[0]);
    expect(level2Distances[1]).toBeGreaterThan(level1Distances[1]);
  });

  it('should handle multiple root nodes', () => {
    const nodes: Node[] = [
      {
        id: '1',
        type: 'richText',
        position: { x: 0, y: 0 },
        data: { label: 'Root 1' }
      },
      {
        id: '2',
        type: 'richText',
        position: { x: 0, y: 0 },
        data: { label: 'Root 2' }
      },
      {
        id: '3',
        type: 'richText',
        position: { x: 0, y: 0 },
        data: { label: 'Child of Root 1' }
      },
      {
        id: '4',
        type: 'richText',
        position: { x: 0, y: 0 },
        data: { label: 'Child of Root 2' }
      }
    ];

    const edges: Edge[] = [
      { id: 'e1-3', source: '1', target: '3' },
      { id: 'e2-4', source: '2', target: '4' }
    ];

    const layouted = radialMindMapLayout(nodes, edges);

    // Both roots should be positioned (not at same location)
    const root1 = layouted.find(n => n.id === '1')!;
    const root2 = layouted.find(n => n.id === '2')!;
    
    const distance = Math.sqrt(
      Math.pow(root1.position.x - root2.position.x, 2) +
      Math.pow(root1.position.y - root2.position.y, 2)
    );
    
    expect(distance).toBeGreaterThan(100);
  });

  it('should prevent node overlaps', () => {
    const nodes: Node[] = Array.from({ length: 10 }, (_, i) => ({
      id: `${i + 1}`,
      type: 'richText',
      position: { x: 0, y: 0 },
      data: { label: `Node ${i + 1}` }
    }));

    const edges: Edge[] = Array.from({ length: 9 }, (_, i) => ({
      id: `e1-${i + 2}`,
      source: '1',
      target: `${i + 2}`
    }));

    const layouted = radialMindMapLayout(nodes, edges);

    // Check that no two nodes are too close
    for (let i = 1; i < layouted.length; i++) {
      for (let j = i + 1; j < layouted.length; j++) {
        const distance = Math.sqrt(
          Math.pow(layouted[i].position.x - layouted[j].position.x, 2) +
          Math.pow(layouted[i].position.y - layouted[j].position.y, 2)
        );
        // Nodes should be at least 100px apart
        expect(distance).toBeGreaterThan(100);
      }
    }
  });

  it('should handle deep hierarchies', () => {
    const nodes: Node[] = [
      { id: '1', type: 'richText', position: { x: 0, y: 0 }, data: { label: 'Level 0' } },
      { id: '2', type: 'richText', position: { x: 0, y: 0 }, data: { label: 'Level 1' } },
      { id: '3', type: 'richText', position: { x: 0, y: 0 }, data: { label: 'Level 2' } },
      { id: '4', type: 'richText', position: { x: 0, y: 0 }, data: { label: 'Level 3' } },
      { id: '5', type: 'richText', position: { x: 0, y: 0 }, data: { label: 'Level 4' } }
    ];

    const edges: Edge[] = [
      { id: 'e1-2', source: '1', target: '2' },
      { id: 'e2-3', source: '2', target: '3' },
      { id: 'e3-4', source: '3', target: '4' },
      { id: 'e4-5', source: '4', target: '5' }
    ];

    const layouted = radialMindMapLayout(nodes, edges);

    // Each level should be progressively further from root
    const distances = layouted.map(node =>
      Math.sqrt(Math.pow(node.position.x, 2) + Math.pow(node.position.y, 2))
    );

    for (let i = 1; i < distances.length; i++) {
      expect(distances[i]).toBeGreaterThan(distances[i - 1]);
    }
  });

  it('should handle empty node list', () => {
    const layouted = radialMindMapLayout([], []);
    expect(layouted).toHaveLength(0);
  });

  it('should preserve node data', () => {
    const nodes: Node[] = [
      {
        id: '1',
        type: 'richText',
        position: { x: 0, y: 0 },
        data: { 
          label: 'Test',
          title: 'Test Title',
          content: 'Test Content',
          customField: 'Custom Value'
        }
      }
    ];

    const layouted = radialMindMapLayout(nodes, []);

    expect(layouted[0].data.label).toBe('Test');
    expect(layouted[0].data.title).toBe('Test Title');
    expect(layouted[0].data.content).toBe('Test Content');
    expect(layouted[0].data.customField).toBe('Custom Value');
  });
});
