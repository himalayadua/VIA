import { useState, useEffect } from 'react';
import { ReactFlowProvider } from 'reactflow';
import { FolderOpen } from 'lucide-react';
import { Toolbar } from './components/Toolbar';
import { Canvas } from './components/Canvas';
import { ChatSidebar } from './components/chat/ChatSidebar';
import { CanvasManager } from './components/CanvasManager';
import { TemporalView } from './components/TemporalView';
import { useCanvasStore } from './store/canvasStore';
import './styles/grow-animations.css';
import './styles/conflict-animations.css';
import './styles/card-reference.css';
import './styles/learning-engagement.css';

function App() {
  const [showCanvasManager, setShowCanvasManager] = useState(false);
  const { sidebarWidth, setSidebarWidth, viewMode, currentCanvasId } = useCanvasStore();

  useEffect(() => {
    console.log('[App] showCanvasManager changed:', showCanvasManager);
  }, [showCanvasManager]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'o') {
        e.preventDefault();
        setShowCanvasManager(true);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <ReactFlowProvider>
      <div className={`h-screen flex flex-col bg-slate-950 ${viewMode === 'mindmap' ? 'overflow-hidden' : ''}`}>
        <Toolbar />

        <div className="flex-1 flex pt-[57px]" style={{ paddingRight: `${sidebarWidth}px` }}>
          {!currentCanvasId ? (
            <div className="flex-1 flex flex-col items-center justify-center">
              <div className="text-center mb-8">
                <h1 className="text-4xl font-bold text-slate-100 mb-4">Welcome to Via Canvas</h1>
                <p className="text-xl text-slate-400 mb-8">
                  An infinite mind-mapping and temporal visualization tool
                </p>
              </div>
              <button
                onClick={() => setShowCanvasManager(true)}
                className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 rounded-lg transition-colors flex items-center gap-3 text-lg font-semibold"
              >
                <FolderOpen className="w-6 h-6" />
                Open Canvas Manager
              </button>
              <p className="text-slate-500 mt-4 text-sm">or press Ctrl+O</p>
            </div>
          ) : viewMode === 'mindmap' ? (
            <Canvas />
          ) : (
            <TemporalView />
          )}
        </div>

        <ChatSidebar width={sidebarWidth} onResize={setSidebarWidth} canvasId={currentCanvasId} />

        {showCanvasManager && (
          <div style={{ position: 'fixed', inset: 0, zIndex: 9999 }}>
            <CanvasManager 
              onClose={() => {
                console.log('[App] CanvasManager onClose called');
                setShowCanvasManager(false);
              }} 
            />
          </div>
        )}

        <button
          onClick={() => setShowCanvasManager(true)}
          className="fixed bottom-4 left-4 bg-slate-800 hover:bg-slate-700 text-slate-200 p-3 rounded-full shadow-lg transition-colors z-10"
          title="Open Canvas Manager (Ctrl+O)"
        >
          <FolderOpen className="w-6 h-6" />
        </button>
      </div>
    </ReactFlowProvider>
  );
}

export default App;
