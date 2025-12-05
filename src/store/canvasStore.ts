import { create } from 'zustand';
import { Node, Edge, addEdge, applyNodeChanges, applyEdgeChanges, NodeChange, EdgeChange, Connection } from 'reactflow';
import { api } from '../lib/api';
import { applyLayout, LayoutAlgorithm, arrangeChildrenCircular } from '../utils/layoutAlgorithms';
import { buildHierarchy, moveNodeWithChildren } from '../utils/hierarchyUtils';
import { snapshotManager, Viewport } from '../utils/snapshotManager';
import { getRightmostPosition } from '../utils/smartPositioning';
import { layoutBranch } from '../utils/advancedLayout';
import { getNodeLevel, getRootNodes, getNodeDefaultMetadata } from '../utils/nodeUtilities';

interface CanvasState {
  currentCanvasId: string | null;
  canvasName: string;
  nodes: Node[];
  edges: Edge[];
  history: {
    past: { nodes: Node[]; edges: Edge[] }[];
    future: { nodes: Node[]; edges: Edge[] }[];
  };
  selectedNode: string | null;
  viewMode: 'mindmap' | 'temporal';
  sidebarWidth: number;
  collapseState: Record<string, boolean>; // nodeId -> isCollapsed
  modificationCount: number;
  lastSnapshotTime: number;
  reactFlowInstance: any | null;
  activeGrowOperations: Set<string>;
  learningActions: Record<string, {
    status: 'idle' | 'loading' | 'success' | 'error';
    result: any;
    error: string | null;
  }>;
  error: string | null;
  childLayoutMode: 'circular' | 'hierarchical'; // Layout preference for child nodes

  setCurrentCanvas: (id: string, name: string) => void;
  setNodes: (nodes: Node[]) => void;
  setEdges: (edges: Edge[]) => void;
  onNodesChange: (changes: NodeChange[]) => void;
  onEdgesChange: (changes: EdgeChange[]) => void;
  onConnect: (connection: Connection) => void;
  addNode: (node: Omit<Node, 'id'>) => Promise<void>;
  updateNode: (id: string, data: Partial<Node['data']>) => Promise<void>;
  deleteNode: (id: string) => Promise<void>;
  deleteEdge: (id: string) => Promise<void>;
  duplicateNode: (id: string) => Promise<void>;
  changeNodeType: (id: string, newType: string) => Promise<void>;
  addTagToNode: (nodeId: string, tag: string) => Promise<void>;
  removeTagFromNode: (nodeId: string, tag: string) => Promise<void>;
  createChildNode: (parentId: string) => Promise<void>;
  createSiblingNode: (nodeId: string) => Promise<void>;
  deleteSelectedNodes: () => Promise<void>;
  duplicateSelectedNodes: () => Promise<void>;
  clearSelection: () => void;
  getSelectedNodes: () => Node[];
  toggleCollapse: (nodeId: string) => void;
  setCollapseState: (nodeId: string, collapsed: boolean) => void;
  setSelectedNode: (id: string | null) => void;
  undo: () => void;
  redo: () => void;
  setViewMode: (mode: 'mindmap' | 'temporal') => void;
  setSidebarWidth: (width: number) => void;
  loadCanvas: (canvasId: string) => Promise<void>;
  saveCanvas: () => Promise<void>;
  exportCanvas: () => string;
  importCanvas: (data: string) => Promise<void>;
  applyLayoutToCanvas: (algorithm: LayoutAlgorithm) => Promise<void>;
  setReactFlowInstance: (instance: any) => void;
  triggerSnapshot: () => Promise<void>;
  incrementModificationCount: () => void;
  handleGrow: (nodeId: string) => Promise<void>;
  executeLearningAction: (action: string, nodeId: string) => Promise<void>;
  clearLearningAction: (actionId: string) => void;
  addCardsIncremental: (newCardIds: string[]) => Promise<void>;
  mergeCards: (sourceCardId: string, targetCardId: string) => Promise<void>;
  // Engagement tracking
  incrementReadCount: (cardId: string) => Promise<void>;
  handleComprehensiveLearn: (nodeId: string) => Promise<void>;
  updateEdgesForNode: (nodeId: string, readCount: number) => void;
  applyLearningClusterEffects: (parentNodeId: string) => void;
  // Layout utilities
  setChildLayoutMode: (mode: 'circular' | 'hierarchical') => void;
  getNodeLevel: (nodeId: string) => number;
  getRootNodes: () => Node[];
  optimizeLayout: () => Promise<void>;
}

