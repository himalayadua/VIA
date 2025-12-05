/**
 * ChartRenderer Component
 * 
 * Renders charts from JSON data. Currently a placeholder that displays
 * the chart data. Can be enhanced with a charting library like Chart.js
 * or Recharts in the future.
 */

import { useState } from 'react';
import { BarChart3, Maximize2, Minimize2 } from 'lucide-react';

interface ChartRendererProps {
  chartId?: string;
  data: any;
  sessionId?: string;
}

export const ChartRenderer = ({ chartId, data }: ChartRendererProps) => {
  const [isExpanded, setIsExpanded] = useState(false);

  // Extract chart metadata
  const chartType = data?.type || 'unknown';
  const chartTitle = data?.title || 'Chart';
  const hasData = data?.data || data?.values;

  return (
    <div className="my-3 border border-slate-700 rounded-lg overflow-hidden bg-slate-800/50">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-slate-800 border-b border-slate-700">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-blue-400" />
          <span className="text-sm font-medium text-slate-200">{chartTitle}</span>
          {chartType !== 'unknown' && (
            <span className="text-xs text-slate-500">({chartType})</span>
          )}
        </div>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="p-1 hover:bg-slate-700 rounded transition-colors"
          title={isExpanded ? 'Collapse' : 'Expand'}
        >
          {isExpanded ? (
            <Minimize2 className="w-4 h-4 text-slate-400" />
          ) : (
            <Maximize2 className="w-4 h-4 text-slate-400" />
          )}
        </button>
      </div>

      {/* Chart Content */}
      <div className={`p-4 ${isExpanded ? 'min-h-[400px]' : 'min-h-[200px]'}`}>
        {hasData ? (
          <div className="flex flex-col items-center justify-center h-full">
            <BarChart3 className="w-16 h-16 text-slate-600 mb-3" />
            <p className="text-sm text-slate-400 text-center mb-2">
              Chart rendering not yet implemented
            </p>
            <p className="text-xs text-slate-500 text-center">
              Chart type: {chartType}
            </p>
            {chartId && (
              <p className="text-xs text-slate-600 mt-1">ID: {chartId}</p>
            )}
            
            {/* Show data preview in development */}
            {process.env.NODE_ENV === 'development' && (
              <details className="mt-4 w-full">
                <summary className="text-xs text-slate-500 cursor-pointer hover:text-slate-400">
                  View chart data (dev only)
                </summary>
                <pre className="mt-2 p-2 bg-slate-900 rounded text-xs text-slate-400 overflow-auto max-h-40">
                  {JSON.stringify(data, null, 2)}
                </pre>
              </details>
            )}
          </div>
        ) : (
          <div className="flex items-center justify-center h-full">
            <p className="text-sm text-slate-500">No chart data available</p>
          </div>
        )}
      </div>

      {/* Footer with info */}
      <div className="px-4 py-2 bg-slate-900/50 border-t border-slate-700">
        <p className="text-xs text-slate-500">
          💡 Tip: Chart rendering requires a charting library (Chart.js, Recharts, etc.)
        </p>
      </div>
    </div>
  );
};
