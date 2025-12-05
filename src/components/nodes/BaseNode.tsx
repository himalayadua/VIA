import { memo, ReactNode, useState, KeyboardEvent } from 'react';
import { Handle, Position } from 'reactflow';
import { GripVertical, MoreVertical, ChevronDown, ChevronRight, X, Plus } from 'lucide-react';
import { CARD_THEMES, CardType, getCardTypeDisplayName } from '../../types/cardTypes';
import { 
  getSourceIcon, 
  getSourceColor, 
  getSourceDisplayName, 
  getShortUrl,
  hasConflict,
  getConflictBadge,
  type SourceType 
} from '../../utils/sourceAttribution';
import { getCardTypeIcon } from '../../utils/cardTypeUtils';

export interface BaseNodeProps {
  id: string;
  selected: boolean;
  cardType: CardType;
  title: string;
  tags: string[];
  timestamp: string;
  collapsed?: boolean;
  hasChildren?: boolean;
  hiddenCount?: number;
  onToggleCollapse?: () => void;
  onMenuClick?: (e: React.MouseEvent) => void;
  onTagRemove?: (tag: string) => void;
  onTagAdd?: (tag: string) => void;
  children: ReactNode;
  // Source attribution
  sourceType?: SourceType;
  sourceUrl?: string;
  hasConflictFlag?: boolean;
  onSourceClick?: () => void;
  // Learning engagement
  readCount?: number;
  importance?: 'normal' | 'high';
  cardTypeIcon?: string;
}

