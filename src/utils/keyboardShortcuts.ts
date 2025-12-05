import { Node } from 'reactflow';

export interface KeyboardShortcut {
  key: string;
  ctrl?: boolean;
  shift?: boolean;
  alt?: boolean;
  meta?: boolean;
  action: (selectedNodes: Node[]) => void;
  description: string;
  preventDefault?: boolean;
}

export const KEYBOARD_SHORTCUTS: KeyboardShortcut[] = [
  {
    key: 'Tab',
    action: () => {
      // Create child node - implemented in KeyboardHandler
    },
    description: 'Create child node',
    preventDefault: true
  },
  {
    key: 'Enter',
    action: () => {
      // Create sibling node - implemented in KeyboardHandler
    },
    description: 'Create sibling node',
    preventDefault: true
  },
  {
    key: 'Delete',
    action: () => {
      // Delete selected nodes - implemented in KeyboardHandler
    },
    description: 'Delete selected nodes',
    preventDefault: true
  },
  {
    key: 'Backspace',
    action: () => {
      // Delete selected nodes - implemented in KeyboardHandler
    },
    description: 'Delete selected nodes',
    preventDefault: true
  },
  {
    key: 'd',
    ctrl: true,
    meta: true, // Command on Mac
    action: () => {
      // Duplicate selected nodes - implemented in KeyboardHandler
    },
    description: 'Duplicate selected nodes',
    preventDefault: true
  },
  {
    key: 'Escape',
    action: () => {
      // Clear selection - implemented in KeyboardHandler
    },
    description: 'Clear selection / Cancel editing',
    preventDefault: false
  },
  {
    key: 'f',
    ctrl: true,
    meta: true,
    action: () => {
      // Open search - will be implemented in Task 13
    },
    description: 'Open search',
    preventDefault: true
  },
  {
    key: 'k',
    ctrl: true,
    meta: true,
    action: () => {
      // Toggle chat assistant
    },
    description: 'Toggle chat assistant',
    preventDefault: true
  },
  {
    key: 'l',
    ctrl: true,
    meta: true,
    action: () => {
      // Apply auto-layout - will be implemented in Task 8
    },
    description: 'Apply auto-layout',
    preventDefault: true
  }
];

/**
 * Check if a keyboard event matches a shortcut
 */
export function matchesShortcut(event: KeyboardEvent, shortcut: KeyboardShortcut): boolean {
  const keyMatches = event.key.toLowerCase() === shortcut.key.toLowerCase();
  const shiftMatches = shortcut.shift ? event.shiftKey : !event.shiftKey;
  const altMatches = shortcut.alt ? event.altKey : !event.altKey;
  
  // For Mac compatibility, check both ctrl and meta
  const modifierMatches = shortcut.ctrl || shortcut.meta
    ? (event.ctrlKey || event.metaKey)
    : (!event.ctrlKey && !event.metaKey);

  return keyMatches && modifierMatches && shiftMatches && altMatches;
}

/**
 * Check if the user is currently editing text
 */
export function isEditingText(): boolean {
  const activeElement = document.activeElement;
  if (!activeElement) return false;

  const tagName = activeElement.tagName.toLowerCase();
  const isContentEditable = activeElement.getAttribute('contenteditable') === 'true';
  
  return (
    tagName === 'input' ||
    tagName === 'textarea' ||
    isContentEditable
  );
}

/**
 * Get shortcut display string for UI
 */
export function getShortcutDisplay(shortcut: KeyboardShortcut): string {
  const parts: string[] = [];
  
  const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
  
  if (shortcut.ctrl || shortcut.meta) {
    parts.push(isMac ? '⌘' : 'Ctrl');
  }
  if (shortcut.shift) {
    parts.push(isMac ? '⇧' : 'Shift');
  }
  if (shortcut.alt) {
    parts.push(isMac ? '⌥' : 'Alt');
  }
  
  // Capitalize first letter of key
  const key = shortcut.key.charAt(0).toUpperCase() + shortcut.key.slice(1);
  parts.push(key);
  
  return parts.join(isMac ? '' : '+');
}
