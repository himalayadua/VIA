import { memo, useState } from 'react';
import { NodeProps } from 'reactflow';
import ReactMarkdown from 'react-markdown';
import { BaseNode } from './BaseNode';
import { CardType } from '../../types/cardTypes';

export const RichTextNode = memo(({ id, data, selected }: NodeProps) => {
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [isEditingContent, setIsEditingContent] = useState(false);
  const [title, setTitle] = useState(data.title || 'Untitled');
  const [content, setContent] = useState(data.content || '');

  const handleTitleClick = () => {
    setIsEditingTitle(true);
  };

  const handleTitleBlur = () => {
    setIsEditingTitle(false);
    if (data.onUpdateTitle) {
      data.onUpdateTitle(title);
    }
  };

  const handleContentDoubleClick = () => {
    setIsEditingContent(true);
  };

  const handleContentBlur = () => {
    setIsEditingContent(false);
    if (data.onUpdateContent) {
      data.onUpdateContent(content);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent, isTitle: boolean) => {
    if (e.key === 'Escape') {
      if (isTitle) {
        setTitle(data.title || 'Untitled');
        setIsEditingTitle(false);
      } else {
        setContent(data.content || '');
        setIsEditingContent(false);
      }
    } else if (e.key === 'Enter' && e.ctrlKey && !isTitle) {
      handleContentBlur();
    }
  };

  return (
    <BaseNode
      id={id}
      selected={selected}
      cardType={CardType.RICH_TEXT}
      title={title}
      tags={data.tags || []}
      timestamp={data.createdAt || new Date().toISOString()}
      collapsed={data.collapsed}
      hasChildren={data.hasChildren}
      onToggleCollapse={data.onToggleCollapse}
      onMenuClick={data.onMenuClick}
      onTagRemove={data.onTagRemove}
      onTagAdd={data.onTagAdd}
      sourceType={data.sourceType}
      sourceUrl={data.sourceUrl}
      hasConflictFlag={data.hasConflict}
      onSourceClick={data.onSourceClick}
    >
      <div className="space-y-3">
        {/* Title */}
        {isEditingTitle ? (
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            onBlur={handleTitleBlur}
            onKeyDown={(e) => handleKeyDown(e, true)}
            className="w-full bg-white/10 text-white text-lg font-semibold rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-white/30"
            autoFocus
            placeholder="Enter title..."
          />
        ) : (
          <h3
            onClick={handleTitleClick}
            className="text-lg font-semibold cursor-pointer hover:bg-white/10 rounded px-2 py-1 transition-colors"
          >
            {title}
          </h3>
        )}

        {/* Content */}
        {isEditingContent ? (
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            onBlur={handleContentBlur}
            onKeyDown={(e) => handleKeyDown(e, false)}
            className="w-full h-32 bg-white/10 text-white rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-white/30 resize-none font-mono text-sm"
            autoFocus
            placeholder="Enter content (supports Markdown)..."
          />
        ) : (
          <div
            onDoubleClick={handleContentDoubleClick}
            className="prose prose-invert prose-sm max-w-none cursor-pointer hover:bg-white/5 rounded p-2 transition-colors min-h-[60px]"
          >
            {content ? (
              <ReactMarkdown>{content}</ReactMarkdown>
            ) : (
              <p className="text-white/50 italic">Double-click to edit</p>
            )}
          </div>
        )}
      </div>
    </BaseNode>
  );
});

RichTextNode.displayName = 'RichTextNode';
