import { Download, Upload, Undo, Redo, Save, Search, Clock, Map, Network, MessageSquare } from 'lucide-react';
import { useCanvasStore } from '../store/canvasStore';
import { useSearchStore } from '../store/searchStore';
import { useChatStore } from '../store/chatStore';
import { useRef, useState } from 'react';
import { LayoutAlgorithm } from '../utils/layoutAlgorithms';

export const Toolbar = () => {
  const {
    undo,
    redo,
    saveCanvas,
    exportCanvas,
    importCanvas,
    viewMode,
    setViewMode,
    canvasName,
    applyLayoutToCanvas
  } = useCanvasStore();
  const { openSearch } = useSearchStore();
  const { toggleSidebar, isSidebarOpen } = useChatStore();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [showLayoutMenu, setShowLayoutMenu] = useState(false);
  const [isApplyingLayout, setIsApplyingLayout] = useState(false);

  const handleExport = () => {
    const data = exportCanvas();
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${canvasName.replace(/\s+/g, '_')}_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleImport = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async (event) => {
      const content = event.target?.result as string;
      await importCanvas(content);
    };
    reader.readAsText(file);
  };

  const handleApplyLayout = async (algorithm: LayoutAlgorithm) => {
    setIsApplyingLayout(true);
    setShowLayoutMenu(false);
    
    try {
      await applyLayoutToCanvas(algorithm);
    } catch (error) {
      console.error('Failed to apply layout:', error);
    } finally {
      setIsApplyingLayout(false);
    }
  };

  return (
    <div className="fixed top-0 left-0 right-0 bg-slate-900 border-b border-slate-700 px-4 py-3 flex items-center justify-between z-20">
      <div className="flex items-center gap-4">
        <h1 className="text-xl font-bold text-slate-100">Via Canvas</h1>
        <span className="text-slate-400">|</span>
        <span className="text-slate-300 font-medium">{canvasName}</span>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={undo}
          className="p-2 hover:bg-slate-800 rounded transition-colors group"
          title="Undo (Ctrl+Z)"
        >
          <Undo className="w-5 h-5 text-slate-400 group-hover:text-slate-100" />
        </button>
        <button
          onClick={redo}
          className="p-2 hover:bg-slate-800 rounded transition-colors group"
          title="Redo (Ctrl+Y)"
        >
          <Redo className="w-5 h-5 text-slate-400 group-hover:text-slate-100" />
        </button>

        <div className="w-px h-6 bg-slate-700 mx-2" />

        <button
          onClick={() => setViewMode(viewMode === 'mindmap' ? 'temporal' : 'mindmap')}
          className={`p-2 hover:bg-slate-800 rounded transition-colors group ${
            viewMode === 'temporal' ? 'bg-slate-800' : ''
          }`}
          title={`Switch to ${viewMode === 'mindmap' ? 'Temporal' : 'Mind Map'} View`}
        >
          {viewMode === 'mindmap' ? (
            <Clock className="w-5 h-5 text-slate-400 group-hover:text-slate-100" />
          ) : (
            <Map className="w-5 h-5 text-slate-400 group-hover:text-slate-100" />
          )}
        </button>

        <div className="w-px h-6 bg-slate-700 mx-2" />

        <button
          onClick={saveCanvas}
          className="p-2 hover:bg-slate-800 rounded transition-colors group"
          title="Save Canvas"
        >
          <Save className="w-5 h-5 text-slate-400 group-hover:text-slate-100" />
        </button>
        <button
          onClick={handleExport}
          className="p-2 hover:bg-slate-800 rounded transition-colors group"
          title="Export Canvas"
        >
          <Download className="w-5 h-5 text-slate-400 group-hover:text-slate-100" />
        </button>
        <button
          onClick={handleImport}
          className="p-2 hover:bg-slate-800 rounded transition-colors group"
          title="Import Canvas"
        >
          <Upload className="w-5 h-5 text-slate-400 group-hover:text-slate-100" />
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".json"
          onChange={handleFileChange}
          className="hidden"
        />

        <div className="w-px h-6 bg-slate-700 mx-2" />

        <div className="relative">
          <button
            onClick={() => setShowLayoutMenu(!showLayoutMenu)}
            disabled={isApplyingLayout}
            className={`p-2 hover:bg-slate-800 rounded transition-colors group ${
              isApplyingLayout ? 'opacity-50 cursor-not-allowed' : ''
            }`}
            title="Auto Layout (Ctrl+L)"
          >
            <Network className={`w-5 h-5 text-slate-400 group-hover:text-slate-100 ${
              isApplyingLayout ? 'animate-spin' : ''
            }`} />
          </button>

          {showLayoutMenu && (
            <div className="absolute top-full right-0 mt-2 bg-slate-800 border border-slate-700 rounded-lg shadow-2xl py-1 min-w-[160px] z-50">
              <button
                onClick={() => handleApplyLayout('tree')}
                className="w-full px-4 py-2 text-left text-sm text-slate-200 hover:bg-slate-700 transition-colors"
              >
                Tree Layout
              </button>
              <button
                onClick={() => handleApplyLayout('force')}
                className="w-full px-4 py-2 text-left text-sm text-slate-200 hover:bg-slate-700 transition-colors"
              >
                Force-Directed
              </button>
              <button
                onClick={() => handleApplyLayout('circular')}
                className="w-full px-4 py-2 text-left text-sm text-slate-200 hover:bg-slate-700 transition-colors"
              >
                Circular Layout
              </button>
            </div>
          )}
        </div>

        <button
          onClick={openSearch}
          className="p-2 hover:bg-slate-800 rounded transition-colors group"
          title="Search (Ctrl+F)"
        >
          <Search className="w-5 h-5 text-slate-400 group-hover:text-slate-100" />
        </button>

        <button
          onClick={toggleSidebar}
          className={`p-2 hover:bg-slate-800 rounded transition-colors group ${
            isSidebarOpen ? 'bg-slate-800' : ''
          }`}
          title="Chat Assistant (Ctrl+K)"
        >
          <MessageSquare className="w-5 h-5 text-slate-400 group-hover:text-slate-100" />
        </button>
      </div>
    </div>
  );
};
