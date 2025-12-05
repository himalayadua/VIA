import { useCallback, useEffect, useState } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  ConnectionMode,
  BackgroundVariant,
  MarkerType,
  useReactFlow
} from 'reactflow';
import 'reactflow/dist/style.css';
import { useCanvasStore } from '../store/canvasStore';
import { useSearchStore } from '../store/searchStore';
import { CustomNode } from './CustomNode';
import { RichTextNode } from './nodes/RichTextNode';
import { TodoNode } from './nodes/TodoNode';
import { VideoNode } from './nodes/VideoNode';
import { LinkNode } from './nodes/LinkNode';
import { ReminderNode } from './nodes/ReminderNode';
import { EngagementEdge } from './edges/EngagementEdge';
import { ContextMenu, MenuItem } from './ContextMenu';
import { KeyboardHandler } from './KeyboardHandler';
import { SearchPanel } from './SearchPanel';
import { SourceDetailsModal } from './SourceDetailsModal';
import { ConflictComparisonModal } from './ConflictComparisonModal';
import { 
  FileText, 
  CheckSquare, 
  Video, 
  Link as LinkIcon, 
  Clock, 
  Sparkles, 
  Loader2,
  GraduationCap,
  Search,
  Lightbulb,
  BookOpen,
  Target,
  AlertCircle,
  Network,
  RefreshCw,
  CheckCircle
} from 'lucide-react';
import { CardType } from '../types/cardTypes';
import { buildHierarchy, getDescendants, hasChildren, countDescendants } from '../utils/hierarchyUtils';

const nodeTypes = {
  custom: CustomNode,
  richText: RichTextNode,
  rich_text: RichTextNode,
  todo: TodoNode,
  video: VideoNode,
  link: LinkNode,
  reminder: ReminderNode
};

const edgeTypes = {
  engagement: EngagementEdge,
  default: EngagementEdge
};

const edgeOptions = {
  animated: false,
  style: { stroke: 'rgba(203, 213, 225, 0.7)', strokeWidth: 2.5 }, // Light color for dark background
  markerEnd: {
    type: MarkerType.ArrowClosed,
    color: 'rgba(203, 213, 225, 0.7)' // Light color for arrow markers
  }
};