export const useCanvasStore = create<CanvasState>((set, get) => ({
  currentCanvasId: null,
  canvasName: 'Untitled Canvas',
  nodes: [],
  edges: [],
  history: {
    past: [],
    future: []
  },
  selectedNode: null,
  viewMode: 'mindmap',
  sidebarWidth: 300,
  collapseState: {},
  modificationCount: 0,
  lastSnapshotTime: Date.now(),
  reactFlowInstance: null,
  activeGrowOperations: new Set<string>(),
  learningActions: {},
  error: null,
  childLayoutMode: 'circular', // Default to circular layout

  setCurrentCanvas: async (id, name) => {
    // Trigger snapshot before switching canvas
    await get().triggerSnapshot();
    set({ currentCanvasId: id, canvasName: name, modificationCount: 0 });
  },

  setNodes: (nodes) => set({ nodes }),

  setEdges: (edges) => set({ edges }),

  onNodesChange: (changes) => {
    set((state) => {
      // Check if this is the end of a drag operation
      const dragEndChange = changes.find(
        c => c.type === 'position' && 'dragging' in c && c.dragging === false
      );

      if (dragEndChange && dragEndChange.type === 'position') {
        // Get the node that was dragged
        const draggedNodeId = dragEndChange.id;
        const oldNode = state.nodes.find(n => n.id === draggedNodeId);
        
        if (oldNode && dragEndChange.position) {
          // Calculate delta
          const delta = {
            x: dragEndChange.position.x - oldNode.position.x,
            y: dragEndChange.position.y - oldNode.position.y
          };

          // Build hierarchy
          const hierarchyMap = buildHierarchy(state.nodes, state.edges);

          // Move node and all its children
          const movedNodes = moveNodeWithChildren(
            draggedNodeId,
            delta,
            hierarchyMap,
            state.nodes
          );

          // Batch update positions in database
          if (state.currentCanvasId) {
            const updates = movedNodes
              .filter(n => n.id === draggedNodeId || hierarchyMap.get(draggedNodeId)?.children.some(c => c.nodeId === n.id))
              .map(node => ({
                id: node.id,
                position_x: node.position.x,
                position_y: node.position.y
              }));

            if (updates.length > 0) {
              api.batchUpdateNodes(updates).catch(err => 
                console.error('Failed to update node positions:', err)
              );
            }
          }

          return {
            nodes: movedNodes,
            history: {
              past: [...state.history.past, { nodes: state.nodes, edges: state.edges }],
              future: []
            }
          };
        }
      }

      // For other changes, apply normally
      const newNodes = applyNodeChanges(changes, state.nodes);
      return { nodes: newNodes };
    });
  },

  onEdgesChange: (changes) => {
    set((state) => ({
      edges: applyEdgeChanges(changes, state.edges)
    }));
  },

  onConnect: async (connection) => {
    const { currentCanvasId } = get();

    // Add edge with consistent styling (no animation, solid line)
    const newEdge = {
      ...connection,
      animated: false, // Ensure solid line, not dotted
      type: 'engagement', // Use our custom edge type
    };

    set((state) => ({
      edges: addEdge(newEdge, state.edges)
    }));

    if (currentCanvasId) {
      try {
        await api.createConnection({
          canvas_id: currentCanvasId,
          source_id: connection.source!,
          target_id: connection.target!,
          type: connection.sourceHandle || 'default',
          animated: false // Explicitly set to false for solid lines
        });
      } catch (error) {
        console.error('Failed to create connection:', error);
      }
    }
  },

  addNode: async (nodeData) => {
    const { currentCanvasId, nodes, edges } = get();
    if (!currentCanvasId) return;

    try {
      // Use smart positioning if position is at origin (0,0) or not specified
      let position = nodeData.position;
      if (!position || (position.x === 0 && position.y === 0)) {
        // Find root nodes or use all nodes if no roots
        const rootNodes = getRootNodes(nodes, edges);
        const sourceNodes = rootNodes.length > 0 ? rootNodes : nodes;
        
        if (sourceNodes.length > 0) {
          position = getRightmostPosition(sourceNodes, nodes, edges);
        } else {
          // First node on canvas
          position = { x: 100, y: 100 };
        }
      }

      // Get default metadata for card type
      const cardType = nodeData.data?.cardType || nodeData.type || 'rich_text';
      const defaultMetadata = getNodeDefaultMetadata(cardType as any);

      const data = await api.createNode({
        canvas_id: currentCanvasId,
        content: nodeData.data?.label || '',
        position_x: position.x,
        position_y: position.y,
        type: nodeData.type || 'custom',
        parent_id: nodeData.data?.parentId || null,
        card_data: { ...defaultMetadata, ...nodeData.data?.card_data }
      });

      const newNode: Node = {
        id: data.id,
        type: data.type,
        position: { x: data.position_x, y: data.position_y },
        data: { 
          label: data.content, 
          parentId: data.parent_id,
          // Include source attribution fields from API response
          sourceType: data.source_type || 'manual',
          sourceUrl: data.source_url,
          extractedAt: data.extracted_at,
          sources: data.sources || [],
          hasConflict: data.has_conflict || false
        }
      };

      set((state) => ({
        nodes: [...state.nodes, newNode],
        history: {
          past: [...state.history.past, { nodes: state.nodes, edges: state.edges }],
          future: []
        }
      }));
      
      // Increment modification counter
      get().incrementModificationCount();
    } catch (error) {
      console.error('Failed to add node:', error);
    }
  },

  updateNode: async (id, data) => {
    const { currentCanvasId } = get();
    if (!currentCanvasId) return;

    try {
      // Build update payload with all relevant fields
      const updatePayload: any = {};
      
      if (data.content !== undefined) updatePayload.content = data.content;
      if (data.title !== undefined) updatePayload.title = data.title;
      if (data.cardType !== undefined) updatePayload.card_type = data.cardType;
      if (data.card_data !== undefined) updatePayload.card_data = data.card_data;
      if (data.tags !== undefined) updatePayload.tags = data.tags;
      if (data.label !== undefined) updatePayload.content = data.label; // Backward compatibility

      // Only make API call if there's something to update
      if (Object.keys(updatePayload).length > 0) {
        await api.updateNode(id, updatePayload);
      }

      set((state) => ({
        nodes: state.nodes.map(node =>
          node.id === id ? { ...node, data: { ...node.data, ...data } } : node
        ),
        history: {
          past: [...state.history.past, { nodes: state.nodes, edges: state.edges }],
          future: []
        }
      }));
    } catch (error) {
      console.error('Failed to update node:', error);
    }
  },

  deleteEdge: async (id: string) => {
    try {
      await api.deleteConnection(id);
      
      // Remove edge from state
      set((state) => ({
        edges: state.edges.filter(e => e.id !== id),
        history: {
          past: [...state.history.past, { nodes: state.nodes, edges: state.edges }],
          future: []
        }
      }));
    } catch (error) {
      console.error('Failed to delete edge:', error);
      throw error;
    }
  },

  deleteNode: async (id) => {
    const { currentCanvasId } = get();
    if (!currentCanvasId) return;

    try {
      await api.deleteNode(id);

      set((state) => ({
        nodes: state.nodes.filter(node => node.id !== id),
        edges: state.edges.filter(edge => edge.source !== id && edge.target !== id),
        history: {
          past: [...state.history.past, { nodes: state.nodes, edges: state.edges }],
          future: []
        }
      }));
    } catch (error) {
      console.error('Failed to delete node:', error);
    }
  },

  duplicateNode: async (id) => {
    const { nodes, edges, currentCanvasId } = get();
    const nodeToDuplicate = nodes.find(n => n.id === id);
    
    if (!nodeToDuplicate || !currentCanvasId) return;

    try {
      // Use smart positioning to find optimal position for duplicate
      const duplicatePosition = getRightmostPosition(
        [nodeToDuplicate],
        nodes,
        edges
      );

      const data = await api.createNode({
        canvas_id: currentCanvasId,
        content: nodeToDuplicate.data?.label || '',
        title: nodeToDuplicate.data?.title || '',
        card_type: nodeToDuplicate.data?.cardType || 'rich_text',
        card_data: nodeToDuplicate.data?.card_data || {},
        tags: nodeToDuplicate.data?.tags || [],
        position_x: duplicatePosition.x,
        position_y: duplicatePosition.y,
        type: nodeToDuplicate.type || 'custom',
        parent_id: nodeToDuplicate.data?.parentId || null
      });

      const newNode: Node = {
        id: data.id,
        type: data.type,
        position: duplicatePosition,
        data: { 
          ...nodeToDuplicate.data,
          label: data.content,
          parentId: data.parent_id,
          // Include source attribution fields from API response
          sourceType: data.source_type || 'manual',
          sourceUrl: data.source_url,
          extractedAt: data.extracted_at,
          sources: data.sources || [],
          hasConflict: data.has_conflict || false
        }
      };

      set((state) => ({
        nodes: [...state.nodes, newNode],
        history: {
          past: [...state.history.past, { nodes: state.nodes, edges: state.edges }],
          future: []
        }
      }));
    } catch (error) {
      console.error('Failed to duplicate node:', error);
    }
  },

  changeNodeType: async (id, newType) => {
    const { nodes } = get();
    const node = nodes.find(n => n.id === id);
    
    if (!node) return;

    try {
      await api.updateNode(id, { 
        card_type: newType
      });

      set((state) => ({
        nodes: state.nodes.map(n =>
          n.id === id
            ? { 
                ...n, 
                type: newType,
                data: { ...n.data, cardType: newType }
              }
            : n
        ),
        history: {
          past: [...state.history.past, { nodes: state.nodes, edges: state.edges }],
          future: []
        }
      }));
    } catch (error) {
      console.error('Failed to change node type:', error);
    }
  },

  createChildNode: async (parentId) => {
    const { nodes, edges, currentCanvasId, childLayoutMode } = get();
    const parentNode = nodes.find(n => n.id === parentId);
    
    if (!parentNode || !currentCanvasId) return;

    try {
      // Find existing children of this parent
      const existingChildren = nodes.filter(n => n.data?.parentId === parentId);
      
      // Calculate initial position (will be rearranged)
      const tempPosition = {
        x: parentNode.position.x + 280,
        y: parentNode.position.y
      };

      const data = await api.createNode({
        canvas_id: currentCanvasId,
        content: '',
        title: 'New Child Node',
        card_type: 'rich_text',
        card_data: {},
        tags: [],
        position_x: tempPosition.x,
        position_y: tempPosition.y,
        type: 'richText',
        parent_id: parentId
      });

      const newNode: Node = {
        id: data.id,
        type: 'richText',
        position: tempPosition,
        data: {
          label: 'New Child Node',
          title: 'New Child Node',
          content: '',
          cardType: 'rich_text',
          tags: [],
          createdAt: new Date().toISOString(),
          parentId: parentId,
          // Include source attribution fields from API response
          sourceType: data.source_type || 'manual',
          sourceUrl: data.source_url,
          extractedAt: data.extracted_at,
          sources: data.sources || [],
          hasConflict: data.has_conflict || false
        }
      };

      // Create edge from parent to child
      const newEdge: Edge = {
        id: `${parentId}-${data.id}`,
        source: parentId,
        target: data.id,
        animated: true
      };

      await api.createConnection({
        canvas_id: currentCanvasId,
        source_id: parentId,
        target_id: data.id,
        type: 'default'
      });

      // Add new node to state
      const updatedNodes = [...nodes, newNode];
      const updatedEdges = [...edges, newEdge];
      
      // Get all children (including the new one)
      const allChildren = [...existingChildren, newNode];
      
      // Arrange children based on layout mode
      let arrangedChildren: Node[];
      if (childLayoutMode === 'hierarchical' && allChildren.length > 3) {
        // Use hierarchical layout for many children
        arrangedChildren = layoutBranch(allChildren, updatedEdges, [parentNode]);
      } else {
        // Use circular layout (default or for few children)
        arrangedChildren = arrangeChildrenCircular(parentNode, allChildren, 280);
      }
      
      // Update positions in state
      const finalNodes = updatedNodes.map(node => {
        const arranged = arrangedChildren.find(c => c.id === node.id);
        return arranged || node;
      });

      // Batch update child positions in database
      if (arrangedChildren.length > 0) {
        const positionUpdates = arrangedChildren.map(child => ({
          id: child.id,
          position_x: child.position.x,
          position_y: child.position.y
        }));
        
        await api.batchUpdateNodes(positionUpdates);
      }

      set((state) => ({
        nodes: finalNodes,
        edges: updatedEdges,
        selectedNode: data.id,
        history: {
          past: [...state.history.past, { nodes: state.nodes, edges: state.edges }],
          future: []
        }
      }));
    } catch (error) {
      console.error('Failed to create child node:', error);
    }
  },

  createSiblingNode: async (nodeId) => {
    const { nodes, edges, currentCanvasId } = get();
    const siblingNode = nodes.find(n => n.id === nodeId);
    
    if (!siblingNode || !currentCanvasId) return;

    try {
      // Use smart positioning to find optimal position to the right
      const siblingPosition = getRightmostPosition(
        [siblingNode],  // Source node
        nodes,          // All nodes
        edges           // All edges
      );

      const data = await api.createNode({
        canvas_id: currentCanvasId,
        content: '',
        title: 'New Sibling Node',
        card_type: 'rich_text',
        card_data: {},
        tags: [],
        position_x: siblingPosition.x,
        position_y: siblingPosition.y,
        type: 'richText',
        parent_id: siblingNode.data?.parentId || null
      });

      const newNode: Node = {
        id: data.id,
        type: 'richText',
        position: siblingPosition,
        data: {
          label: 'New Sibling Node',
          title: 'New Sibling Node',
          content: '',
          cardType: 'rich_text',
          tags: [],
          createdAt: new Date().toISOString(),
          parentId: siblingNode.data?.parentId || null,
          // Include source attribution fields from API response
          sourceType: data.source_type || 'manual',
          sourceUrl: data.source_url,
          extractedAt: data.extracted_at,
          sources: data.sources || [],
          hasConflict: data.has_conflict || false
        }
      };

      set((state) => ({
        nodes: [...state.nodes, newNode],
        selectedNode: data.id,
        history: {
          past: [...state.history.past, { nodes: state.nodes, edges: state.edges }],
          future: []
        }
      }));
    } catch (error) {
      console.error('Failed to create sibling node:', error);
    }
  },

  deleteSelectedNodes: async () => {
    const { nodes, selectedNode } = get();
    
    if (!selectedNode) return;

    const selectedNodes = nodes.filter(n => n.selected || n.id === selectedNode);
    
    for (const node of selectedNodes) {
      await get().deleteNode(node.id);
    }
  },

  duplicateSelectedNodes: async () => {
    const { nodes, selectedNode } = get();
    
    if (!selectedNode) return;

    const selectedNodes = nodes.filter(n => n.selected || n.id === selectedNode);
    
    for (const node of selectedNodes) {
      await get().duplicateNode(node.id);
    }
  },

  clearSelection: () => {
    set({ selectedNode: null });
  },

  getSelectedNodes: () => {
    const { nodes, selectedNode } = get();
    return nodes.filter(n => n.selected || n.id === selectedNode);
  },

  toggleCollapse: (nodeId) => {
    set((state) => ({
      collapseState: {
        ...state.collapseState,
        [nodeId]: !state.collapseState[nodeId]
      }
    }));
  },

  setCollapseState: (nodeId, collapsed) => {
    set((state) => ({
      collapseState: {
        ...state.collapseState,
        [nodeId]: collapsed
      }
    }));
  },

  addTagToNode: async (nodeId, tag) => {
    const { nodes } = get();
    const node = nodes.find(n => n.id === nodeId);
    if (!node) return;

    const currentTags = node.data.tags || [];
    const newTags = [...currentTags, tag];

    try {
      await api.updateNode(nodeId, { tags: newTags });

      set((state) => ({
        nodes: state.nodes.map(n =>
          n.id === nodeId
            ? { ...n, data: { ...n.data, tags: newTags } }
            : n
        ),
        history: {
          past: [...state.history.past, { nodes: state.nodes, edges: state.edges }],
          future: []
        }
      }));
    } catch (error) {
      console.error('Failed to add tag:', error);
    }
  },

  removeTagFromNode: async (nodeId, tag) => {
    const { nodes } = get();
    const node = nodes.find(n => n.id === nodeId);
    if (!node) return;

    const currentTags = node.data.tags || [];
    const newTags = currentTags.filter((t: string) => t !== tag);

    try {
      await api.updateNode(nodeId, { tags: newTags });

      set((state) => ({
        nodes: state.nodes.map(n =>
          n.id === nodeId
            ? { ...n, data: { ...n.data, tags: newTags } }
            : n
        ),
        history: {
          past: [...state.history.past, { nodes: state.nodes, edges: state.edges }],
          future: []
        }
      }));
    } catch (error) {
      console.error('Failed to remove tag:', error);
    }
  },

  setSelectedNode: async (id) => {
    if (id) {
      await get().incrementReadCount(id);
    }
    set({ selectedNode: id });
  },

  undo: () => {
    set((state) => {
      const { past, future } = state.history;
      if (past.length === 0) return state;

      const previous = past[past.length - 1];
      const newPast = past.slice(0, past.length - 1);

      return {
        nodes: previous.nodes,
        edges: previous.edges,
        history: {
          past: newPast,
          future: [{ nodes: state.nodes, edges: state.edges }, ...future]
        }
      };
    });
  },

  redo: () => {
    set((state) => {
      const { past, future } = state.history;
      if (future.length === 0) return state;

      const next = future[0];
      const newFuture = future.slice(1);

      return {
        nodes: next.nodes,
        edges: next.edges,
        history: {
          past: [...past, { nodes: state.nodes, edges: state.edges }],
          future: newFuture
        }
      };
    });
  },

  setViewMode: (mode) => set({ viewMode: mode }),

  setSidebarWidth: (width) => set({ sidebarWidth: width }),

  loadCanvas: async (canvasId) => {
    try {
      const nodes = await api.getNodes(canvasId);
      const connections = await api.getConnections(canvasId);

      const rfNodes: Node[] = (nodes || []).map(node => ({
        id: node.id,
        type: node.type,
        position: { 
          x: parseFloat(node.position_x), 
          y: parseFloat(node.position_y) 
        },
        data: {
          label: node.content,
          title: node.title || node.content || 'Untitled',
          content: node.content || '',
          cardType: node.card_type || 'rich_text',
          card_data: node.card_data || {},
          tags: node.tags || [],
          createdAt: node.created_at,
          updatedAt: node.updated_at,
          parentId: node.parent_id,
          width: node.width,
          height: node.height,
          // Source attribution fields
          sourceType: node.source_type || 'manual',
          sourceUrl: node.source_url,
          extractedAt: node.extracted_at,
          sources: node.sources || [],
          // Conflict detection
          hasConflict: node.has_conflict || false,
          // Engagement tracking
          readCount: node.card_data?.read_count || 0,
          importance: node.card_data?.importance || 'normal',
          cardTypeIcon: node.card_data?.card_type_icon,
          // Spread card_data fields for direct access by card components
          ...node.card_data
        }
      }));

      const rfEdges: Edge[] = (connections || []).map(conn => {
        const targetNode = rfNodes.find(n => n.id === conn.target_id);
        return {
          id: conn.id,
          source: conn.source_id,
          target: conn.target_id,
          type: 'engagement',
          animated: false, // Force false for all edges - we want solid lines, not dotted
          data: {
            targetReadCount: targetNode?.data?.readCount || targetNode?.data?.card_data?.read_count || 0
          }
        };
      });

      set({
        nodes: rfNodes,
        edges: rfEdges,
        currentCanvasId: canvasId,
        history: { past: [], future: [] }
      });
    } catch (error) {
      console.error('Failed to load canvas:', error);
    }
  },

  saveCanvas: async () => {
    const { currentCanvasId, nodes } = get();
    if (!currentCanvasId) return;

    try {
      // Create snapshot before save
      await get().triggerSnapshot();

      // Batch update all node positions
      const updates = nodes.map(node => ({
        id: node.id,
        position_x: node.position.x,
        position_y: node.position.y
      }));

      await api.batchUpdateNodes(updates);
    } catch (error) {
      console.error('Failed to save canvas:', error);
    }
  },

  exportCanvas: () => {
    const { nodes, edges, canvasName } = get();
    const exportData = {
      version: '1.0',
      name: canvasName,
      nodes: nodes.map(node => ({
        id: node.id,
        type: node.type,
        position: node.position,
        data: node.data
      })),
      edges: edges.map(edge => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        type: edge.type
      })),
      timestamp: new Date().toISOString()
    };
    return JSON.stringify(exportData, null, 2);
  },

  importCanvas: async (data) => {
    try {
      const importData = JSON.parse(data);
      const { currentCanvasId } = get();

      if (!currentCanvasId) return;

      // Get existing nodes and connections to delete
      const existingNodes = await api.getNodes(currentCanvasId);
      const existingConnections = await api.getConnections(currentCanvasId);

      // Delete existing data
      for (const node of existingNodes) {
        await api.deleteNode(node.id);
      }
      for (const conn of existingConnections) {
        await api.deleteConnection(conn.id);
      }

      const nodeIdMap = new Map<string, string>();

      // Create new nodes
      for (const node of importData.nodes) {
        const newNode = await api.createNode({
          canvas_id: currentCanvasId,
          content: node.data.label || '',
          position_x: node.position.x,
          position_y: node.position.y,
          type: node.type
        });

        if (newNode) {
          nodeIdMap.set(node.id, newNode.id);
        }
      }

      // Create new connections
      for (const edge of importData.edges) {
        const newSourceId = nodeIdMap.get(edge.source);
        const newTargetId = nodeIdMap.get(edge.target);

        if (newSourceId && newTargetId) {
          await api.createConnection({
            canvas_id: currentCanvasId,
            source_id: newSourceId,
            target_id: newTargetId,
            type: edge.type || 'default'
          });
        }
      }

      await get().loadCanvas(currentCanvasId);
    } catch (error) {
      console.error('Import failed:', error);
    }
  },

  applyLayoutToCanvas: async (algorithm) => {
    const { nodes, edges, currentCanvasId } = get();
    
    if (!currentCanvasId || nodes.length === 0) return;

    try {
      // Apply layout algorithm
      const layoutedNodes = applyLayout(nodes, edges, { algorithm });

      // Update nodes in state
      set((state) => ({
        nodes: layoutedNodes,
        history: {
          past: [...state.history.past, { nodes: state.nodes, edges: state.edges }],
          future: []
        }
      }));

      // Batch update positions in database
      const updates = layoutedNodes.map(node => ({
        id: node.id,
        position_x: node.position.x,
        position_y: node.position.y
      }));

      await api.batchUpdateNodes(updates);
      
      // Trigger snapshot after layout
      get().incrementModificationCount();
    } catch (error) {
      console.error('Failed to apply layout:', error);
    }
  },

  setReactFlowInstance: (instance) => {
    set({ reactFlowInstance: instance });
  },

  triggerSnapshot: async () => {
    const { currentCanvasId, nodes, edges, reactFlowInstance } = get();
    
    if (!currentCanvasId || nodes.length === 0) return;

    try {
      // Get viewport from ReactFlow instance
      const viewport: Viewport = reactFlowInstance?.getViewport() || { x: 0, y: 0, zoom: 1 };

      // Create snapshot
      const snapshot = snapshotManager.createSnapshot(
        currentCanvasId,
        nodes,
        edges,
        viewport
      );

      // Save to database
      await snapshotManager.saveToDatabase(snapshot);

      // Update last snapshot time
      set({ lastSnapshotTime: Date.now(), modificationCount: 0 });
    } catch (error) {
      console.error('Failed to create snapshot:', error);
    }
  },

  incrementModificationCount: () => {
    set((state) => {
      const newCount = state.modificationCount + 1;
      
      // Trigger snapshot every 10 modifications
      if (newCount >= 10) {
        // Trigger snapshot asynchronously
        get().triggerSnapshot();
        return { modificationCount: 0 };
      }
      
      return { modificationCount: newCount };
    });
  },

  handleGrow: async (nodeId: string) => {
    const { currentCanvasId, nodes, activeGrowOperations } = get();
    
    if (!currentCanvasId) {
      console.error('No canvas selected');
      return;
    }

    if (activeGrowOperations.has(nodeId)) {
      console.log('Card is already being grown');
      return;
    }

    // Find the node
    const node = nodes.find(n => n.id === nodeId);
    if (!node) {
      console.error('Node not found');
      return;
    }

    try {
      // Add to active operations
      set(state => ({
        activeGrowOperations: new Set([...state.activeGrowOperations, nodeId])
      }));

      // Get session ID from localStorage
      const sessionId = localStorage.getItem('chat_session_id') || undefined;

      // Call the chat API with a grow request
      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: `Grow the card with ID ${nodeId}. The card title is "${node.data?.title || ''}" and content is: ${node.data?.content || ''}. Extract 3-5 key concepts and create child cards arranged in a circle around this parent card.`,
          canvas_id: currentCanvasId,
          session_id: sessionId
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Handle SSE stream
      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body reader available');
      }

      const decoder = new TextDecoder();
      let buffer = '';

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.trim() === '') continue;
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                
                // Handle completion
                if (data.type === 'complete') {
                  // Store current nodes before reload
                  const nodesBefore = get().nodes;
                  
                  // Reload canvas to show new cards
                  await get().loadCanvas(currentCanvasId);
                  
                  // Apply layout to newly created child cards
                  const { nodes: nodesAfter, edges: edgesAfter } = get();
                  const parentNode = nodesAfter.find(n => n.id === nodeId);
                  
                  if (parentNode) {
                    // Find all child nodes
                    const childEdges = edgesAfter.filter(edge => edge.source === nodeId);
                    const childNodeIds = childEdges.map(edge => edge.target);
                    const childNodes = nodesAfter.filter(n => childNodeIds.includes(n.id));
                    
                    if (childNodes.length > 0) {
                      // Arrange children based on layout mode
                      const { childLayoutMode } = get();
                      let arrangedChildren: Node[];
                      
                      if (childLayoutMode === 'hierarchical' && childNodes.length > 3) {
                        // Use hierarchical layout for many children
                        arrangedChildren = layoutBranch(childNodes, edgesAfter, [parentNode]);
                      } else {
                        // Use circular layout (default or for few children)
                        arrangedChildren = arrangeChildrenCircular(
                          parentNode,
                          childNodes,
                          280 // radius
                        );
                      }
                      
                      // Update node positions in state
                      const updatedNodes = nodesAfter.map(node => {
                        const arranged = arrangedChildren.find(c => c.id === node.id);
                        return arranged || node;
                      });
                      
                      set({ nodes: updatedNodes });
                      
                      // Batch update positions in database
                      const positionUpdates = arrangedChildren.map(node => ({
                        id: node.id,
                        position_x: node.position.x,
                        position_y: node.position.y
                      }));
                      
                      if (positionUpdates.length > 0) {
                        api.batchUpdateNodes(positionUpdates).catch(err =>
                          console.error('Failed to update child node positions:', err)
                        );
                      }
                    }
                  }
                  
                  // Apply animations after a short delay
                  setTimeout(() => {
                    const edges = get().edges;
                    
                    // Find new child cards (cards connected to parent that weren't there before)
                    const childEdges = edges.filter(edge => edge.source === nodeId);
                    const childNodeIds = childEdges.map(edge => edge.target);
                    
                    // Filter to only truly new nodes
                    const beforeIds = new Set(nodesBefore.map(n => n.id));
                    const newChildIds = childNodeIds.filter(id => !beforeIds.has(id));
                    
                    // Apply animations to new cards
                    newChildIds.forEach((childId, index) => {
                      const cardElement = document.querySelector(`[data-id="${childId}"]`);
                      if (cardElement) {
                        cardElement.classList.add('animate-grow-appear', 'grow-new-card');
                        
                        // Add stagger delay
                        if (index < 5) {
                          cardElement.classList.add(`animate-grow-stagger-${index + 1}`);
                        }
                        
                        // Remove animation classes after completion
                        setTimeout(() => {
                          cardElement.classList.remove(
                            'animate-grow-appear',
                            `animate-grow-stagger-${index + 1}`
                          );
                        }, 1000 + (index * 100));
                        
                        // Remove new card styling after longer delay
                        setTimeout(() => {
                          cardElement.classList.remove('grow-new-card');
                        }, 3000);
                      }
                    });
                    
                    // Highlight parent card temporarily
                    const parentElement = document.querySelector(`[data-id="${nodeId}"]`);
                    if (parentElement) {
                      parentElement.classList.add('grow-parent-card');
                      setTimeout(() => {
                        parentElement.classList.remove('grow-parent-card');
                      }, 2000);
                    }
                  }, 100);
                  
                  console.log('Grow operation completed successfully');
                }
              } catch (parseError) {
                console.warn('Failed to parse SSE data:', line);
              }
            }
          }
        }
      } finally {
        reader.releaseLock();
      }

    } catch (error) {
      console.error('Error growing card:', error);
    } finally {
      // Remove from active operations
      set(state => {
        const newActiveOps = new Set(state.activeGrowOperations);
        newActiveOps.delete(nodeId);
        return { activeGrowOperations: newActiveOps };
      });
    }
  },

  mergeCards: async (sourceCardId: string, targetCardId: string) => {
    const { currentCanvasId } = get();
    
    if (!currentCanvasId) {
      console.error('No canvas selected');
      return;
    }

    try {
      // Call merge API
      await api.mergeCards(sourceCardId, targetCardId);
      
      // Reload canvas to reflect changes
      await get().loadCanvas(currentCanvasId);
      
      console.log(`Successfully merged card ${sourceCardId} into ${targetCardId}`);
    } catch (error) {
      console.error('Error merging cards:', error);
      set({ error: error instanceof Error ? error.message : 'Failed to merge cards' });
    }
  },

  executeLearningAction: async (action: string, nodeId: string) => {
    const { currentCanvasId, nodes } = get();
    if (!currentCanvasId) return;
    
    const actionId = `${action}_${nodeId}`;
    
    // Set loading state
    set(state => ({
      learningActions: {
        ...state.learningActions,
        [actionId]: { status: 'loading', result: null, error: null }
      }
    }));
    
    try {
      // Call API
      const result = await api.executeLearningAction(action, nodeId, {
        canvas_id: currentCanvasId,
        create_card_option: true // Create cards by default
      });
      
      // Update state with result
      set(state => ({
        learningActions: {
          ...state.learningActions,
          [actionId]: { status: 'success', result, error: null }
        }
      }));
      
      // If new cards were created, add them incrementally
      if (result.new_card_ids && result.new_card_ids.length > 0) {
        await get().addCardsIncremental(result.new_card_ids);
      } else if (result.simplified_card_id) {
        // Handle single card creation (simplify action)
        await get().addCardsIncremental([result.simplified_card_id]);
      } else if (result.gap_card_ids && result.gap_card_ids.length > 0) {
        // Handle gap cards
        await get().addCardsIncremental(result.gap_card_ids);
      } else if (result.example_card_ids && result.example_card_ids.length > 0) {
        // Handle example cards
        await get().addCardsIncremental(result.example_card_ids);
      } else if (result.plan_card_ids && result.plan_card_ids.length > 0) {
        // Handle action plan cards
        await get().addCardsIncremental(result.plan_card_ids);
      }
      
      console.log(`Learning action ${action} completed successfully`);
      
    } catch (error) {
      console.error(`Learning action ${action} failed:`, error);
      set(state => ({
        learningActions: {
          ...state.learningActions,
          [actionId]: { 
            status: 'error', 
            result: null, 
            error: error instanceof Error ? error.message : 'Unknown error' 
          }
        }
      }));
    }
  },

  clearLearningAction: (actionId: string) => {
    set(state => {
      const newActions = { ...state.learningActions };
      delete newActions[actionId];
      return { learningActions: newActions };
    });
  },

  addCardsIncremental: async (newCardIds: string[]) => {
    const { currentCanvasId } = get();
    if (!currentCanvasId) return;
    
    try {
      // Fetch only new cards
      const newCards = await Promise.all(
        newCardIds.map(id => api.getNode(id))
      );
      
      // Convert to ReactFlow nodes
      const rfNodes = newCards.map(card => ({
        id: card.id,
        type: card.card_type || 'rich_text',
        position: { x: card.position_x || 0, y: card.position_y || 0 },
        data: {
          label: card.content,
          title: card.title || card.content || 'Untitled',
          content: card.content || '',
          cardType: card.card_type || 'rich_text',
          card_data: card.card_data || {},
          tags: card.tags || [],
          createdAt: card.created_at,
          parentId: card.parent_id,
          sourceType: card.source_type || 'ai_generated',
          sourceUrl: card.source_url,
          extractedAt: card.extracted_at,
          sources: card.sources || [],
          hasConflict: card.has_conflict || false
        }
      }));
      
      // Add to existing nodes (don't reload all!)
      set(state => ({
        nodes: [...state.nodes, ...rfNodes]
      }));
      
      // Fetch new connections
      const allConnections = await api.getConnections(currentCanvasId);
      const newEdges = allConnections
        .filter(conn => newCardIds.includes(conn.source_id) || newCardIds.includes(conn.target_id))
        .map(conn => ({
          id: conn.id,
          source: conn.source_id,
          target: conn.target_id,
          type: 'default',
          animated: true
        }));
      
      // Add new edges
      set(state => ({
        edges: [...state.edges, ...newEdges]
      }));
      
      console.log(`Added ${newCards.length} cards and ${newEdges.length} connections incrementally`);
      
    } catch (error) {
      console.error('Failed to add cards incrementally:', error);
    }
  },

  // Engagement tracking
  incrementReadCount: async (cardId: string) => {
    try {
      const { nodes } = get();
      const node = nodes.find(n => n.id === cardId);
      
      if (node) {
        const newReadCount = (node.data.readCount || 0) + 1;
        
        // Update in database
        await api.updateNode(cardId, {
          card_data: {
            ...node.data.card_data,
            read_count: newReadCount
          }
        });
        
        // Update in state
        set(state => ({
          nodes: state.nodes.map(n =>
            n.id === cardId
              ? { ...n, data: { ...n.data, readCount: newReadCount } }
              : n
          )
        }));
        
        // Update edges connected to this card
        get().updateEdgesForNode(cardId, newReadCount);
      }
    } catch (error) {
      console.error('Failed to increment read count:', error);
    }
  },

  handleComprehensiveLearn: async (nodeId: string) => {
    const { currentCanvasId } = get();
    if (!currentCanvasId) return;
    
    try {
      // Get session ID from localStorage or generate one
      const sessionId = localStorage.getItem('chat_session_id') || 'default-session';
      
      // Call backend
      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: `Execute comprehensive learning for card ${nodeId}`,
          canvas_id: currentCanvasId,
          session_id: sessionId
        })
      });
      
      if (!response.body) throw new Error('No response body');
      
      // Parse SSE stream
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.type === 'complete') {
                // Reload canvas to show new cards
                await get().loadCanvas(currentCanvasId);
                
                // Apply visual cluster effects
                setTimeout(() => {
                  get().applyLearningClusterEffects(nodeId);
                }, 500);
                
                break;
              }
            } catch (parseError) {
              console.warn('Failed to parse SSE data:', parseError);
            }
          }
        }
      }
    } catch (error) {
      console.error('Comprehensive learn failed:', error);
    }
  },

  updateEdgesForNode: (nodeId: string, readCount: number) => {
    set(state => ({
      edges: state.edges.map(edge =>
        edge.target === nodeId
          ? { 
              ...edge, 
              type: 'engagement',
              data: { ...edge.data, targetReadCount: readCount } 
            }
          : edge
      )
    }));
  },

  applyLearningClusterEffects: (parentNodeId: string) => {
    const { nodes, edges, reactFlowInstance } = get();
    
    // Define cluster colors by card type
    const CLUSTER_COLORS: Record<string, string> = {
      question: '#A78BFA',      // Purple
      todo: '#34D399',          // Green
      reminder: '#FCD34D',      // Yellow
      person: '#60A5FA',        // Blue
      concept: '#F472B6',       // Pink
      technique: '#FB923C',     // Orange
      contradiction: '#EF4444', // Red
      example: '#10B981',       // Emerald
      challenge: '#8B5CF6',     // Violet
      rich_text: '#64748B'      // Gray (default)
    };
    
    // Find parent and child cards
    const parentNode = nodes.find(n => n.id === parentNodeId);
    const childEdges = edges.filter(e => e.source === parentNodeId);
    const childNodeIds = childEdges.map(e => e.target);
    const childCards = nodes.filter(n => childNodeIds.includes(n.id));
    
    if (!parentNode) return;
    
    // Apply colored borders to cluster cards
    setTimeout(() => {
      [parentNode, ...childCards].forEach(card => {
        const cardType = card.data?.cardType || 'rich_text';
        const color = CLUSTER_COLORS[cardType] || '#64748B';
        const element = document.querySelector(`[data-id="${card.id}"]`);
        if (element) {
          (element as HTMLElement).style.border = `3px solid ${color}`;
          element.classList.add('learning-cluster-card');
        }
      });
      
      // Zoom to show entire cluster
      if (reactFlowInstance && childCards.length > 0) {
        const clusterNodes = [parentNode, ...childCards];
        reactFlowInstance.fitView({ 
          nodes: clusterNodes, 
          padding: 0.2, 
          duration: 800 
        });
      }
    }, 100);
  },

  // Layout utilities
  setChildLayoutMode: (mode: 'circular' | 'hierarchical') => {
    set({ childLayoutMode: mode });
  },

  getNodeLevel: (nodeId: string) => {
    const { nodes, edges } = get();
    const rootNodes = getRootNodes(nodes, edges);
    return getNodeLevel(nodeId, nodes, edges, rootNodes);
  },

  getRootNodes: () => {
    const { nodes, edges } = get();
    return getRootNodes(nodes, edges);
  },

  optimizeLayout: async () => {
    const { nodes, currentCanvasId } = get();
    
    if (!currentCanvasId || nodes.length === 0) return;

    try {
      // Simple overlap prevention: shift overlapping nodes
      const optimizedNodes = nodes.map((node, index) => {
        // Check for overlaps with previous nodes
        const overlapping = nodes.slice(0, index).find(other => {
          const dx = Math.abs(node.position.x - other.position.x);
          const dy = Math.abs(node.position.y - other.position.y);
          return dx < 320 && dy < 170; // Card dimensions + padding
        });
        
        if (overlapping) {
          // Shift to the right
          return {
            ...node,
            position: {
              x: overlapping.position.x + 400,
              y: overlapping.position.y
            }
          };
        }
        
        return node;
      });
      
      // Update nodes in state
      set((state) => ({
        nodes: optimizedNodes,
        history: {
          past: [...state.history.past, { nodes: state.nodes, edges: state.edges }],
          future: []
        }
      }));

      // Batch update positions in database
      const updates = optimizedNodes
        .filter((node, index) => {
          const original = nodes[index];
          return node.position.x !== original.position.x || node.position.y !== original.position.y;
        })
        .map(node => ({
          id: node.id,
          position_x: node.position.x,
          position_y: node.position.y
        }));

      if (updates.length > 0) {
        await api.batchUpdateNodes(updates);
        console.log(`Layout optimized: ${updates.length} nodes repositioned`);
      }
    } catch (error) {
      console.error('Failed to optimize layout:', error);
    }
  }
}));
