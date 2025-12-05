/**
 * Card Reference Utilities
 * 
 * Utilities for detecting and handling card references in chat messages
 */

export interface CardReference {
  cardId: string;
  displayText: string;
  startIndex: number;
  endIndex: number;
}

/**
 * Detect card references in text
 * Supports patterns like:
 * - [CARD:card_id]
 * - [CARD:card_id:Display Text]
 * - card-123
 * - #card-123
 */
export function detectCardReferences(text: string): CardReference[] {
  const references: CardReference[] = [];
  
  // Pattern 1: [CARD:card_id] or [CARD:card_id:Display Text]
  const cardPattern = /\[CARD:([a-zA-Z0-9-]+)(?::([^\]]+))?\]/g;
  let match;
  
  while ((match = cardPattern.exec(text)) !== null) {
    references.push({
      cardId: match[1],
      displayText: match[2] || `Card ${match[1].slice(0, 8)}`,
      startIndex: match.index,
      endIndex: match.index + match[0].length
    });
  }
  
  // Pattern 2: card-uuid or #card-uuid (standalone)
  const standalonePattern = /#?(card-[a-zA-Z0-9-]+)/g;
  
  while ((match = standalonePattern.exec(text)) !== null) {
    // Check if this is already captured by the CARD pattern
    const alreadyCaptured = references.some(
      ref => ref.startIndex <= match.index && ref.endIndex >= match.index
    );
    
    if (!alreadyCaptured) {
      references.push({
        cardId: match[1],
        displayText: match[1].slice(0, 12),
        startIndex: match.index,
        endIndex: match.index + match[0].length
      });
    }
  }
  
  return references.sort((a, b) => a.startIndex - b.startIndex);
}

/**
 * Replace card references with React components
 * Returns array of text segments and card reference objects
 */
export function parseTextWithCardReferences(text: string): Array<{ type: 'text' | 'card'; content: string | CardReference }> {
  const references = detectCardReferences(text);
  
  if (references.length === 0) {
    return [{ type: 'text', content: text }];
  }
  
  const segments: Array<{ type: 'text' | 'card'; content: string | CardReference }> = [];
  let lastIndex = 0;
  
  references.forEach(ref => {
    // Add text before reference
    if (ref.startIndex > lastIndex) {
      segments.push({
        type: 'text',
        content: text.slice(lastIndex, ref.startIndex)
      });
    }
    
    // Add card reference
    segments.push({
      type: 'card',
      content: ref
    });
    
    lastIndex = ref.endIndex;
  });
  
  // Add remaining text
  if (lastIndex < text.length) {
    segments.push({
      type: 'text',
      content: text.slice(lastIndex)
    });
  }
  
  return segments;
}

/**
 * Extract all card IDs from text
 */
export function extractCardIds(text: string): string[] {
  const references = detectCardReferences(text);
  return references.map(ref => ref.cardId);
}
