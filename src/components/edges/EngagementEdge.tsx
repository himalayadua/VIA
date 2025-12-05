/**
 * EngagementEdge Component
 * 
 * Custom ReactFlow edge that visualizes learning engagement through line width.
 * Width increases with read_count, mimicking neural pathway strengthening.
 */

import { BaseEdge, getBezierPath, EdgeProps } from 'reactflow';

export const EngagementEdge = ({ 
  id, 
  sourceX, 
  sourceY, 
  targetX, 
  targetY, 
  sourcePosition, 
  targetPosition, 
  data,
  selected = false,
  style = {}
}: EdgeProps) => {
  const [edgePath] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });
  
  // Get target node's read count from edge data
  const readCount = data?.targetReadCount || 0;
  const strokeWidth = getEdgeWidth(readCount);
  
  // Color based on engagement - light colors for dark background
  // Light gray/white for unread, bright blue/cyan for read
  // When selected, use a brighter highlight color
  let strokeColor: string;
  if (selected) {
    // Bright yellow/white highlight for selected edges
    strokeColor = 'rgba(250, 204, 21, 0.9)'; // Bright yellow for selection
  } else if (readCount === 0) {
    strokeColor = 'rgba(203, 213, 225, 0.6)';  // Light slate gray for unread (visible on dark)
  } else {
    strokeColor = `rgba(${96 + readCount * 2}, ${165 + readCount}, ${250}, ${Math.min(0.5 + (readCount / 20), 1)})`; // Bright blue, more opaque with more reads
  }
  
  // Increase width and add glow when selected
  const finalStrokeWidth = selected ? strokeWidth + 1.5 : strokeWidth;
  const filter = selected 
    ? 'drop-shadow(0 0 4px rgba(250, 204, 21, 0.8))' // Strong glow for selected
    : (readCount > 0 ? `drop-shadow(0 0 ${readCount * 0.5}px ${strokeColor})` : 'none');
  
  return (
    <BaseEdge 
      id={id} 
      path={edgePath} 
      style={{ 
        ...style,
        strokeWidth: finalStrokeWidth, 
        stroke: strokeColor,
        transition: 'stroke-width 0.3s ease, stroke 0.3s ease, filter 0.3s ease',
        filter: filter,
      }} 
    />
  );
};

/**
 * Calculate edge width based on read count
 * Progressive scale mimicking neural strengthening
 * Minimum width increased for better visibility on dark backgrounds
 */
function getEdgeWidth(readCount: number): number {
  if (readCount === 0) return 2.5;       // Unread (visible on dark background)
  if (readCount < 5) return 3;           // Read 1-4 times
  if (readCount < 10) return 3.5;       // Read 5-9 times
  if (readCount < 15) return 4;         // Read 10-14 times
  if (readCount < 20) return 4.5;       // Read 15-19 times
  return 5;                              // Read 20+ times (max)
}
