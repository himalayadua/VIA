/**
 * Card Type Utilities
 * 
 * Constants and utilities for card type icons and colors
 */

export const CARD_TYPE_ICONS: Record<string, string> = {
  question: '❓',
  todo: '✓',
  reminder: '⏰',
  person: '👤',
  concept: '💡',
  technique: '🔧',
  contradiction: '⚠️',
  example: '📝',
  challenge: '🎯',
  default: ''
};

export const CLUSTER_COLORS: Record<string, string> = {
  question: '#A78BFA',      // Purple
  todo: '#34D399',          // Green
  reminder: '#FCD34D',      // Yellow
  person: '#60A5FA',        // Blue
  concept: '#F472B6',       // Pink
  technique: '#FB923C',     // Orange
  contradiction: '#EF4444', // Red
  example: '#10B981',       // Emerald
  challenge: '#8B5CF6',     // Violet
  default: '#64748B'        // Slate
};

export function getCardTypeIcon(cardType: string): string {
  return CARD_TYPE_ICONS[cardType] || CARD_TYPE_ICONS.default;
}

export function getClusterColor(cardType: string): string {
  return CLUSTER_COLORS[cardType] || CLUSTER_COLORS.default;
}