export const BaseNode = memo(({
  id,
  selected,
  cardType,
  title,
  tags,
  timestamp,
  collapsed = false,
  hasChildren = false,
  hiddenCount = 0,
  onToggleCollapse,
  onMenuClick,
  onTagRemove,
  onTagAdd,
  children,
  sourceType,
  sourceUrl,
  hasConflictFlag,
  onSourceClick,
  readCount = 0,
  importance = 'normal',
  cardTypeIcon
}: BaseNodeProps) => {
  const theme = CARD_THEMES[cardType];
  const Icon = theme.icon;
  
  // Get card type icon
  const typeIcon = cardTypeIcon ? getCardTypeIcon(cardTypeIcon) : '';
  const isImportant = importance === 'high';
  const isRead = readCount > 0;
  
  // Tag input state
  const [isAddingTag, setIsAddingTag] = useState(false);
  const [tagInput, setTagInput] = useState('');

  const handleTagInputKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && tagInput.trim()) {
      e.preventDefault();
      const newTag = tagInput.trim();
      
      // Validate tag length (max 50 chars)
      if (newTag.length > 50) {
        return;
      }
      
      // Check for duplicates
      if (tags.includes(newTag)) {
        setTagInput('');
        return;
      }
      
      // Add tag
      if (onTagAdd) {
        onTagAdd(newTag);
      }
      
      setTagInput('');
      setIsAddingTag(false);
    } else if (e.key === 'Escape') {
      setTagInput('');
      setIsAddingTag(false);
    }
  };

  const handleAddTagClick = () => {
    setIsAddingTag(true);
  };

  const handleTagInputBlur = () => {
    setTagInput('');
    setIsAddingTag(false);
  };

  return (
    <div
      className={`relative group rounded-lg shadow-2xl transition-all duration-200 overflow-hidden ${
        theme.background
      } ${selected ? 'ring-2 ring-blue-400 shadow-blue-500/50' : 'hover:shadow-xl'} ${
        hasConflict(hasConflictFlag) ? 'conflict-card conflict-border-pulse' : ''
      }`}
      style={{
        minWidth: '300px',
        minHeight: '150px',
        maxWidth: '500px'
      }}
    >
      {/* Connection Handles */}
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 !bg-blue-500 !border-2 !border-white"
      />
      <Handle
        type="target"
        position={Position.Left}
        className="w-3 h-3 !bg-blue-500 !border-2 !border-white"
      />

      {/* Drag Handle */}
      <div className="absolute -top-2 -left-2 opacity-0 group-hover:opacity-100 transition-opacity cursor-move z-10">
        <div className="bg-slate-700/90 backdrop-blur-sm rounded p-1 shadow-lg">
          <GripVertical className="w-4 h-4 text-slate-300" />
        </div>
      </div>

      {/* Geometric Circle Decorations */}
      <div className="absolute top-4 right-4 w-24 h-24 rounded-full bg-white/5 blur-2xl pointer-events-none" />
      <div className="absolute bottom-4 left-4 w-16 h-16 rounded-full bg-white/5 blur-xl pointer-events-none" />

      {/* Header */}
      <div className={`${theme.headerBg} backdrop-blur-sm px-4 py-3 flex items-center justify-between border-b border-white/10`}>
        <div className="flex items-center gap-2 flex-1">
          {/* Card Type Icon (if set) */}
          {typeIcon && (
            <span className="text-lg" title={cardTypeIcon}>
              {typeIcon}
            </span>
          )}
          
          {/* Card Type Badge */}
          <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-black/20">
            <Icon className="w-4 h-4" />
            <span className="text-xs font-medium">{getCardTypeDisplayName(cardType)}</span>
          </div>
          
          {/* Importance Badge */}
          {isImportant && (
            <span className="text-sm" title="Important card">
              ⭐
            </span>
          )}
          
          {/* Read Indicator */}
          {isRead && (
            <span className="text-xs opacity-70" title={`Read ${readCount} time${readCount !== 1 ? 's' : ''}`}>
              ✅
            </span>
          )}

          {/* Source Badge */}
          {sourceType && sourceType !== 'manual' && (
            <button
              onClick={onSourceClick}
              className={`flex items-center gap-1.5 px-2 py-1 rounded border transition-all hover:scale-105 ${getSourceColor(sourceType)}`}
              title={sourceUrl ? `${getSourceDisplayName(sourceType)}: ${getShortUrl(sourceUrl)}` : getSourceDisplayName(sourceType)}
            >
              <span className="text-sm">{getSourceIcon(sourceType)}</span>
              <span className="text-xs font-medium">
                {sourceUrl ? getShortUrl(sourceUrl) : getSourceDisplayName(sourceType)}
              </span>
            </button>
          )}

          {/* Conflict Badge */}
          {hasConflict(hasConflictFlag) && (
            <button
              onClick={onSourceClick}
              className={`flex items-center gap-1.5 px-2 py-1 rounded border transition-all hover:scale-105 conflict-pulse ${getConflictBadge().color}`}
              title="This card has conflicting information - click to view details"
            >
              <span className="text-sm">{getConflictBadge().icon}</span>
              <span className="text-xs font-medium">{getConflictBadge().text}</span>
            </button>
          )}

          {/* Collapse/Expand Button */}
          {hasChildren && onToggleCollapse && (
            <button
              onClick={onToggleCollapse}
              className="p-1 hover:bg-white/10 rounded transition-colors"
              title={collapsed ? 'Expand' : 'Collapse'}
            >
              {collapsed ? (
                <ChevronRight className="w-4 h-4" />
              ) : (
                <ChevronDown className="w-4 h-4" />
              )}
            </button>
          )}

          {/* Collapsed Badge */}
          {collapsed && hasChildren && hiddenCount > 0 && (
            <span className="px-2 py-0.5 text-xs bg-white/20 rounded">
              +{hiddenCount}
            </span>
          )}
        </div>

        {/* Three-dot Menu */}
        <button
          onClick={onMenuClick}
          className="p-1.5 hover:bg-white/10 rounded transition-colors"
          title="More options"
        >
          <MoreVertical className="w-4 h-4" />
        </button>
      </div>

      {/* Content Area */}
      <div className="p-4">
        {children}
      </div>

      {/* Footer - Tags and Timestamp */}
      <div className="px-4 pb-4 space-y-2">
        {/* Tags */}
        <div className="flex flex-wrap gap-1.5 items-center">
          {tags.map((tag, index) => (
            <div
              key={index}
              className={`flex items-center gap-1 px-2 py-1 rounded text-xs bg-black/20 backdrop-blur-sm ${theme.accentColor}`}
            >
              <span>{tag}</span>
              {onTagRemove && (
                <button
                  onClick={() => onTagRemove(tag)}
                  className="hover:bg-white/10 rounded p-0.5 transition-colors"
                  title="Remove tag"
                >
                  <X className="w-3 h-3" />
                </button>
              )}
            </div>
          ))}
          
          {/* Tag Input */}
          {isAddingTag ? (
            <input
              type="text"
              value={tagInput}
              onChange={(e) => setTagInput(e.target.value)}
              onKeyDown={handleTagInputKeyDown}
              onBlur={handleTagInputBlur}
              className="px-2 py-1 text-xs bg-black/20 backdrop-blur-sm rounded focus:outline-none focus:ring-1 focus:ring-white/30"
              placeholder="Add tag..."
              maxLength={50}
              autoFocus
            />
          ) : (
            onTagAdd && (
              <button
                onClick={handleAddTagClick}
                className="flex items-center gap-1 px-2 py-1 text-xs bg-black/20 backdrop-blur-sm rounded hover:bg-black/30 transition-colors"
                title="Add tag"
              >
                <Plus className="w-3 h-3" />
                <span>Add tag</span>
              </button>
            )
          )}
        </div>

        {/* Timestamp */}
        <div className={`flex items-center gap-1.5 text-xs ${theme.accentColor} opacity-70`}>
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{new Date(timestamp).toLocaleString()}</span>
        </div>
      </div>

      {/* Source Handles */}
      <Handle
        type="source"
        position={Position.Bottom}
        className="w-3 h-3 !bg-green-500 !border-2 !border-white"
      />
      <Handle
        type="source"
        position={Position.Right}
        className="w-3 h-3 !bg-green-500 !border-2 !border-white"
      />
    </div>
  );
});

BaseNode.displayName = 'BaseNode';
