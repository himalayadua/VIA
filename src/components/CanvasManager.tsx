import React, { useState, useEffect, useRef, useCallback } from 'react';
import { api } from '../lib/api';
import { useCanvasStore } from '../store/canvasStore';

// Error boundary component
class CanvasManagerErrorBoundary extends React.Component<
  { children: React.ReactNode; onClose: () => void },
  { hasError: boolean; error: Error | null }
> {
  constructor(props: { children: React.ReactNode; onClose: () => void }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('[CanvasManager] Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="fixed inset-0 bg-black z-50 flex items-center justify-center">
          <div className="text-center">
            <p className="text-white text-xl mb-4">Error loading Canvas Manager</p>
            <p className="text-white/60 text-sm mb-4">{this.state.error?.message}</p>
            <button
              onClick={() => {
                this.setState({ hasError: false, error: null });
                this.props.onClose();
              }}
              className="px-4 py-2 bg-white/10 text-white rounded"
            >
              Close
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

interface CanvasItem {
  id: string;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
}

interface CanvasManagerProps {
  onClose: () => void;
}

// Available images from public/images folder
const CANVAS_IMAGES = [
  '/images/alain-bonnardeaux-xNuBvTXkdT4-unsplash.jpg',
  '/images/andry-roby-x29o6PFuAyg-unsplash.jpg',
  '/images/brice-cooper-33jyO4XRtOY-unsplash.jpg',
  '/images/leo_visions-jIvIRbtu77A-unsplash.jpg',
  '/images/lina-mican-_y8Xdkb_neA-unsplash.jpg',
  '/images/marco-grosso-ABGHh9toXUE-unsplash.jpg',
  '/images/marek-piwnicki-3wTFUr0wtbk-unsplash.jpg',
  '/images/mitch-mfcWa44Kv8o-unsplash.jpg',
  '/images/naomi-august-rr4-VsbNCX4-unsplash.jpg',
  '/images/nikolaos-anastasopoulos--cHHXSK2aME-unsplash.jpg',
  '/images/steve-busch-PjiRvYo-uFw-unsplash.jpg',
  '/images/tanner-marquis-i3v2sMuvirQ-unsplash.jpg',
  '/images/uran-wang-5wDq-27_zKI-unsplash.jpg',
];

// Get image for canvas dynamically based on ID
const getCanvasImage = (canvasId: string): string => {
  try {
    // Use canvas ID to deterministically assign image
    const hash = canvasId.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
    const imageIndex = hash % CANVAS_IMAGES.length;
    const imagePath = CANVAS_IMAGES[imageIndex];
    console.log('[CanvasManager] Getting image for canvas:', canvasId, '->', imagePath);
    return imagePath;
  } catch (error) {
    console.error('[CanvasManager] Error getting canvas image:', error);
    return CANVAS_IMAGES[0]; // Fallback to first image
  }
};

// Elegant serif font
const serifFont = { fontFamily: 'Georgia, "Times New Roman", serif' };
const sansFont = { fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif' };

const CanvasManagerInternal = ({ onClose }: CanvasManagerProps) => {
  const [canvases, setCanvases] = useState<CanvasItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeIndex, setActiveIndex] = useState(0);
  const [displayIndex, setDisplayIndex] = useState(0); // What's actually displayed (lags behind during transition)
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [direction, setDirection] = useState(0); // -1 up, 1 down
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null);
  const [showEditModal, setShowEditModal] = useState<string | null>(null);
  const [newCanvasName, setNewCanvasName] = useState('');
  const [newCanvasDescription, setNewCanvasDescription] = useState('');
  const [editCanvasName, setEditCanvasName] = useState('');
  const [editCanvasDescription, setEditCanvasDescription] = useState('');
  const [touchStart, setTouchStart] = useState<number | null>(null);
  const [nextImageAnimating, setNextImageAnimating] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  
  const { loadCanvas, setCurrentCanvas, currentCanvasId } = useCanvasStore();

  useEffect(() => {
    console.log('[CanvasManager] Component mounted, loading canvases...');
    loadCanvases();
    
    return () => {
      console.log('[CanvasManager] Component unmounting...');
    };
  }, []);

  // Set initial active index to current canvas
  useEffect(() => {
    if (canvases.length > 0) {
      if (currentCanvasId) {
        const index = canvases.findIndex(c => c.id === currentCanvasId);
        if (index !== -1) {
          console.log('[CanvasManager] Setting activeIndex to current canvas:', index);
          setActiveIndex(index);
          setDisplayIndex(index);
        } else {
          console.log('[CanvasManager] Current canvas not found, setting activeIndex to 0');
          setActiveIndex(0);
          setDisplayIndex(0);
        }
      } else {
        // No current canvas, set to first canvas
        console.log('[CanvasManager] No current canvas, setting activeIndex to 0');
        setActiveIndex(0);
        setDisplayIndex(0);
      }
    }
  }, [canvases, currentCanvasId]);

  const loadCanvases = async () => {
    try {
      setIsLoading(true);
      const data = await api.getCanvases();
      console.log('[CanvasManager] Loaded canvases:', data);
      setCanvases(data);
      // Ensure activeIndex is valid - always set to 0 if canvases exist and current index is invalid
      if (data.length > 0) {
        if (activeIndex >= data.length || activeIndex < 0) {
          console.log('[CanvasManager] Resetting activeIndex to 0');
          setActiveIndex(0);
          setDisplayIndex(0);
        } else {
          console.log('[CanvasManager] Keeping activeIndex at:', activeIndex);
          // Keep displayIndex in sync when not transitioning
          if (!isTransitioning) {
            setDisplayIndex(activeIndex);
          }
        }
      }
    } catch (error) {
      console.error('[CanvasManager] Failed to load canvases:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const goToCanvas = useCallback((newIndex: number, dir: number) => {
    if (isTransitioning || newIndex === activeIndex) return;
    if (newIndex < 0 || newIndex >= canvases.length) return;
    
    // Update activeIndex immediately (for logic)
    setActiveIndex(newIndex);
    // But keep displayIndex at old value during transition
    setDirection(dir);
    setIsTransitioning(true);
    setNextImageAnimating(false); // Reset animation state
    
    // Trigger next image animation after a tiny delay to ensure it renders first
    // Use requestAnimationFrame to ensure DOM is ready
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        setNextImageAnimating(true);
      });
    });
    
    // After transition completes, update displayIndex FIRST, then reset transition state
    // This ensures the next image div is removed before currentCanvas changes
    setTimeout(() => {
      // Update displayIndex first - this will cause nextCanvas to become null
      // (because isTransitioning is still true, but nextCanvas calculation will change)
      // Actually, we need to update displayIndex AFTER isTransitioning is false
      // to ensure the next image div is removed
      
      // First, stop the transition state
      setIsTransitioning(false);
      setDirection(0);
      setNextImageAnimating(false);
      
      // Wait for React to process the state update and remove the next image div
      // Then update displayIndex so currentCanvas changes
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          setDisplayIndex(newIndex);
        });
      });
    }, 700); // Match the transition duration exactly
  }, [activeIndex, isTransitioning, canvases.length]);

  const goNext = useCallback(() => {
    if (activeIndex < canvases.length - 1) {
      goToCanvas(activeIndex + 1, 1);
    }
  }, [activeIndex, canvases.length, goToCanvas]);

  const goPrev = useCallback(() => {
    if (activeIndex > 0) {
      goToCanvas(activeIndex - 1, -1);
    }
  }, [activeIndex, goToCanvas]);

  // Wheel handler for scroll navigation
  useEffect(() => {
    const container = containerRef.current;
    if (!container || showCreateModal || showDeleteConfirm || showEditModal) return;

    let wheelTimeout: ReturnType<typeof setTimeout>;
    const handleWheel = (e: WheelEvent) => {
      e.preventDefault();
      if (isTransitioning) return;
      
      clearTimeout(wheelTimeout);
      wheelTimeout = setTimeout(() => {
        if (e.deltaY > 30) goNext();
        else if (e.deltaY < -30) goPrev();
      }, 50);
    };

    container.addEventListener('wheel', handleWheel, { passive: false });
    return () => {
      container.removeEventListener('wheel', handleWheel);
      clearTimeout(wheelTimeout);
    };
  }, [goNext, goPrev, isTransitioning, showCreateModal, showDeleteConfirm, showEditModal]);

  // Touch handlers
  const handleTouchStart = (e: React.TouchEvent) => {
    setTouchStart(e.touches[0].clientY);
  };

  const handleTouchEnd = (e: React.TouchEvent) => {
    if (!touchStart || showCreateModal || showDeleteConfirm || showEditModal) return;
    const touchEnd = e.changedTouches[0].clientY;
    const diff = touchStart - touchEnd;
    
    if (Math.abs(diff) > 50) {
      if (diff > 0) goNext();
      else goPrev();
    }
    setTouchStart(null);
  };

  // Keyboard handler
  useEffect(() => {
    if (showCreateModal || showDeleteConfirm || showEditModal) return;
    
    const handleKeyDown = (e: KeyboardEvent) => {
      console.log('[CanvasManager] Key pressed:', e.key);
      if (e.key === 'ArrowDown' || e.key === 'ArrowRight') {
        e.preventDefault();
        goNext();
      }
      if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') {
        e.preventDefault();
        goPrev();
      }
      if (e.key === 'Escape') {
        console.log('[CanvasManager] Escape key pressed, closing...');
        e.preventDefault();
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [goNext, goPrev, onClose, showCreateModal, showDeleteConfirm, showEditModal]);

  const handleCreateCanvas = async () => {
    if (!newCanvasName.trim()) return;

    try {
      const data = await api.createCanvas({
        name: newCanvasName,
        description: newCanvasDescription
      });

      await loadCanvases();
      const newIndex = canvases.length; // New canvas will be at the end
      setActiveIndex(newIndex);
      setNewCanvasName('');
      setNewCanvasDescription('');
      setShowCreateModal(false);
      
      // Auto-select the new canvas
      await handleSelectCanvas(data.id, data.name);
    } catch (error) {
      console.error('Failed to create canvas:', error);
    }
  };

  const handleSelectCanvas = async (id: string, name: string) => {
    console.log('[CanvasManager] handleSelectCanvas called with:', id, name);
    console.trace('[CanvasManager] Stack trace for handleSelectCanvas');
    try {
      console.log('[CanvasManager] Setting current canvas...');
      setCurrentCanvas(id, name);
      console.log('[CanvasManager] Loading canvas data...');
      await loadCanvas(id);
      console.log('[CanvasManager] Canvas loaded, calling onClose...');
      onClose();
      console.log('[CanvasManager] onClose called');
    } catch (error) {
      console.error('[CanvasManager] Error selecting canvas:', error);
    }
  };

  const handleDeleteCanvas = async (id: string) => {
    try {
      await api.deleteCanvas(id);
      await loadCanvases();

      if (currentCanvasId === id) {
        // If deleting the active canvas, switch to first available
        const remainingCanvases = canvases.filter(c => c.id !== id);
        if (remainingCanvases.length > 0) {
          const nextCanvas = remainingCanvases[0];
          setCurrentCanvas(nextCanvas.id, nextCanvas.name);
          await loadCanvas(nextCanvas.id);
        }
      }
      
      setShowDeleteConfirm(null);
      if (canvases.length <= 1) {
        onClose();
      }
    } catch (error) {
      console.error('Failed to delete canvas:', error);
    }
  };

  const handleUpdateCanvas = async (id: string) => {
    if (!editCanvasName.trim()) return;

    try {
      await api.updateCanvas(id, {
        name: editCanvasName,
        description: editCanvasDescription
      });
      await loadCanvases();
      setShowEditModal(null);
      setEditCanvasName('');
      setEditCanvasDescription('');
    } catch (error) {
      console.error('Failed to update canvas:', error);
    }
  };

  const openEditModal = (canvas: CanvasItem) => {
    setEditCanvasName(canvas.name);
    setEditCanvasDescription(canvas.description);
    setShowEditModal(canvas.id);
  };

  // Ensure displayIndex is within bounds (this is what we actually show)
  // During transition, displayIndex stays at the old value until transition completes
  const safeDisplayIndex = canvases.length > 0 ? Math.min(displayIndex, canvases.length - 1) : 0;
  const currentCanvas = canvases.length > 0 && safeDisplayIndex >= 0 ? canvases[safeDisplayIndex] : null;
  
  // Calculate next canvas - use activeIndex to determine what's coming next
  // This ensures nextCanvas is available even after direction becomes 0
  let nextCanvas: CanvasItem | null = null;
  if (activeIndex !== safeDisplayIndex) {
    // We're transitioning to a different canvas
    if (activeIndex >= 0 && activeIndex < canvases.length) {
      nextCanvas = canvases[activeIndex];
    }
  } else if (direction !== 0) {
    // During transition, calculate based on direction
    const nextIndex = direction === 1 
      ? Math.min(safeDisplayIndex + 1, canvases.length - 1) 
      : Math.max(safeDisplayIndex - 1, 0);
    if (nextIndex >= 0 && nextIndex < canvases.length && nextIndex !== safeDisplayIndex) {
      nextCanvas = canvases[nextIndex];
    }
  }
  
  // Show next title/image if transitioning OR if activeIndex differs from displayIndex
  // (to prevent blink when displayIndex updates)
  const showNextContent = isTransitioning || (activeIndex !== safeDisplayIndex && nextCanvas !== null);

  // Timeline markers positions (8 markers on each side)
  const timelineMarkers = Array.from({ length: 8 }, (_, i) => ({
    id: i,
    position: (i / 7) * 100, // 0% to 100%
    isActive: i === 3 || i === 4, // Middle markers active
  }));

  // Debug logging
  useEffect(() => {
    console.log('[CanvasManager] Render state:', {
      canvasesLength: canvases.length,
      isLoading,
      activeIndex,
      displayIndex,
      currentCanvas: currentCanvas?.name,
      showCreateModal,
      showDeleteConfirm,
      showEditModal
    });
  }, [canvases.length, isLoading, activeIndex, displayIndex, currentCanvas, showCreateModal, showDeleteConfirm, showEditModal]);

  // Prevent accidental closes
  const handleClose = useCallback(() => {
    console.log('[CanvasManager] handleClose called');
    console.trace('[CanvasManager] Stack trace for handleClose');
    onClose();
  }, [onClose]);

  // Check if component is in DOM (must be before any early returns!)
  // Removed debug logging to prevent console spam
  useEffect(() => {
    // DOM check removed - was causing console spam
    // Component is working correctly, no need for continuous DOM monitoring
  }, []);

  // Log when component is about to render
  console.log('[CanvasManager] About to render:', {
    isLoading,
    canvasesCount: canvases.length,
    currentCanvasExists: !!currentCanvas
  });

  // Early return if still loading (AFTER all hooks!)
  if (isLoading) {
    return (
      <div 
        ref={containerRef}
        className="fixed inset-0 bg-black overflow-hidden relative select-none z-50"
        style={sansFont}
      >
        <div className="w-full h-full flex items-center justify-center relative">
          <div className="text-center">
            <div className="w-16 h-16 border-4 border-white/20 border-t-white rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-white/60 text-sm">Loading canvases...</p>
          </div>
        </div>
      </div>
    );
  }

  console.log('[CanvasManager] Rendering main component, showCanvasManager should be true');

  return (
    <div 
      ref={containerRef}
      className="fixed inset-0 bg-black overflow-hidden relative select-none"
      style={{
        ...sansFont,
        zIndex: 9999, // Ensure highest z-index
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
      }}
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
      onClick={(e) => {
        // Prevent clicks on the background from closing
        if (e.target === e.currentTarget) {
          console.log('[CanvasManager] Background clicked, but not closing');
        }
      }}
    >
      {/* Top Header Bar */}
      <div 
        className="absolute top-0 left-0 right-0 h-10 flex items-center justify-between px-8 z-50"
        style={{
          background: 'rgba(0, 0, 0, 0.8)',
          backdropFilter: 'blur(10px)',
          WebkitBackdropFilter: 'blur(10px)',
        }}
      >
        <span className="text-white/30 text-xs tracking-widest uppercase">VIA</span>
        <span className="text-white/50 text-xs tracking-wide">ALL IDEAS IN ONE PLACE</span>
        <span className="text-white/30 text-xs tracking-widest uppercase">CANVAS</span>
      </div>

      {/* Close Button */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          console.log('[CanvasManager] Close button clicked');
          handleClose();
        }}
        className="absolute top-14 right-6 z-50 w-10 h-10 rounded-full flex items-center justify-center border transition-all hover:bg-white/10"
        style={{
          background: 'rgba(255, 255, 255, 0.1)',
          backdropFilter: 'blur(12px)',
          WebkitBackdropFilter: 'blur(12px)',
          borderColor: 'rgba(255, 255, 255, 0.15)',
        }}
      >
        <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>

      {isLoading ? (
        // Loading State
        <div className="w-full h-full flex items-center justify-center relative">
          <div className="text-center">
            <div className="w-16 h-16 border-4 border-white/20 border-t-white rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-white/60 text-sm">Loading canvases...</p>
          </div>
        </div>
      ) : canvases.length === 0 ? (
        // Empty State with Elegant UI
        <div className="w-full h-full flex items-center justify-center relative">
          {/* Wave Animation Background Effects */}
          <div className="absolute inset-0 pointer-events-none z-0">
            <div 
              className="absolute left-0 top-0 bottom-0 w-32 opacity-20"
              style={{
                background: 'linear-gradient(90deg, rgba(255,255,255,0.1) 0%, transparent 100%)',
                animation: 'waveLeft 4s ease-in-out infinite',
              }}
            />
            <div 
              className="absolute right-0 top-0 bottom-0 w-32 opacity-20"
              style={{
                background: 'linear-gradient(270deg, rgba(255,255,255,0.1) 0%, transparent 100%)',
                animation: 'waveRight 4s ease-in-out infinite 0.5s',
              }}
            />
          </div>

          <div className="text-center z-10">
            <h1 
              className="text-white text-6xl font-normal tracking-tight mb-4"
              style={serifFont}
            >
              No Canvases Yet
            </h1>
            <p className="text-white/50 text-sm mb-8 tracking-wide">
              Create your first canvas to get started
            </p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-6 py-3 rounded-full text-white/80 hover:text-white transition-all"
              style={{
                background: 'rgba(255, 255, 255, 0.1)',
                backdropFilter: 'blur(12px)',
                WebkitBackdropFilter: 'blur(12px)',
                border: '1px solid rgba(255, 255, 255, 0.15)',
              }}
            >
              Create First Canvas
            </button>
          </div>
        </div>
      ) : !currentCanvas ? (
        // Loading state when canvases exist but currentCanvas is not set yet
        <div className="w-full h-full flex items-center justify-center relative">
          <div className="text-center">
            <div className="w-16 h-16 border-4 border-white/20 border-t-white rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-white/60 text-sm">Preparing canvas...</p>
          </div>
        </div>
      ) : (
        <>
          {/* Wave Animation Background Effects */}
          <div className="absolute inset-0 pointer-events-none z-0">
            <div 
              className="absolute left-0 top-0 bottom-0 w-32 opacity-20"
              style={{
                background: 'linear-gradient(90deg, rgba(255,255,255,0.1) 0%, transparent 100%)',
                animation: 'waveLeft 4s ease-in-out infinite',
              }}
            />
            <div 
              className="absolute right-0 top-0 bottom-0 w-32 opacity-20"
              style={{
                background: 'linear-gradient(270deg, rgba(255,255,255,0.1) 0%, transparent 100%)',
                animation: 'waveRight 4s ease-in-out infinite 0.5s',
              }}
            />
            <div 
              className="absolute left-0 top-1/2 -translate-y-1/2 w-64 h-64 rounded-full opacity-10"
              style={{
                background: 'radial-gradient(circle, rgba(255,255,255,0.2) 0%, transparent 70%)',
                animation: 'rippleLeft 3s ease-in-out infinite',
              }}
            />
            <div 
              className="absolute right-0 top-1/2 -translate-y-1/2 w-64 h-64 rounded-full opacity-10"
              style={{
                background: 'radial-gradient(circle, rgba(255,255,255,0.2) 0%, transparent 70%)',
                animation: 'rippleRight 3s ease-in-out infinite 0.5s',
              }}
            />
          </div>

          {/* Main Content Area */}
          <div className="absolute inset-8 lg:inset-12 flex items-center justify-center">
            {/* The Arch Container */}
            <div 
              className="relative w-full max-w-3xl h-full max-h-[85vh] overflow-hidden"
              style={{
                borderRadius: '300px 300px 12px 12px',
                boxShadow: '0 0 0 1px rgba(255,255,255,0.05), 0 25px 50px -12px rgba(0,0,0,0.9)',
              }}
            >
              {/* Background Images Layer */}
              <div className="absolute inset-0">
                {/* Current Image */}
                {currentCanvas ? (
                  <div 
                    className={`absolute inset-0 ${isTransitioning ? 'transition-transform duration-700 ease-out' : ''}`}
                    style={{
                      transform: isTransitioning 
                        ? `translateY(${direction * -100}%)` 
                        : 'translateY(0)',
                    }}
                  >
                    <img
                      src={getCanvasImage(currentCanvas.id)}
                      alt={currentCanvas.name}
                      className="w-full h-full object-cover"
                      style={{ filter: 'brightness(0.85)' }}
                      onError={(e) => {
                        console.error('[CanvasManager] Image failed to load:', e);
                        // Fallback to a placeholder or first image
                        (e.target as HTMLImageElement).src = CANVAS_IMAGES[0];
                      }}
                    />
                  </div>
                ) : (
                  <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
                    <p className="text-white/40 text-sm">No canvas selected</p>
                  </div>
                )}
                
                {/* Next Image (slides in) - shown during transition and briefly after */}
                {showNextContent && nextCanvas && (
                  <div 
                    className="absolute inset-0 transition-transform duration-700 ease-out"
                    style={{
                      transform: nextImageAnimating 
                        ? 'translateY(0)' 
                        : `translateY(${direction * 100}%)`,
                    }}
                  >
                    <img
                      src={getCanvasImage(nextCanvas!.id)}
                      alt={nextCanvas!.name}
                      className="w-full h-full object-cover"
                      style={{ filter: 'brightness(0.85)' }}
                    />
                  </div>
                )}
              </div>

              {/* Enhanced Frosted Glass Overlay */}
              <div 
                className="absolute inset-0"
                style={{
                  background: 'rgba(0, 0, 0, 0.25)',
                  backdropFilter: 'blur(10px) saturate(150%)',
                  WebkitBackdropFilter: 'blur(10px) saturate(150%)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                }}
              />

              {/* Gradient Overlays */}
              <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-black/30 pointer-events-none" />
              <div className="absolute inset-0 bg-gradient-to-b from-black/40 via-transparent to-transparent pointer-events-none" />

              {/* Content Overlay */}
              <div className="absolute inset-0 flex flex-col">
                {/* Header */}
                <div className="flex items-center justify-between p-6 relative z-10">
                  <div 
                    className="w-10 h-10 rounded-full flex items-center justify-center border"
                    style={{
                      background: 'rgba(255, 255, 255, 0.1)',
                      backdropFilter: 'blur(12px)',
                      WebkitBackdropFilter: 'blur(12px)',
                      borderColor: 'rgba(255, 255, 255, 0.15)',
                    }}
                  >
                    <svg className="w-5 h-5 text-white" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
                    </svg>
                  </div>
                  
                  <div className="flex items-center gap-3">
                    <span className="text-white/60 text-sm tracking-wide">Via Canvas</span>
                    <div className="w-9 h-9 rounded-full overflow-hidden ring-2 ring-white/20">
                      <div className="w-full h-full bg-gradient-to-br from-orange-400 to-pink-500" />
                    </div>
                  </div>
                </div>

                {/* Center Content - Title */}
                <div className="flex-1 flex flex-col items-center justify-center relative">
                  {/* Current Title */}
                  {currentCanvas ? (
                    <div 
                      className={`text-center ${isTransitioning ? 'transition-all duration-700 ease-out' : ''} ${
                        showNextContent ? 'opacity-0' : 'opacity-100'
                      }`}
                      style={{
                        transform: isTransitioning 
                          ? `translateY(${direction * -60}px)` 
                          : 'translateY(0)',
                      }}
                    >
                      <h1 
                        className="text-white text-6xl lg:text-7xl font-normal tracking-tight drop-shadow-2xl cursor-pointer hover:opacity-80 transition-opacity"
                        style={serifFont}
                        onClick={() => {
                          console.log('[CanvasManager] Title clicked, selecting canvas:', currentCanvas.id);
                          handleSelectCanvas(currentCanvas.id, currentCanvas.name);
                        }}
                      >
                        {currentCanvas.name}
                      </h1>
                      <p className="text-white/50 text-sm mt-3 tracking-widest uppercase">
                        {currentCanvas.description || 'Canvas'}
                      </p>
                    </div>
                  ) : (
                    <div className="text-center">
                      <p className="text-white/60 text-sm">Loading...</p>
                    </div>
                  )}

                  {/* Next Title (slides in) - shown during transition and briefly after */}
                  {showNextContent && nextCanvas && (
                    <div 
                      className="absolute text-center transition-all duration-700 ease-out"
                      style={{
                        transform: `translateY(${direction * 60}px)`,
                        opacity: 0,
                        animation: 'fadeSlideIn 700ms ease-out 100ms forwards',
                      }}
                    >
                      <h1 
                        className="text-white text-6xl lg:text-7xl font-normal tracking-tight"
                        style={serifFont}
                      >
                        {nextCanvas!.name}
                      </h1>
                      <p className="text-white/50 text-sm mt-3 tracking-widest uppercase">
                        {nextCanvas!.description || 'Canvas'}
                      </p>
                    </div>
                  )}
                </div>

                {/* Bottom Navigation */}
                <div className="p-6 flex items-center justify-center gap-8 relative z-10">
                  <button 
                    onClick={(e) => {
                      e.stopPropagation();
                      setShowCreateModal(true);
                    }}
                    className="text-sm tracking-wider transition-all duration-300 text-white/40 hover:text-white/70"
                  >
                    Create
                  </button>
                  <div className="flex gap-3">
                    {canvases.map((canvas, index) => (
                      <button
                        key={canvas.id}
                        onClick={(e) => {
                          e.stopPropagation();
                          goToCanvas(index, index > activeIndex ? 1 : -1);
                        }}
                        className={`transition-all duration-300 rounded-full ${
                          index === activeIndex 
                            ? 'w-8 h-2 bg-white shadow-lg' 
                            : 'w-2 h-2 bg-white/40 hover:bg-white/60'
                        }`}
                      />
                    ))}
                  </div>
                </div>
              </div>

              {/* Action Buttons (on hover) */}
              <div className="absolute top-20 right-6 z-20 opacity-0 hover:opacity-100 transition-opacity group">
                <div className="flex flex-col gap-2">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (currentCanvas) openEditModal(currentCanvas);
                    }}
                    className="w-10 h-10 rounded-full flex items-center justify-center border transition-all hover:bg-white/10"
                    style={{
                      background: 'rgba(255, 255, 255, 0.1)',
                      backdropFilter: 'blur(12px)',
                      WebkitBackdropFilter: 'blur(12px)',
                      borderColor: 'rgba(255, 255, 255, 0.15)',
                    }}
                  >
                    <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (currentCanvas) setShowDeleteConfirm(currentCanvas.id);
                    }}
                    className="w-10 h-10 rounded-full flex items-center justify-center border transition-all hover:bg-red-500/20"
                    style={{
                      background: 'rgba(255, 255, 255, 0.1)',
                      backdropFilter: 'blur(12px)',
                      WebkitBackdropFilter: 'blur(12px)',
                      borderColor: 'rgba(255, 255, 255, 0.15)',
                    }}
                  >
                    <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>

              {/* Side Navigation Arrows */}
              <button 
                onClick={(e) => {
                  e.stopPropagation();
                  goPrev();
                }}
                className={`absolute left-4 top-1/2 -translate-y-1/2 w-10 h-10 flex items-center justify-center text-white/30 hover:text-white/70 transition-all ${
                  activeIndex === 0 ? 'opacity-0 pointer-events-none' : 'opacity-100'
                }`}
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              
              <button 
                onClick={(e) => {
                  e.stopPropagation();
                  goNext();
                }}
                className={`absolute right-4 top-1/2 -translate-y-1/2 w-10 h-10 flex items-center justify-center text-white/30 hover:text-white/70 transition-all ${
                  activeIndex === canvases.length - 1 ? 'opacity-0 pointer-events-none' : 'opacity-100'
                }`}
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </div>

            {/* Side Timeline Markers - Left */}
            <div className="absolute left-6 top-1/2 -translate-y-1/2 flex flex-col items-center gap-2 z-20">
              <svg className="absolute inset-0 w-1 h-full" style={{ left: '50%', transform: 'translateX(-50%)' }}>
                <line
                  x1="50%"
                  y1="0%"
                  x2="50%"
                  y2="100%"
                  stroke="rgba(255,255,255,0.2)"
                  strokeWidth="1"
                />
              </svg>
              {timelineMarkers.map((marker) => (
                <div
                  key={marker.id}
                  className="relative"
                  style={{ top: `${marker.position}%`, transform: 'translateY(-50%)' }}
                >
                  <div
                    className={`w-2 h-2 rounded-full transition-all duration-300 ${
                      marker.isActive
                        ? 'bg-white ring-2 ring-white/50 ring-offset-2 ring-offset-transparent scale-125'
                        : 'bg-white/30 hover:bg-white/50'
                    }`}
                  />
                </div>
              ))}
            </div>

            {/* Side Timeline Markers - Right */}
            <div className="absolute right-6 top-1/2 -translate-y-1/2 flex flex-col items-center gap-2 z-20">
              <svg className="absolute inset-0 w-1 h-full" style={{ left: '50%', transform: 'translateX(-50%)' }}>
                <line
                  x1="50%"
                  y1="0%"
                  x2="50%"
                  y2="100%"
                  stroke="rgba(255,255,255,0.2)"
                  strokeWidth="1"
                />
              </svg>
              {timelineMarkers.map((marker) => (
                <div
                  key={marker.id}
                  className="relative"
                  style={{ top: `${marker.position}%`, transform: 'translateY(-50%)' }}
                >
                  <div
                    className={`w-2 h-2 rounded-full transition-all duration-300 ${
                      marker.isActive
                        ? 'bg-white ring-2 ring-white/50 ring-offset-2 ring-offset-transparent scale-125'
                        : 'bg-white/30 hover:bg-white/50'
                    }`}
                  />
                </div>
              ))}
            </div>
          </div>
        </>
      )}

      {/* Footer */}
      <div 
        className="absolute bottom-0 left-0 right-0 h-14 flex items-center justify-between px-8 z-40 border-t"
        style={{
          background: 'rgba(0, 0, 0, 0.6)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          borderTopColor: 'rgba(255, 255, 255, 0.1)',
        }}
      >
        <div className="flex items-center gap-4">
          <div className="flex items-baseline gap-2">
            <span className="text-white text-xl font-light" style={serifFont}>
              {new Date().getFullYear()}
            </span>
            <div className="w-px h-4 bg-white/20 mx-1" />
            <span className="text-white/40 text-xs leading-tight">
              {new Date().toLocaleDateString('en-US', { day: 'numeric', month: 'short' })}
            </span>
          </div>
          <div className="w-px h-6 bg-white/10 mx-4" />
          <span className="text-white/60 text-sm tracking-wide">
            {canvases.length} {canvases.length === 1 ? 'Canvas' : 'Canvases'}
          </span>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="flex gap-1.5">
            {[1, 2, 1, 2, 1].map((h, i) => (
              <div 
                key={i} 
                className="w-0.5 bg-white/40 rounded-full"
                style={{ height: `${h * 6}px` }}
              />
            ))}
          </div>
          <span className="text-white/60 text-sm tracking-wide ml-2">Via Canvas</span>
        </div>
      </div>

      {/* Create Canvas Modal */}
      {showCreateModal && (
        <ElegantModal
          title="Create New Canvas"
          onClose={() => {
            setShowCreateModal(false);
            setNewCanvasName('');
            setNewCanvasDescription('');
          }}
        >
          <div className="space-y-4">
            <div>
              <label className="block text-xs text-white/60 mb-2 tracking-wide uppercase">Canvas Name</label>
              <input
                type="text"
                value={newCanvasName}
                onChange={(e) => setNewCanvasName(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleCreateCanvas()}
                placeholder="Enter canvas name..."
                className="w-full bg-white/10 backdrop-blur-md border border-white/20 text-white rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-white/30"
                autoFocus
              />
            </div>
            <div>
              <label className="block text-xs text-white/60 mb-2 tracking-wide uppercase">Description (Optional)</label>
              <textarea
                value={newCanvasDescription}
                onChange={(e) => setNewCanvasDescription(e.target.value)}
                placeholder="Add a description..."
                rows={3}
                className="w-full bg-white/10 backdrop-blur-md border border-white/20 text-white rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-white/30 resize-none"
              />
            </div>
            <div className="flex gap-3 pt-2">
              <button
                onClick={handleCreateCanvas}
                disabled={!newCanvasName.trim()}
                className="flex-1 px-6 py-3 rounded-full text-white font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                style={{
                  background: 'rgba(255, 255, 255, 0.2)',
                  backdropFilter: 'blur(12px)',
                  WebkitBackdropFilter: 'blur(12px)',
                  border: '1px solid rgba(255, 255, 255, 0.3)',
                }}
              >
                Create
              </button>
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  setNewCanvasName('');
                  setNewCanvasDescription('');
                }}
                className="px-6 py-3 rounded-full text-white/60 hover:text-white transition-all"
                style={{
                  background: 'rgba(255, 255, 255, 0.05)',
                  backdropFilter: 'blur(12px)',
                  WebkitBackdropFilter: 'blur(12px)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                }}
              >
                Cancel
              </button>
            </div>
          </div>
        </ElegantModal>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <ElegantModal
          title="Delete Canvas"
          onClose={() => setShowDeleteConfirm(null)}
        >
          <div className="space-y-4">
            <p className="text-white/70 text-sm">
              Are you sure you want to delete this canvas? This action cannot be undone.
            </p>
            <div className="flex gap-3 pt-2">
              <button
                onClick={() => handleDeleteCanvas(showDeleteConfirm)}
                className="flex-1 px-6 py-3 rounded-full text-white font-medium transition-all"
                style={{
                  background: 'rgba(239, 68, 68, 0.3)',
                  backdropFilter: 'blur(12px)',
                  WebkitBackdropFilter: 'blur(12px)',
                  border: '1px solid rgba(239, 68, 68, 0.5)',
                }}
              >
                Delete
              </button>
              <button
                onClick={() => setShowDeleteConfirm(null)}
                className="px-6 py-3 rounded-full text-white/60 hover:text-white transition-all"
                style={{
                  background: 'rgba(255, 255, 255, 0.05)',
                  backdropFilter: 'blur(12px)',
                  WebkitBackdropFilter: 'blur(12px)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                }}
              >
                Cancel
              </button>
            </div>
          </div>
        </ElegantModal>
      )}

      {/* Edit Canvas Modal */}
      {showEditModal && (
        <ElegantModal
          title="Edit Canvas"
          onClose={() => {
            setShowEditModal(null);
            setEditCanvasName('');
            setEditCanvasDescription('');
          }}
        >
          <div className="space-y-4">
            <div>
              <label className="block text-xs text-white/60 mb-2 tracking-wide uppercase">Canvas Name</label>
              <input
                type="text"
                value={editCanvasName}
                onChange={(e) => setEditCanvasName(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && showEditModal && handleUpdateCanvas(showEditModal)}
                placeholder="Enter canvas name..."
                className="w-full bg-white/10 backdrop-blur-md border border-white/20 text-white rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-white/30"
                autoFocus
              />
            </div>
            <div>
              <label className="block text-xs text-white/60 mb-2 tracking-wide uppercase">Description</label>
              <textarea
                value={editCanvasDescription}
                onChange={(e) => setEditCanvasDescription(e.target.value)}
                placeholder="Add a description..."
                rows={3}
                className="w-full bg-white/10 backdrop-blur-md border border-white/20 text-white rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-white/30 resize-none"
              />
            </div>
            <div className="flex gap-3 pt-2">
              <button
                onClick={() => showEditModal && handleUpdateCanvas(showEditModal)}
                disabled={!editCanvasName.trim()}
                className="flex-1 px-6 py-3 rounded-full text-white font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                style={{
                  background: 'rgba(255, 255, 255, 0.2)',
                  backdropFilter: 'blur(12px)',
                  WebkitBackdropFilter: 'blur(12px)',
                  border: '1px solid rgba(255, 255, 255, 0.3)',
                }}
              >
                Save
              </button>
              <button
                onClick={() => {
                  setShowEditModal(null);
                  setEditCanvasName('');
                  setEditCanvasDescription('');
                }}
                className="px-6 py-3 rounded-full text-white/60 hover:text-white transition-all"
                style={{
                  background: 'rgba(255, 255, 255, 0.05)',
                  backdropFilter: 'blur(12px)',
                  WebkitBackdropFilter: 'blur(12px)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                }}
              >
                Cancel
              </button>
            </div>
          </div>
        </ElegantModal>
      )}

      {/* CSS Animations */}
      <style>{`
        @keyframes waveLeft {
          0%, 100% {
            transform: translateX(0) scaleY(1);
            opacity: 0.1;
          }
          50% {
            transform: translateX(20px) scaleY(1.1);
            opacity: 0.2;
          }
        }
        
        @keyframes waveRight {
          0%, 100% {
            transform: translateX(0) scaleY(1);
            opacity: 0.1;
          }
          50% {
            transform: translateX(-20px) scaleY(1.1);
            opacity: 0.2;
          }
        }
        
        @keyframes rippleLeft {
          0%, 100% {
            transform: translate(-50%, -50%) scale(0.8);
            opacity: 0.1;
          }
          50% {
            transform: translate(-50%, -50%) scale(1.2);
            opacity: 0.15;
          }
        }
        
        @keyframes rippleRight {
          0%, 100% {
            transform: translate(50%, -50%) scale(0.8);
            opacity: 0.1;
          }
          50% {
            transform: translate(50%, -50%) scale(1.2);
            opacity: 0.15;
          }
        }

        @keyframes slideIn {
          from { transform: translateY(${direction * 100}%); }
          to { transform: translateY(0); }
        }
        
        @keyframes fadeSlideIn {
          from { 
            opacity: 0; 
            transform: translateY(${direction * 60}px); 
          }
          to { 
            opacity: 1; 
            transform: translateY(0); 
          }
        }
      `}</style>
    </div>
  );
};

// Elegant Modal Component
interface ElegantModalProps {
  title: string;
  children: React.ReactNode;
  onClose: () => void;
}

const ElegantModal = ({ title, children, onClose }: ElegantModalProps) => {
  return (
    <div className="fixed inset-0 flex items-center justify-center z-50">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/60"
        onClick={onClose}
        style={{
          backdropFilter: 'blur(4px)',
          WebkitBackdropFilter: 'blur(4px)',
        }}
      />
      
      {/* Modal */}
      <div 
        className="relative w-full max-w-md mx-4 rounded-2xl p-6"
        style={{
          background: 'rgba(0, 0, 0, 0.7)',
          backdropFilter: 'blur(20px) saturate(180%)',
          WebkitBackdropFilter: 'blur(20px) saturate(180%)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.5)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-6">
          <h2 
            className="text-2xl font-normal text-white"
            style={serifFont}
          >
            {title}
          </h2>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full flex items-center justify-center hover:bg-white/10 transition-colors"
          >
            <svg className="w-5 h-5 text-white/60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        {children}
      </div>
    </div>
  );
};

// Export with error boundary
export const CanvasManager = ({ onClose }: CanvasManagerProps) => {
  return (
    <CanvasManagerErrorBoundary onClose={onClose}>
      <CanvasManagerInternal onClose={onClose} />
    </CanvasManagerErrorBoundary>
  );
};
