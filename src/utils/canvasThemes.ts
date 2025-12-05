/**
 * Canvas Theme System
 * Provides consistent color themes for canvas cards in the Canvas Manager
 */

export interface CanvasTheme {
  gradient: string; // Tailwind gradient classes
  ring: string; // Ring color for active state
  name: string; // Theme name for reference
}

/**
 * 8 vibrant gradient themes for canvas cards
 */
export const CANVAS_THEMES: CanvasTheme[] = [
  {
    name: 'Emerald',
    gradient: 'from-emerald-500 to-emerald-700',
    ring: 'ring-emerald-500'
  },
  {
    name: 'Cyan',
    gradient: 'from-cyan-500 to-cyan-700',
    ring: 'ring-cyan-500'
  },
  {
    name: 'Rose',
    gradient: 'from-rose-500 to-rose-700',
    ring: 'ring-rose-500'
  },
  {
    name: 'Orange',
    gradient: 'from-orange-500 to-orange-700',
    ring: 'ring-orange-500'
  },
  {
    name: 'Amber',
    gradient: 'from-amber-500 to-amber-700',
    ring: 'ring-amber-500'
  },
  {
    name: 'Purple',
    gradient: 'from-purple-500 to-purple-700',
    ring: 'ring-purple-500'
  },
  {
    name: 'Pink',
    gradient: 'from-pink-500 to-pink-700',
    ring: 'ring-pink-500'
  },
  {
    name: 'Blue',
    gradient: 'from-blue-500 to-blue-700',
    ring: 'ring-blue-500'
  }
];

/**
 * Simple hash function to convert string to number
 */
function hashString(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  return Math.abs(hash);
}

/**
 * Get a consistent theme for a canvas based on its ID
 * The same canvas ID will always return the same theme
 */
export function getCanvasTheme(canvasId: string): CanvasTheme {
  const hash = hashString(canvasId);
  const index = hash % CANVAS_THEMES.length;
  return CANVAS_THEMES[index];
}

/**
 * Format canvas number with leading zero (01, 02, 03, etc.)
 */
export function formatCanvasNumber(index: number): string {
  return (index + 1).toString().padStart(2, '0');
}
