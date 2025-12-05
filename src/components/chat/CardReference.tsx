/**
 * CardReference Component
 * 
 * Clickable card reference that highlights and brings the card into view
 */

import { ExternalLink, MapPin } from 'lucide-react';
import { useCanvasStore } from '../../store/canvasStore';
import { useReactFlow } from 'reactflow';

interface CardReferenceProps {
  cardId: string;
  displayText: string;
}

export const CardReference = ({ cardId, displayText }: CardReferenceProps) => {
  const { nodes, setSelectedNode } = useCanvasStore();
  const reactFlowInstance = useReactFlow();
  
  const card = nodes.find(n => n.id === cardId);
  
  const handleClick = async () => {
    if (!card) {
      console.warn(`Card ${cardId} not found on canvas`);
      return;
    }
    
    try {
      // Track engagement when card reference is clicked
      await useCanvasStore.getState().incrementReadCount(cardId);
      
      // Select the card (this will also increment read count, but that's ok - double counting shows engagement)
      setSelectedNode(cardId);
      
      // Bring card into view with smooth animation
      reactFlowInstance.setCenter(
        card.position.x + 150, // Center of typical card
        card.position.y + 100,
        { zoom: 1.2, duration: 800 }
      );
      
      // Highlight the card temporarily
      const cardElement = document.querySelector(`[data-id="${cardId}"]`);
      if (cardElement) {
        cardElement.classList.add('card-reference-highlight');
        setTimeout(() => {
          cardElement.classList.remove('card-reference-highlight');
        }, 2000);
      }
    } catch (error) {
      console.error('Error navigating to card:', error);
    }
  };
  
  if (!card) {
    // Card not found - show as disabled reference
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-slate-700/50 text-slate-400 text-sm font-mono cursor-not-allowed">
        <ExternalLink className="w-3 h-3" />
        {displayText}
        <span className="text-xs">(not found)</span>
      </span>
    );
  }
  
  return (
    <button
      onClick={handleClick}
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 hover:text-blue-300 text-sm font-mono transition-colors cursor-pointer border border-blue-500/30 hover:border-blue-500/50"
      title={`Go to: ${card.data.title || displayText}`}
    >
      <MapPin className="w-3 h-3" />
      {displayText}
    </button>
  );
};
