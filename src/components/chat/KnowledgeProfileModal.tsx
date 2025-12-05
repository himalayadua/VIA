/**
 * Knowledge Profile Modal
 * 
 * Displays canvas statistics and knowledge profile
 */

import { X, Brain, Tag, Network, TrendingUp, AlertCircle } from 'lucide-react';
import { useCanvasStore } from '../../store/canvasStore';
import { useMemo } from 'react';

interface KnowledgeProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const KnowledgeProfileModal = ({ isOpen, onClose }: KnowledgeProfileModalProps) => {
  const { nodes, edges } = useCanvasStore();
  
  const stats = useMemo(() => {
    // Calculate statistics
    const totalCards = nodes.length;
    const totalConnections = edges.length;
    
    // Count by card type
    const cardTypes = nodes.reduce((acc, node) => {
      const type = node.data.cardType || 'rich_text';
      acc[type] = (acc[type] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
    
    // Extract all tags
    const allTags = nodes.flatMap(node => node.data.tags || []);
    const tagCounts = allTags.reduce((acc, tag) => {
      acc[tag] = (acc[tag] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
    
    // Top 5 tags
    const topTags = Object.entries(tagCounts)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 5);
    
    // Find most connected cards (hubs)
    const connectionCounts = nodes.map(node => {
      const connections = edges.filter(
        edge => edge.source === node.id || edge.target === node.id
      ).length;
      return { node, connections };
    }).sort((a, b) => b.connections - a.connections);
    
    const hubs = connectionCounts.slice(0, 3);
    
    // Find isolated cards (no connections)
    const isolatedCards = nodes.filter(node => {
      return !edges.some(edge => edge.source === node.id || edge.target === node.id);
    });
    
    // Calculate average connections per card
    const avgConnections = totalCards > 0 ? (totalConnections * 2 / totalCards).toFixed(1) : '0';
    
    return {
      totalCards,
      totalConnections,
      cardTypes,
      topTags,
      hubs,
      isolatedCards,
      avgConnections
    };
  }, [nodes, edges]);
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-slate-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-700">
          <div className="flex items-center gap-2">
            <Brain className="w-5 h-5 text-blue-400" />
            <h2 className="text-lg font-semibold text-slate-100">Knowledge Profile</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-slate-700 rounded transition-colors"
          >
            <X className="w-5 h-5 text-slate-400" />
          </button>
        </div>
        
        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          {/* Overview Stats */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-slate-900/50 rounded-lg p-4">
              <div className="text-slate-400 text-sm mb-1">Total Cards</div>
              <div className="text-2xl font-bold text-slate-100">{stats.totalCards}</div>
            </div>
            <div className="bg-slate-900/50 rounded-lg p-4">
              <div className="text-slate-400 text-sm mb-1">Connections</div>
              <div className="text-2xl font-bold text-slate-100">{stats.totalConnections}</div>
            </div>
            <div className="bg-slate-900/50 rounded-lg p-4">
              <div className="text-slate-400 text-sm mb-1">Avg Connections</div>
              <div className="text-2xl font-bold text-slate-100">{stats.avgConnections}</div>
            </div>
            <div className="bg-slate-900/50 rounded-lg p-4">
              <div className="text-slate-400 text-sm mb-1">Isolated Cards</div>
              <div className="text-2xl font-bold text-orange-400">{stats.isolatedCards.length}</div>
            </div>
          </div>
          
          {/* Card Types */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <Tag className="w-4 h-4 text-slate-400" />
              <h3 className="text-sm font-semibold text-slate-300">Card Types</h3>
            </div>
            <div className="space-y-2">
              {Object.entries(stats.cardTypes).map(([type, count]) => (
                <div key={type} className="flex items-center justify-between">
                  <span className="text-sm text-slate-400 capitalize">{type.replace('_', ' ')}</span>
                  <div className="flex items-center gap-2">
                    <div className="w-32 h-2 bg-slate-700 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-500"
                        style={{ width: `${(count / stats.totalCards) * 100}%` }}
                      />
                    </div>
                    <span className="text-sm text-slate-300 w-8 text-right">{count}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          {/* Top Tags */}
          {stats.topTags.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <TrendingUp className="w-4 h-4 text-slate-400" />
                <h3 className="text-sm font-semibold text-slate-300">Top Tags</h3>
              </div>
              <div className="flex flex-wrap gap-2">
                {stats.topTags.map(([tag, count]) => (
                  <div
                    key={tag}
                    className="px-3 py-1 bg-slate-700 rounded-full text-sm text-slate-300 flex items-center gap-2"
                  >
                    <span>{tag}</span>
                    <span className="text-xs text-slate-400">×{count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {/* Knowledge Hubs */}
          {stats.hubs.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <Network className="w-4 h-4 text-slate-400" />
                <h3 className="text-sm font-semibold text-slate-300">Knowledge Hubs</h3>
                <span className="text-xs text-slate-500">(Most Connected)</span>
              </div>
              <div className="space-y-2">
                {stats.hubs.map(({ node, connections }) => (
                  <div
                    key={node.id}
                    className="flex items-center justify-between p-2 bg-slate-900/50 rounded"
                  >
                    <span className="text-sm text-slate-300 truncate flex-1">
                      {node.data.title || 'Untitled'}
                    </span>
                    <span className="text-xs text-slate-400 ml-2">
                      {connections} connection{connections !== 1 ? 's' : ''}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {/* Isolated Cards Warning */}
          {stats.isolatedCards.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <AlertCircle className="w-4 h-4 text-orange-400" />
                <h3 className="text-sm font-semibold text-slate-300">Isolated Cards</h3>
                <span className="text-xs text-slate-500">(No Connections)</span>
              </div>
              <div className="text-sm text-slate-400 mb-2">
                {stats.isolatedCards.length} card{stats.isolatedCards.length !== 1 ? 's' : ''} without connections. 
                Consider linking them to related topics.
              </div>
              <div className="space-y-1 max-h-32 overflow-y-auto">
                {stats.isolatedCards.slice(0, 5).map(node => (
                  <div
                    key={node.id}
                    className="text-xs text-slate-500 truncate px-2 py-1 bg-slate-900/30 rounded"
                  >
                    {node.data.title || 'Untitled'}
                  </div>
                ))}
                {stats.isolatedCards.length > 5 && (
                  <div className="text-xs text-slate-500 px-2 py-1">
                    ...and {stats.isolatedCards.length - 5} more
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
        
        {/* Footer */}
        <div className="p-4 border-t border-slate-700 bg-slate-900/30">
          <p className="text-xs text-slate-500 text-center">
            This profile helps the AI understand your knowledge landscape and provide better recommendations.
          </p>
        </div>
      </div>
    </div>
  );
};
