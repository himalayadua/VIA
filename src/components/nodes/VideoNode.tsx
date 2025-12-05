import { memo, useState, useEffect } from 'react';
import { NodeProps } from 'reactflow';
import { BaseNode } from './BaseNode';
import { CardType, extractYouTubeId } from '../../types/cardTypes';

export const VideoNode = memo(({ id, data, selected }: NodeProps) => {
  const [title, setTitle] = useState(data.title || 'Video');
  const [videoUrl, setVideoUrl] = useState(data.videoUrl || '');
  const [videoId, setVideoId] = useState(data.videoId || '');
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [isEditingUrl, setIsEditingUrl] = useState(false);

  useEffect(() => {
    if (videoUrl) {
      const id = extractYouTubeId(videoUrl);
      if (id) {
        setVideoId(id);
        if (data.onUpdateVideo) {
          data.onUpdateVideo(videoUrl, id);
        }
      }
    }
  }, [videoUrl]);

  const handleTitleBlur = () => {
    setIsEditingTitle(false);
    if (data.onUpdateTitle) {
      data.onUpdateTitle(title);
    }
  };

  const handleUrlBlur = () => {
    setIsEditingUrl(false);
  };

  return (
    <BaseNode
      id={id}
      selected={selected}
      cardType={CardType.VIDEO}
      title={title}
      tags={data.tags || []}
      timestamp={data.createdAt || new Date().toISOString()}
      collapsed={data.collapsed}
      hasChildren={data.hasChildren}
      onToggleCollapse={data.onToggleCollapse}
      onMenuClick={data.onMenuClick}
      onTagRemove={data.onTagRemove}
      onTagAdd={data.onTagAdd}
    >
      <div className="space-y-3">
        {/* Title */}
        {isEditingTitle ? (
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            onBlur={handleTitleBlur}
            onKeyDown={(e) => e.key === 'Enter' && handleTitleBlur()}
            className="w-full bg-white/10 text-white text-lg font-semibold rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-white/30"
            autoFocus
          />
        ) : (
          <h3
            onClick={() => setIsEditingTitle(true)}
            className="text-lg font-semibold cursor-pointer hover:bg-white/10 rounded px-2 py-1 transition-colors"
          >
            {title}
          </h3>
        )}

        {/* URL Input */}
        {isEditingUrl || !videoId ? (
          <div className="space-y-2">
            <input
              type="text"
              value={videoUrl}
              onChange={(e) => setVideoUrl(e.target.value)}
              onBlur={handleUrlBlur}
              placeholder="Enter YouTube URL..."
              className="w-full bg-white/10 text-white text-sm rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-white/30"
              autoFocus={!videoId}
            />
            {videoUrl && !videoId && (
              <p className="text-xs text-red-300">Invalid YouTube URL</p>
            )}
          </div>
        ) : (
          <div className="space-y-2">
            {/* Video Embed */}
            <div className="relative w-full aspect-video bg-black/20 rounded overflow-hidden">
              <iframe
                src={`https://www.youtube.com/embed/${videoId}`}
                title={title}
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
                className="absolute inset-0 w-full h-full"
              />
            </div>
            <button
              onClick={() => setIsEditingUrl(true)}
              className="text-xs text-white/70 hover:text-white transition-colors"
            >
              Change video
            </button>
          </div>
        )}
      </div>
    </BaseNode>
  );
});

VideoNode.displayName = 'VideoNode';