export const Canvas = () => {
  const {
    nodes,
    edges,
    onNodesChange,
    onEdgesChange,
    onConnect,
    addNode,
    addTagToNode,
    removeTagFromNode,
    toggleCollapse,
    collapseState,
    currentCanvasId,
    deleteEdge
  } = useCanvasStore();

  const { highlightedNodes } = useSearchStore();
  const { project } = useReactFlow();
  const [contextMenu, setContextMenu] = useState<{
    position: { x: number; y: number };
    type: 'canvas' | 'node' | 'edge';
    nodeId?: string;
    edgeId?: string;
  } | null>(null);
  const [sourceDetailsModal, setSourceDetailsModal] = useState<{
    isOpen: boolean;
    nodeId?: string;
  }>({ isOpen: false });
  const [conflictModal, setConflictModal] = useState<{
    isOpen: boolean;
    nodeId?: string;
  }>({ isOpen: false });

  const createNodeAtPosition = useCallback(
    (cardType: CardType, clientPosition: { x: number; y: number }) => {
      const reactFlowBounds = document
        .querySelector('.react-flow')
        ?.getBoundingClientRect();

      if (!reactFlowBounds) return;

      // Use screenToFlowPosition instead of deprecated project
      const position = project({
        x: clientPosition.x - reactFlowBounds.left,
        y: clientPosition.y - reactFlowBounds.top
      });

      const typeMap: Record<CardType, string> = {
        [CardType.RICH_TEXT]: 'richText',
        [CardType.TODO]: 'todo',
        [CardType.VIDEO]: 'video',
        [CardType.LINK]: 'link',
        [CardType.REMINDER]: 'reminder'
      };

      addNode({
        type: typeMap[cardType],
        position,
        data: {
          label: 'New Node',
          title: cardType === CardType.RICH_TEXT ? 'New Note' : `New ${cardType}`,
          content: '',
          cardType,
          tags: [],
          createdAt: new Date().toISOString()
        }
      });
    },
    [addNode, project]
  );

  const handlePaneDoubleClick = useCallback(
    (event: React.MouseEvent) => {
      createNodeAtPosition(CardType.RICH_TEXT, {
        x: event.clientX,
        y: event.clientY
      });
    },
    [createNodeAtPosition]
  );

  const handlePaneContextMenu = useCallback((event: React.MouseEvent) => {
    event.preventDefault();
    setContextMenu({
      position: { x: event.clientX, y: event.clientY },
      type: 'canvas'
    });
  }, []);

  const handleNodeContextMenu = useCallback((event: React.MouseEvent, node: any) => {
    event.preventDefault();
    setContextMenu({
      position: { x: event.clientX, y: event.clientY },
      type: 'node',
      nodeId: node.id
    });
  }, []);

  const handleEdgeContextMenu = useCallback((event: React.MouseEvent, edge: any) => {
    event.preventDefault();
    setContextMenu({
      position: { x: event.clientX, y: event.clientY },
      type: 'edge',
      edgeId: edge.id
    });
  }, []);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
        e.preventDefault();
        useCanvasStore.getState().undo();
      } else if ((e.ctrlKey || e.metaKey) && (e.key === 'y' || (e.key === 'z' && e.shiftKey))) {
        e.preventDefault();
        useCanvasStore.getState().redo();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  if (!currentCanvasId) {
    return (
      <div className="flex-1 flex items-center justify-center bg-slate-950">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-slate-400 mb-2">No Canvas Selected</h2>
          <p className="text-slate-500">Create or select a canvas to get started</p>
        </div>
      </div>
    );
  }

  // Build hierarchy for collapse logic
  const hierarchyMap = buildHierarchy(nodes, edges);
  
  // Get all collapsed node IDs and their descendants
  const hiddenNodeIds = new Set<string>();
  Object.entries(collapseState).forEach(([nodeId, isCollapsed]) => {
    if (isCollapsed) {
      const descendants = getDescendants(nodeId, hierarchyMap);
      descendants.forEach(id => hiddenNodeIds.add(id));
    }
  });

  // Filter visible nodes and edges
  const visibleNodes = nodes.filter(node => !hiddenNodeIds.has(node.id));
  const visibleEdges = edges.filter(edge => 
    !hiddenNodeIds.has(edge.source) && !hiddenNodeIds.has(edge.target)
  );

  // Enhance nodes with handlers and highlight state
  const enhancedNodes = visibleNodes.map(node => {
    const isHighlighted = highlightedNodes.has(node.id);
    
    return {
      ...node,
      data: {
        ...node.data,
        onTagAdd: (tag: string) => addTagToNode(node.id, tag),
        onTagRemove: (tag: string) => removeTagFromNode(node.id, tag),
        onToggleCollapse: () => toggleCollapse(node.id),
        hasChildren: hasChildren(node.id, edges),
        collapsed: collapseState[node.id] || false,
        hiddenCount: collapseState[node.id] ? countDescendants(node.id, hierarchyMap) : 0,
        // Add update callbacks for node content
        onUpdateTitle: (title: string) => {
          useCanvasStore.getState().updateNode(node.id, { title });
        },
        onUpdateContent: (content: string) => {
          useCanvasStore.getState().updateNode(node.id, { content });
        },
        onUpdateCardData: (card_data: any) => {
          useCanvasStore.getState().updateNode(node.id, { card_data });
        },
        // Source attribution handler
        onSourceClick: () => {
          // If card has conflict, show conflict modal, otherwise show source details
          if (node.data?.hasConflict) {
            setConflictModal({ isOpen: true, nodeId: node.id });
          } else {
            setSourceDetailsModal({ isOpen: true, nodeId: node.id });
          }
        }
      },
      // Add visual highlight for search results
      style: {
        ...node.style,
        ...(isHighlighted && {
          boxShadow: '0 0 0 3px rgba(59, 130, 246, 0.5)',
          zIndex: 1000
        })
      }
    };
  });

  // Canvas context menu items
  const canvasMenuItems: MenuItem[] = [
    {
      label: 'Add Rich Text Note',
      icon: <FileText className="w-4 h-4" />,
      onClick: () => contextMenu && createNodeAtPosition(CardType.RICH_TEXT, contextMenu.position)
    },
    {
      label: 'Add Todo List',
      icon: <CheckSquare className="w-4 h-4" />,
      onClick: () => contextMenu && createNodeAtPosition(CardType.TODO, contextMenu.position)
    },
    {
      label: 'Add Video',
      icon: <Video className="w-4 h-4" />,
      onClick: () => contextMenu && createNodeAtPosition(CardType.VIDEO, contextMenu.position)
    },
    {
      label: 'Add Link',
      icon: <LinkIcon className="w-4 h-4" />,
      onClick: () => contextMenu && createNodeAtPosition(CardType.LINK, contextMenu.position)
    },
    {
      label: 'Add Reminder',
      icon: <Clock className="w-4 h-4" />,
      onClick: () => contextMenu && createNodeAtPosition(CardType.REMINDER, contextMenu.position)
    }
  ];

  // Node context menu items
  const getNodeMenuItems = (nodeId: string): MenuItem[] => {
    const { duplicateNode, changeNodeType, deleteNode, handleGrow, activeGrowOperations } = useCanvasStore.getState();
    
    // Find the node to check if it has content
    const node = nodes.find(n => n.id === nodeId);
    const hasContent = node?.data?.content && 
      typeof node.data.content === 'string' && 
      node.data.content.trim().length > 10;
    
    // Check if this card is currently being grown
    const isGrowing = activeGrowOperations?.has(nodeId);
    
    const menuItems: MenuItem[] = [
      {
        label: 'Change Type',
        submenu: [
          {
            label: 'Rich Text Note',
            icon: <FileText className="w-4 h-4" />,
            onClick: () => changeNodeType(nodeId, 'rich_text')
          },
          {
            label: 'Todo List',
            icon: <CheckSquare className="w-4 h-4" />,
            onClick: () => changeNodeType(nodeId, 'todo')
          },
          {
            label: 'Video',
            icon: <Video className="w-4 h-4" />,
            onClick: () => changeNodeType(nodeId, 'video')
          },
          {
            label: 'Link',
            icon: <LinkIcon className="w-4 h-4" />,
            onClick: () => changeNodeType(nodeId, 'link')
          },
          {
            label: 'Reminder',
            icon: <Clock className="w-4 h-4" />,
            onClick: () => changeNodeType(nodeId, 'reminder')
          }
        ]
      },
      {
        label: 'Duplicate',
        onClick: () => duplicateNode(nodeId)
      }
    ];
    
    // Add Grow option if card has content
    if (hasContent) {
      menuItems.push({
        label: isGrowing ? 'Growing...' : 'Grow',
        icon: isGrowing ? 
          <Loader2 className="w-4 h-4 animate-spin" /> : 
          <Sparkles className="w-4 h-4" />,
        onClick: () => {
          if (!isGrowing && handleGrow) {
            handleGrow(nodeId);
          }
        }
      });
      
      // Add Learning submenu
      menuItems.push({
        label: 'Learning',
        icon: <GraduationCap className="w-4 h-4" />,
        submenu: [
          {
            label: 'Comprehensive Learn',
            icon: <Sparkles className="w-4 h-4" />,
            onClick: () => {
              useCanvasStore.getState().handleComprehensiveLearn(nodeId);
            }
          },
          { divider: true },
          {
            label: 'Find Knowledge Gaps',
            icon: <Search className="w-4 h-4" />,
            onClick: () => {
              useCanvasStore.getState().executeLearningAction('find-gaps', nodeId);
            }
          },
          {
            label: 'Explain Like I\'m 5',
            icon: <Lightbulb className="w-4 h-4" />,
            onClick: () => {
              useCanvasStore.getState().executeLearningAction('simplify', nodeId);
            }
          },
          {
            label: 'Go Deeper',
            icon: <BookOpen className="w-4 h-4" />,
            onClick: () => {
              useCanvasStore.getState().executeLearningAction('go-deeper', nodeId);
            }
          },
          {
            label: 'Find Examples',
            icon: <Target className="w-4 h-4" />,
            onClick: () => {
              useCanvasStore.getState().executeLearningAction('find-examples', nodeId);
            }
          },
          {
            label: 'Challenge This',
            icon: <AlertCircle className="w-4 h-4" />,
            onClick: () => {
              useCanvasStore.getState().executeLearningAction('challenge', nodeId);
            }
          },
          {
            label: 'Connect the Dots',
            icon: <Network className="w-4 h-4" />,
            onClick: () => {
              useCanvasStore.getState().executeLearningAction('connect-dots', nodeId);
            }
          },
          {
            label: 'Update Me',
            icon: <RefreshCw className="w-4 h-4" />,
            onClick: () => {
              useCanvasStore.getState().executeLearningAction('update', nodeId);
            }
          },
          {
            label: 'Translate to Action',
            icon: <CheckCircle className="w-4 h-4" />,
            onClick: () => {
              useCanvasStore.getState().executeLearningAction('action-plan', nodeId);
            }
          }
        ]
      });
    }
    
    menuItems.push(
      { divider: true },
      {
        label: 'Delete',
        danger: true,
        onClick: () => deleteNode(nodeId)
      }
    );
    
    return menuItems;
  };

  // Edge context menu items
  const getEdgeMenuItems = (edgeId: string): MenuItem[] => {
    return [
      {
        label: 'Delete Connection',
        icon: <Network className="w-4 h-4" />,
        onClick: async () => {
          try {
            await deleteEdge(edgeId);
          } catch (error) {
            console.error('Failed to delete edge:', error);
          }
        },
        danger: true
      }
    ];
  };

  return (
    <div className="flex-1 h-full">
      {/* Keyboard Shortcuts Handler */}
      <KeyboardHandler />
      
      {/* Search Panel */}
      <SearchPanel />
      
      <ReactFlow
        nodes={enhancedNodes}
        edges={visibleEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onPaneClick={(e) => {
          if (e.detail === 2) {
            handlePaneDoubleClick(e as any);
          }
        }}
        onPaneContextMenu={handlePaneContextMenu}
        onNodeContextMenu={handleNodeContextMenu}
        onEdgeContextMenu={handleEdgeContextMenu}
        edgesSelectable={true}
        nodesSelectable={true}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        defaultEdgeOptions={edgeOptions}
        connectionMode={ConnectionMode.Loose}
        fitView
        className="bg-slate-950"
        minZoom={0.1}
        maxZoom={2}
      >
        <Background
          variant={BackgroundVariant.Dots}
          gap={20}
          size={1}
          color="#1e293b"
        />
        <Controls className="bg-slate-800 border-slate-700" />
        <MiniMap
          className="bg-slate-800 border-slate-700"
          nodeColor="#334155"
          maskColor="rgba(15, 23, 42, 0.8)"
        />
      </ReactFlow>

      {/* Context Menu */}
      {contextMenu && contextMenu.type === 'canvas' && (
        <ContextMenu
          position={contextMenu.position}
          items={canvasMenuItems}
          onClose={() => setContextMenu(null)}
        />
      )}
      
      {contextMenu && contextMenu.type === 'node' && contextMenu.nodeId && (
        <ContextMenu
          position={contextMenu.position}
          items={getNodeMenuItems(contextMenu.nodeId)}
          onClose={() => setContextMenu(null)}
        />
      )}

      {contextMenu && contextMenu.type === 'edge' && contextMenu.edgeId && (
        <ContextMenu
          position={contextMenu.position}
          items={getEdgeMenuItems(contextMenu.edgeId)}
          onClose={() => setContextMenu(null)}
        />
      )}

      {/* Source Details Modal */}
      {sourceDetailsModal.isOpen && sourceDetailsModal.nodeId && (() => {
        const node = nodes.find(n => n.id === sourceDetailsModal.nodeId);
        if (!node) return null;
        
        return (
          <SourceDetailsModal
            isOpen={sourceDetailsModal.isOpen}
            onClose={() => setSourceDetailsModal({ isOpen: false })}
            cardTitle={node.data?.title || 'Untitled'}
            sourceType={node.data?.sourceType}
            sourceUrl={node.data?.sourceUrl}
            extractedAt={node.data?.extractedAt}
            extractionMethod={node.data?.extractionMethod}
            sources={node.data?.sources}
            hasConflict={node.data?.hasConflict}
            conflictDetails={node.data?.conflictDetails}
          />
        );
      })()}

      {/* Conflict Comparison Modal */}
      {conflictModal.isOpen && conflictModal.nodeId && (() => {
        const node = nodes.find(n => n.id === conflictModal.nodeId);
        if (!node) return null;
        
        // Find conflicting cards (for now, mock data - would come from backend)
        const conflictingCards = nodes
          .filter(n => n.id !== node.id && n.data?.hasConflict)
          .slice(0, 3)
          .map(n => ({
            id: n.id,
            title: n.data?.title || 'Untitled',
            content: n.data?.content || '',
            tags: n.data?.tags || [],
            sourceUrl: n.data?.sourceUrl,
            sourceType: n.data?.sourceType
          }));
        
        if (conflictingCards.length === 0) return null;
        
        return (
          <ConflictComparisonModal
            isOpen={conflictModal.isOpen}
            onClose={() => setConflictModal({ isOpen: false })}
            currentCard={{
              id: node.id,
              title: node.data?.title || 'Untitled',
              content: node.data?.content || '',
              tags: node.data?.tags || [],
              sourceUrl: node.data?.sourceUrl,
              sourceType: node.data?.sourceType
            }}
            conflictingCards={conflictingCards}
            conflictType={node.data?.conflictType || 'contradiction'}
            similarity={node.data?.conflictSimilarity || 0.7}
            onMerge={(cardId1, cardId2) => {
              useCanvasStore.getState().mergeCards(cardId1, cardId2);
              setConflictModal({ isOpen: false });
            }}
          />
        );
      })()}
    </div>
  );
};
