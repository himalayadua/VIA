/**
 * Source Attribution Utilities
 * 
 * Helpers for displaying source information on cards
 */

export type SourceType = 'url' | 'ai_generated' | 'manual';

export interface SourceInfo {
  url?: string;
  type?: string;
  extracted_at?: string;
  contribution?: number;
}

/**
 * Get icon for source type
 */
export function getSourceIcon(sourceType: SourceType): string {
  switch (sourceType) {
    case 'url':
      return '🔗';
    case 'ai_generated':
      return '🤖';
    case 'manual':
      return '✍️';
    default:
      return '📝';
  }
}

/**
 * Get color class for source type
 */
export function getSourceColor(sourceType: SourceType): string {
  switch (sourceType) {
    case 'url':
      return 'bg-blue-500/20 text-blue-300 border-blue-500/30';
    case 'ai_generated':
      return 'bg-purple-500/20 text-purple-300 border-purple-500/30';
    case 'manual':
      return 'bg-slate-500/20 text-slate-300 border-slate-500/30';
    default:
      return 'bg-slate-500/20 text-slate-300 border-slate-500/30';
  }
}

/**
 * Get display name for source type
 */
export function getSourceDisplayName(sourceType: SourceType): string {
  switch (sourceType) {
    case 'url':
      return 'From URL';
    case 'ai_generated':
      return 'AI Generated';
    case 'manual':
      return 'Manual';
    default:
      return 'Unknown';
  }
}

/**
 * Get short URL display (hostname only)
 */
export function getShortUrl(url: string): string {
  try {
    const urlObj = new URL(url);
    return urlObj.hostname.replace('www.', '');
  } catch {
    return url;
  }
}

/**
 * Format extraction date
 */
export function formatExtractionDate(dateString: string): string {
  try {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    
    return date.toLocaleDateString();
  } catch {
    return dateString;
  }
}

/**
 * Check if card has conflict
 */
export function hasConflict(hasConflict?: boolean): boolean {
  return hasConflict === true;
}

/**
 * Get conflict badge info
 */
export function getConflictBadge() {
  return {
    icon: '⚠️',
    text: 'Conflict',
    color: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30'
  };
}
