import { useEffect } from 'react';
import { useCanvasStore } from '../store/canvasStore';
import { useSearchStore } from '../store/searchStore';
import { useChatStore } from '../store/chatStore';
import { isEditingText } from '../utils/keyboardShortcuts';

export const KeyboardHandler = () => {
  const {
    createChildNode,
    createSiblingNode,
    deleteSelectedNodes,
    duplicateSelectedNodes,
    clearSelection,
    getSelectedNodes,
    applyLayoutToCanvas
  } = useCanvasStore();
  
  const { openSearch } = useSearchStore();
  const { toggleSidebar } = useChatStore();

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Skip if user is editing text
      if (isEditingText()) {
        return;
      }

      const selectedNodes = getSelectedNodes();
      
      // Tab - Create child node
      if (event.key === 'Tab' && selectedNodes.length === 1) {
        event.preventDefault();
        createChildNode(selectedNodes[0].id);
        return;
      }

      // Enter - Create sibling node
      if (event.key === 'Enter' && selectedNodes.length === 1) {
        event.preventDefault();
        createSiblingNode(selectedNodes[0].id);
        return;
      }

      // Delete or Backspace - Delete selected nodes
      if ((event.key === 'Delete' || event.key === 'Backspace') && selectedNodes.length > 0) {
        event.preventDefault();
        deleteSelectedNodes();
        return;
      }

      // Ctrl+D or Cmd+D - Duplicate selected nodes
      if (
        event.key.toLowerCase() === 'd' &&
        (event.ctrlKey || event.metaKey) &&
        selectedNodes.length > 0
      ) {
        event.preventDefault();
        duplicateSelectedNodes();
        return;
      }

      // Escape - Clear selection
      if (event.key === 'Escape') {
        clearSelection();
        return;
      }

      // Ctrl+F or Cmd+F - Open search
      if (
        event.key.toLowerCase() === 'f' &&
        (event.ctrlKey || event.metaKey)
      ) {
        event.preventDefault();
        openSearch();
        return;
      }

      // Ctrl+K or Cmd+K - Toggle chat assistant
      if (
        event.key.toLowerCase() === 'k' &&
        (event.ctrlKey || event.metaKey)
      ) {
        event.preventDefault();
        toggleSidebar();
        return;
      }

      // Ctrl+L or Cmd+L - Apply auto-layout
      if (
        event.key.toLowerCase() === 'l' &&
        (event.ctrlKey || event.metaKey)
      ) {
        event.preventDefault();
        applyLayoutToCanvas('tree'); // Default to tree layout
        return;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [
    createChildNode,
    createSiblingNode,
    deleteSelectedNodes,
    duplicateSelectedNodes,
    clearSelection,
    getSelectedNodes,
    applyLayoutToCanvas,
    openSearch,
    toggleSidebar
  ]);

  return null; // This component doesn't render anything
};
