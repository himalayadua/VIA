/**
 * ImageRenderer Component
 * 
 * Renders images from references with click-to-enlarge functionality.
 * Supports loading states, error handling, and accessibility.
 */

import { useState } from 'react';
import { X, Maximize2, AlertCircle } from 'lucide-react';

interface ImageRendererProps {
  imageId: string;
  alt?: string;
  sessionId?: string;
}

export const ImageRenderer = ({ imageId, alt, sessionId }: ImageRendererProps) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);

  // In a real implementation, this would fetch the image from the backend
  // For now, we'll show a placeholder
  const imageUrl = `/api/images/${imageId}?session=${sessionId}`;

  const handleImageLoad = () => {
    setIsLoading(false);
    setHasError(false);
  };

  const handleImageError = () => {
    setIsLoading(false);
    setHasError(true);
  };

  const handleImageClick = () => {
    if (!hasError) {
      setIsModalOpen(true);
    }
  };

  return (
    <>
      {/* Image Container */}
      <div className="my-3 relative group">
        <div className="relative rounded-lg overflow-hidden border border-slate-700 bg-slate-800">
          {/* Loading State */}
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-slate-800">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            </div>
          )}

          {/* Error State */}
          {hasError && (
            <div className="flex flex-col items-center justify-center p-8 text-slate-500">
              <AlertCircle className="w-12 h-12 mb-3" />
              <p className="text-sm">Failed to load image</p>
              <p className="text-xs mt-1">ID: {imageId}</p>
            </div>
          )}

          {/* Image */}
          {!hasError && (
            <img
              src={imageUrl}
              alt={alt || `Image ${imageId}`}
              className="w-full h-auto cursor-pointer hover:opacity-90 transition-opacity"
              onLoad={handleImageLoad}
              onError={handleImageError}
              onClick={handleImageClick}
            />
          )}

          {/* Expand Icon Overlay */}
          {!hasError && !isLoading && (
            <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
              <div className="bg-slate-900/80 rounded p-1.5">
                <Maximize2 className="w-4 h-4 text-slate-300" />
              </div>
            </div>
          )}
        </div>

        {/* Alt Text / Caption */}
        {alt && !hasError && (
          <p className="text-xs text-slate-500 mt-2 italic">{alt}</p>
        )}
      </div>

      {/* Lightbox Modal */}
      {isModalOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm animate-fade-in"
          onClick={() => setIsModalOpen(false)}
        >
          <div className="relative max-w-7xl max-h-[90vh] p-4">
            {/* Close Button */}
            <button
              onClick={() => setIsModalOpen(false)}
              className="absolute top-6 right-6 p-2 bg-slate-900/80 hover:bg-slate-800 rounded-full transition-colors z-10"
              title="Close"
            >
              <X className="w-6 h-6 text-slate-300" />
            </button>

            {/* Full Size Image */}
            <img
              src={imageUrl}
              alt={alt || `Image ${imageId}`}
              className="max-w-full max-h-[90vh] object-contain rounded-lg"
              onClick={(e) => e.stopPropagation()}
            />

            {/* Caption in Modal */}
            {alt && (
              <div className="absolute bottom-6 left-1/2 transform -translate-x-1/2 bg-slate-900/90 px-4 py-2 rounded-lg">
                <p className="text-sm text-slate-200">{alt}</p>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
};
