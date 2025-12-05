/**
 * CardsSummary Component
 * 
 * Displays a summary of cards created from content extraction
 */

import { useState } from 'react';
import { CheckCircle, Eye, ChevronRight, ExternalLink } from 'lucide-react';
import { useCanvasStore } from '../../store/canvasStore';

interface CardInfo {
  id: string;
  title: string;
  type: string;
  parent_id?: string | null;
}

interface CardsSummaryProps {
  cards: CardInfo[];
  sourceUrl?: string;
  operationType?: string;
}

export const CardsSummary = ({ cards, sourceUrl, operationType }: CardsSummaryProps) => {
  const { nodes, reactFlowInstance } = useCanvasStore();

  // Build hierarchy
  const buildHierarchy = () => {
    const rootCards = cards.filter(c => !c.parent_id);
    const childrenMap = new Map<string, CardInfo[]>();

    cards.forEach(card => {
      if (card.parent_id) {
        if (!childrenMap.has(card.parent_id)) {
          childrenMap.set(card.parent_id, []);
        }
        childrenMap.get(card.parent_id)!.push(card);
      }
    });

    return { rootCards, childrenMap };
  };

  const { rootCards, childrenMap } = buildHierarchy();

  // Navigate to card on canvas
  const handleViewCard = (cardId: string) => {
    if (!reactFlowInstance) return;

    const node = nodes.find(n => n.id === cardId);
    if (node) {
      // Center and zoom to the card
      reactFlowInstance.setCenter(node.position.x, node.position.y, {
        zoom: 1.5,
        duration: 800
      });

      // Highlight the card temporarily
      const cardElement = document.querySelector(`[data-id="${cardId}"]`);
      if (cardElement) {
        cardElement.classList.add('ring-2', 'ring-blue-500', 'ring-offset-2', 'ring-offset-slate-950');
        setTimeout(() => {
          cardElement.classList.remove('ring-2', 'ring-blue-500', 'ring-offset-2', 'ring-offset-slate-950');
        }, 2000);
      }
    }
  };

  // View all cards on canvas
  const handleViewAll = () => {
    if (!reactFlowInstance || cards.length === 0) return;

    const cardIds = cards.map(c => c.id);
    const cardNodes = nodes.filter(n => cardIds.includes(n.id));

    if (cardNodes.length > 0) {
      reactFlowInstance.fitView({
        nodes: cardNodes.map(n => ({ id: n.id })),
        padding: 0.2,
        duration: 800
      });
    }
  };

  return (
    <div className="bg-gradient-to-br from-green-900/20 to-blue-900/20 border border-green-700/50 rounded-lg p-4 space-y-3">
      {/* Header */}
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-green-500/20 flex items-center justify-center">
          <CheckCircle className="w-5 h-5 text-green-400" />
        </div>
        <div className="flex-1">
          <h3 className="text-sm font-semibold text-green-400">
            Content Extracted Successfully
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Created {cards.length} card{cards.length !== 1 ? 's' : ''} from {operationType || 'content'}
          </p>
          {sourceUrl && (
            <a
              href={sourceUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1 mt-1"
            >
              <span className="truncate max-w-[200px]">{sourceUrl}</span>
              <ExternalLink className="w-3 h-3 flex-shrink-0" />
            </a>
          )}
        </div>
      </div>

      {/* Cards List */}
      <div className="space-y-2">
        {rootCards.map(card => (
          <CardItem
            key={card.id}
            card={card}
            children={childrenMap.get(card.id) || []}
            onViewCard={handleViewCard}
            level={0}
          />
        ))}
      </div>

      {/* View All Button */}
      <button
        onClick={handleViewAll}
        className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors text-sm font-medium"
      >
        <Eye className="w-4 h-4" />
        View All on Canvas
      </button>
    </div>
  );
};

interface CardItemProps {
  card: CardInfo;
  children: CardInfo[];
  onViewCard: (cardId: string) => void;
  level: number;
}

const CardItem = ({ card, children, onViewCard, level }: CardItemProps) => {
  const [isExpanded, setIsExpanded] = useState(children.length > 0);

  const indent = level * 16;

  return (
    <div>
      <button
        onClick={() => {
          if (children.length > 0) {
            setIsExpanded(!isExpanded);
          } else {
            onViewCard(card.id);
          }
        }}
        className="w-full flex items-center gap-2 px-3 py-2 bg-slate-800/50 hover:bg-slate-800 rounded-lg transition-colors text-left group"
        style={{ paddingLeft: `${12 + indent}px` }}
      >
        {children.length > 0 && (
          <ChevronRight
            className={`w-3 h-3 text-slate-400 transition-transform flex-shrink-0 ${
              isExpanded ? 'rotate-90' : ''
            }`}
          />
        )}
        <span className="text-sm text-slate-200 flex-1 truncate">
          {card.title || 'Untitled'}
        </span>
        <span className="text-xs text-slate-500 px-2 py-0.5 bg-slate-700 rounded">
          {card.type}
        </span>
        <Eye
          className="w-3 h-3 text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0"
          onClick={(e) => {
            e.stopPropagation();
            onViewCard(card.id);
          }}
        />
      </button>

      {/* Children */}
      {isExpanded && children.length > 0 && (
        <div className="mt-1 space-y-1">
          {children.map(child => (
            <CardItem
              key={child.id}
              card={child}
              children={[]}
              onViewCard={onViewCard}
              level={level + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
};
