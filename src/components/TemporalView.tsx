import React, { useEffect, useState, useMemo, useRef, useCallback } from 'react';
import { Calendar, Clock, FileText, CheckSquare, Video, Link as LinkIcon } from 'lucide-react';
import { api } from '../lib/api';
import { useCanvasStore } from '../store/canvasStore';
import ReactMarkdown from 'react-markdown';

interface TimelineNode {
  id: string;
  content: string;
  title: string;
  card_type: string;
  card_data: any;
  tags: string[];
  position_x: number;
  position_y: number;
  width: number;
  height: number;
  type: string;
  style: any;
  created_at: string;
}

const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
];

const serifFont = { fontFamily: 'Georgia, "Times New Roman", Times, serif' };
const sansFont = { fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif' };

const getCardIcon = (cardType: string) => {
  const iconMap: Record<string, any> = {
    'rich_text': FileText,
    'todo': CheckSquare,
    'video': Video,
    'link': LinkIcon,
    'reminder': Clock
  };
  return iconMap[cardType] || FileText;
};

const formatDateFull = (date: Date): string => {
  const day = date.getDate();
  const suffix = day === 1 || day === 21 || day === 31 ? 'st' :
                 day === 2 || day === 22 ? 'nd' :
                 day === 3 || day === 23 ? 'rd' : 'th';
  const month = MONTH_NAMES[date.getMonth()];
  const year = date.getFullYear();
  return `${day}${suffix} ${month} ${year}`;
};

export const TemporalView = () => {
  const { currentCanvasId } = useCanvasStore();
  const [allNodes, setAllNodes] = useState<TimelineNode[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedYear, setSelectedYear] = useState<number>(new Date().getFullYear());
  const [selectedMonth, setSelectedMonth] = useState<number | null>(null);
  const [activeIndex, setActiveIndex] = useState(0);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (currentCanvasId) {
      loadTimelineNodes();
    }
  }, [currentCanvasId]);

  const loadTimelineNodes = async () => {
    if (!currentCanvasId) return;

    setIsLoading(true);
    try {
      const data = await api.getNodes(currentCanvasId);
      // Sort by created_at descending (newest first)
      const sorted = [...data].sort((a, b) => 
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );
      setAllNodes(sorted);
      
      // Set default selected month to most recent month with cards
      if (sorted.length > 0) {
        const mostRecent = new Date(sorted[0].created_at);
        setSelectedYear(mostRecent.getFullYear());
        setSelectedMonth(mostRecent.getMonth());
      }
    } catch (error) {
      console.error('Failed to load timeline nodes:', error);
    }
    setIsLoading(false);
  };

  // Group nodes by year and month
  const monthGroups = useMemo(() => {
    const groups = new Map<string, TimelineNode[]>();

    allNodes.forEach(node => {
      const date = new Date(node.created_at);
      const year = date.getFullYear();
      const month = date.getMonth();
      const key = `${year}-${month}`;

      if (!groups.has(key)) {
        groups.set(key, []);
      }
      groups.get(key)!.push(node);
    });

    return Array.from(groups.entries())
      .map(([key, nodes]) => {
        const [year, month] = key.split('-').map(Number);
        return {
          year,
          month,
          monthName: MONTH_NAMES[month],
          nodes: nodes.sort((a, b) => 
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
          )
        };
      })
      .sort((a, b) => {
        if (a.year !== b.year) return b.year - a.year;
        return b.month - a.month;
      });
  }, [allNodes]);

  // Get available years
  const availableYears = useMemo(() => {
    const years = new Set(monthGroups.map(g => g.year));
    return Array.from(years).sort((a, b) => b - a);
  }, [monthGroups]);

  // Get months for selected year
  const monthsForYear = useMemo(() => {
    return monthGroups.filter(g => g.year === selectedYear);
  }, [monthGroups, selectedYear]);

  // Get nodes for selected month
  const selectedNodes = useMemo(() => {
    if (selectedMonth === null) return [];
    const group = monthGroups.find(
      g => g.year === selectedYear && g.month === selectedMonth
    );
    return group?.nodes || [];
  }, [monthGroups, selectedYear, selectedMonth]);

  // Reset active index when month changes
  useEffect(() => {
    if (selectedNodes.length > 0) {
      setActiveIndex(0);
    }
  }, [selectedMonth, selectedYear]);

  // Navigation functions
  const goToCard = useCallback((newIndex: number) => {
    if (isTransitioning || newIndex === activeIndex) return;
    if (newIndex < 0 || newIndex >= selectedNodes.length) return;
    
    setIsTransitioning(true);
    setActiveIndex(newIndex);
    
    setTimeout(() => {
      setIsTransitioning(false);
    }, 400);
  }, [activeIndex, isTransitioning, selectedNodes.length]);

  const goNext = useCallback(() => {
    if (activeIndex < selectedNodes.length - 1) {
      goToCard(activeIndex + 1);
    }
  }, [activeIndex, selectedNodes.length, goToCard]);

  const goPrev = useCallback(() => {
    if (activeIndex > 0) {
      goToCard(activeIndex - 1);
    }
  }, [activeIndex, goToCard]);

  // Wheel handler
  useEffect(() => {
    const container = containerRef.current;
    if (!container || selectedNodes.length === 0) return;

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
  }, [goNext, goPrev, isTransitioning, selectedNodes.length]);

  // Keyboard handler
  useEffect(() => {
    if (selectedNodes.length === 0) return;
    
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowDown' || e.key === 'ArrowRight') goNext();
      if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') goPrev();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [goNext, goPrev, selectedNodes.length]);

  // 3D transform function for cards
  const getCardTransform = (index: number): React.CSSProperties => {
    const diff = index - activeIndex;
    
    if (diff < 0) {
      // Cards that have passed (in front/below)
      return {
        transform: `
          translateZ(${diff * 80}px) 
          translateY(${diff * 40}px)
          translateX(${diff * 20}px)
          scale(${1 + diff * 0.08})
        `,
        opacity: 0,
        zIndex: 10 + diff,
        filter: 'blur(0px)',
        pointerEvents: 'none',
      } as React.CSSProperties;
    } else if (diff === 0) {
      // Active card
      return {
        transform: 'translateZ(0) translateY(0) translateX(0) scale(1)',
        opacity: 1,
        zIndex: 10,
        filter: 'blur(0px)',
        pointerEvents: 'auto',
      } as React.CSSProperties;
    } else {
      // Cards in the back
      return {
        transform: `
          translateZ(${-diff * 60}px) 
          translateY(${-diff * 35}px)
          translateX(${diff * 15}px)
          scale(${1 - diff * 0.06})
        `,
        opacity: Math.max(0, 1 - diff * 0.25),
        zIndex: 10 - diff,
        filter: `blur(${diff * 1.5}px)`,
        pointerEvents: (diff <= 2 ? 'auto' : 'none') as React.CSSProperties['pointerEvents'],
      } as React.CSSProperties;
    }
  };

  // Get current date info for footer
  const currentDate = new Date();
  const currentDay = currentDate.getDate();
  const currentDaySuffix = currentDay === 1 || currentDay === 21 || currentDay === 31 ? 'st' :
                           currentDay === 2 || currentDay === 22 ? 'nd' :
                           currentDay === 3 || currentDay === 23 ? 'rd' : 'th';
  const currentMonth = MONTH_NAMES[currentDate.getMonth()].substring(0, 3);
  const currentYear = currentDate.getFullYear();

  if (!currentCanvasId) {
    return (
      <div className="flex-1 flex items-center justify-center bg-white">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-400 mb-2">No Canvas Selected</h2>
          <p className="text-gray-500">Select a canvas to view its timeline</p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center bg-white">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-400 mx-auto mb-4" />
          <p className="text-gray-400">Loading timeline...</p>
        </div>
      </div>
    );
  }

  if (allNodes.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center bg-white">
        <div className="text-center">
          <Calendar className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-400 mb-2">No Cards Yet</h2>
          <p className="text-gray-500">Create some cards to see them in the timeline</p>
        </div>
      </div>
    );
  }

  return (
    <div 
      ref={containerRef}
      className="flex-1 flex flex-col overflow-hidden relative select-none"
      style={{ 
        ...sansFont,
        background: 'linear-gradient(180deg, #f5f5f0 0%, #e8e8e3 100%)',
      }}
    >
      {/* Header */}
      <header className="absolute top-0 left-0 right-0 z-50 px-6 py-4 flex items-center justify-between">
        {/* Left - App Name and Icons */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-white rounded-full px-4 py-2 shadow-sm border border-gray-100">
            <span className="text-sm font-medium text-gray-800">Via Canvas</span>
            <div className="flex gap-1 ml-2 pl-2 border-l border-gray-200">
              <FileText className="w-4 h-4 text-gray-500" />
              <CheckSquare className="w-4 h-4 text-gray-500" />
            </div>
            <span className="text-xs text-gray-500 ml-2">{allNodes.length}</span>
            <button className="w-6 h-6 rounded-full bg-gray-900 text-white flex items-center justify-center ml-1 text-xs font-bold">
              +
            </button>
          </div>
        </div>

        {/* Center - Year Navigation */}
        <div className="flex gap-1 bg-white rounded-full p-1 shadow-sm border border-gray-100">
          {availableYears.map((year) => (
            <button
              key={year}
              onClick={() => {
                setSelectedYear(year);
                const firstMonth = monthsForYear.find(m => m.year === year);
                if (firstMonth) {
                  setSelectedMonth(firstMonth.month);
                } else {
                  setSelectedMonth(null);
                }
              }}
              className={`px-5 py-1.5 rounded-full text-sm font-medium transition-all duration-300 ${
                selectedYear === year
                  ? 'bg-gray-900 text-white shadow-sm'
                  : 'text-gray-500 hover:text-gray-800 hover:bg-gray-50'
              }`}
            >
              {year}
            </button>
          ))}
        </div>

        {/* Right - User Avatar */}
        <div className="w-10 h-10 rounded-full overflow-hidden ring-2 ring-white shadow-lg bg-gray-300" />
      </header>

      {/* Timeline Axis */}
      {selectedMonth !== null && monthsForYear.length > 0 && (
        <>
          <div 
            className="absolute left-1/2 top-24 bottom-20 w-px bg-gray-300" 
            style={{ transform: 'translateX(120px)' }} 
          />
          
          {/* Month Labels on Timeline */}
          {monthsForYear.map((group, i) => (
            <div 
              key={`${group.year}-${group.month}`}
              className="absolute z-40"
              style={{ 
                left: '50%', 
                top: `${140 + i * 80}px`,
                transform: 'translateX(100px)',
              }}
            >
              <div className={`px-3 py-1 rounded-full text-xs font-medium shadow-sm ${
                selectedMonth === group.month
                  ? 'bg-gray-700 text-white'
                  : 'bg-gray-400 text-white'
              }`}>
                {group.monthName}
              </div>
            </div>
          ))}
        </>
      )}

      {/* Cards Container with 3D Perspective */}
      <div 
        className="absolute inset-0 flex items-center justify-center"
        style={{ 
          perspective: '1200px',
          perspectiveOrigin: '50% 50%',
          paddingTop: '80px',
          paddingBottom: '80px',
        }}
      >
        {selectedMonth === null ? (
          <div className="text-center text-gray-400">
            <p className="text-lg">Select a month to view cards</p>
          </div>
        ) : selectedNodes.length === 0 ? (
          <div className="text-center text-gray-400">
            <p className="text-lg">No cards for this month</p>
          </div>
        ) : (
          <div 
            className="relative"
            style={{ 
              transformStyle: 'preserve-3d',
              width: '520px',
              marginRight: '200px',
            }}
          >
            {selectedNodes.map((node, index) => {
              const styles = getCardTransform(index);
              const isActive = index === activeIndex;
              const date = new Date(node.created_at);
              const Icon = getCardIcon(node.card_type || 'rich_text');
              
              return (
                <div
                  key={node.id}
                  className={`absolute top-0 left-0 w-full transition-all duration-500 ease-out cursor-pointer`}
                  style={{
                    ...styles,
                    transformStyle: 'preserve-3d',
                  }}
                  onClick={() => goToCard(index)}
                >
                  {/* Connector Line to Timeline */}
                  {selectedMonth !== null && (
                    <svg 
                      className="absolute -right-28 top-8 w-28 h-16 pointer-events-none"
                      style={{ 
                        opacity: styles.opacity,
                        filter: styles.filter,
                      }}
                    >
                      <path
                        d={`M 0 8 Q 50 8, 90 ${index % 2 === 0 ? 30 : 45}`}
                        fill="none"
                        stroke="#c4c4c0"
                        strokeWidth="1"
                      />
                      <circle cx="90" cy={index % 2 === 0 ? 30 : 45} r="3" fill="#c4c4c0" />
                    </svg>
                  )}

                  {/* Card */}
                  <div 
                    className={`bg-white rounded-xl overflow-hidden transition-shadow duration-300 ${
                      isActive 
                        ? 'shadow-2xl ring-1 ring-gray-200' 
                        : 'shadow-lg'
                    }`}
                  >
                    {/* Card Header */}
                    <div className="px-5 py-4 border-b border-gray-100">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                          {node.title && (
                            <h3 
                              className="text-base font-semibold text-gray-900 leading-tight"
                              style={serifFont}
                            >
                              {node.title}
                            </h3>
                          )}
                          {node.card_data?.subtitle && (
                            <p className="text-xs text-gray-400 mt-1 flex items-center gap-1">
                              <span className="text-amber-500">✦</span>
                              {node.card_data.subtitle}
                            </p>
                          )}
                        </div>
                        <span className="text-xs text-gray-400 whitespace-nowrap">
                          {formatDateFull(date)}
                        </span>
                      </div>
                    </div>

                    {/* Card Body */}
                    <div className="px-5 py-4 max-h-64 overflow-y-auto">
                      <div className="prose prose-sm max-w-none text-gray-600 leading-relaxed">
                        {node.content ? (
                          <ReactMarkdown>{node.content}</ReactMarkdown>
                        ) : (
                          <span className="text-gray-400 italic">Empty card</span>
                        )}
                      </div>
                    </div>

                    {/* Card Footer */}
                    <div className="px-5 py-3 bg-gray-50 flex items-center justify-between border-t border-gray-100">
                      <div className="flex gap-2">
                        {node.tags && node.tags.slice(0, 3).map((tag: string) => (
                          <span 
                            key={tag} 
                            className="px-2.5 py-1 bg-white text-gray-500 text-xs rounded-md border border-gray-200"
                          >
                            {tag}
                          </span>
                        ))}
                        {node.tags && node.tags.length > 3 && (
                          <span className="px-2.5 py-1 bg-gray-200 text-gray-500 text-xs rounded-md">
                            +{node.tags.length - 3}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <Icon className="w-4 h-4 text-gray-400" />
                        <button className="text-gray-400 hover:text-gray-600 transition-colors p-1">
                          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                            <circle cx="12" cy="6" r="1.5" />
                            <circle cx="12" cy="12" r="1.5" />
                            <circle cx="12" cy="18" r="1.5" />
                          </svg>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Right Scroll Indicator */}
      {selectedNodes.length > 0 && (
        <div className="absolute right-6 top-1/2 -translate-y-1/2 flex flex-col items-center">
          {/* Ruler marks */}
          <div className="flex flex-col gap-0.5">
            {Array.from({ length: Math.min(20, selectedNodes.length * 4) }).map((_, i) => (
              <div 
                key={i} 
                className={`rounded-full transition-all duration-300 ${
                  i >= activeIndex * 4 && i < (activeIndex + 1) * 4
                    ? 'w-1 h-1 bg-gray-600' 
                    : 'w-0.5 h-3 bg-gray-300'
                }`}
                style={{
                  width: i % 4 === 0 ? '3px' : '2px',
                  height: i >= activeIndex * 4 && i < (activeIndex + 1) * 4 ? '8px' : '12px',
                }}
              />
            ))}
          </div>
          
          {/* Current position label */}
          <div className="mt-4 text-xs text-gray-400" style={{ writingMode: 'vertical-rl' }}>
            {activeIndex + 1} / {selectedNodes.length}
          </div>
        </div>
      )}

      {/* Navigation Controls */}
      {selectedNodes.length > 0 && (
        <div className="absolute bottom-24 left-1/2 -translate-x-1/2 flex items-center gap-3">
          <button 
            onClick={goPrev}
            disabled={activeIndex === 0}
            className={`w-8 h-8 rounded-full bg-white shadow-md flex items-center justify-center transition-all ${
              activeIndex === 0 ? 'opacity-30' : 'hover:shadow-lg hover:scale-105'
            }`}
          >
            <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
            </svg>
          </button>
          <div className="flex gap-1.5">
            {selectedNodes.map((_, i) => (
              <button
                key={i}
                onClick={() => goToCard(i)}
                className={`transition-all duration-300 rounded-full ${
                  i === activeIndex 
                    ? 'w-6 h-1.5 bg-gray-800' 
                    : 'w-1.5 h-1.5 bg-gray-400 hover:bg-gray-500'
                }`}
              />
            ))}
          </div>
          <button 
            onClick={goNext}
            disabled={activeIndex === selectedNodes.length - 1}
            className={`w-8 h-8 rounded-full bg-white shadow-md flex items-center justify-center transition-all ${
              activeIndex === selectedNodes.length - 1 ? 'opacity-30' : 'hover:shadow-lg hover:scale-105'
            }`}
          >
            <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        </div>
      )}

      {/* Footer */}
      <footer className="absolute bottom-0 left-0 right-0 h-14 bg-gray-950 flex items-center justify-between px-6 border-t border-gray-800">
        <div className="flex items-center gap-4">
          <div className="flex items-baseline gap-1">
            <span className="text-white text-xl font-light" style={serifFont}>{currentYear}</span>
            <span className="text-gray-500 text-xs ml-1">{currentDay}{currentDaySuffix}<br/>{currentMonth}</span>
          </div>
          <div className="w-px h-5 bg-gray-700 mx-2" />
          <span className="text-gray-400 text-sm">Segments</span>
        </div>
        
        <div className="flex items-center gap-3">
          <div className="flex gap-1">
            {[1, 2, 1, 2, 1].map((h, i) => (
              <div 
                key={i} 
                className="w-0.5 bg-gray-600 rounded-full"
                style={{ height: `${h * 5}px` }}
              />
            ))}
          </div>
          <span className="text-gray-400 text-sm ml-2">Via Canvas</span>
        </div>
      </footer>
    </div>
  );
};
