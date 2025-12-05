import { useState } from 'react';
import { Edit2, Trash2, FolderOpen } from 'lucide-react';
import { getCanvasTheme, formatCanvasNumber } from '../utils/canvasThemes';

interface CanvasCardProps {
  canvas: {
    id: string;
    name: string;
    description: string;
    created_at: string;
    updated_at: string;
  };
  index: number;
  isActive: boolean;
  onSelect: () => void;
  onDelete: (e: React.MouseEvent) => void;
  onUpdate: (name: string, description: string) => Promise<void>;
}

export const CanvasCard = ({
  canvas,
  index,
  isActive,
  onSelect,
  onDelete,
  onUpdate
}: CanvasCardProps) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editName, setEditName] = useState(canvas.name);
  const [editDescription, setEditDescription] = useState(canvas.description);
  const [isSaving, setIsSaving] = useState(false);

  const theme = getCanvasTheme(canvas.id);
  const canvasNumber = formatCanvasNumber(index);

  const handleSave = async () => {
    if (!editName.trim()) return;

    setIsSaving(true);
    try {
      await onUpdate(editName, editDescription);
      setIsEditing(false);
    } catch (error) {
      console.error('Failed to update canvas:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    setEditName(canvas.name);
    setEditDescription(canvas.description);
    setIsEditing(false);
  };

  const handleEdit = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsEditing(true);
  };

  if (isEditing) {
    return (
      <div
        className={`relative bg-slate-800 rounded-xl p-6 border-2 transition-all ${
          isActive ? 'border-blue-500 ring-4 ring-blue-500/20' : 'border-slate-700'
        }`}
      >
        <div className="space-y-4">
          <div>
            <label className="block text-xs text-slate-400 mb-1">Canvas Name</label>
            <input
              type="text"
              value={editName}
              onChange={(e) => setEditName(e.target.value)}
              className="w-full bg-slate-900 text-slate-100 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter canvas name..."
              autoFocus
            />
          </div>

          <div>
            <label className="block text-xs text-slate-400 mb-1">Description</label>
            <textarea
              value={editDescription}
              onChange={(e) => setEditDescription(e.target.value)}
              className="w-full bg-slate-900 text-slate-100 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              placeholder="Add a description..."
              rows={3}
            />
          </div>

          <div className="flex gap-2">
            <button
              onClick={handleSave}
              disabled={isSaving || !editName.trim()}
              className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 disabled:cursor-not-allowed text-white px-4 py-2 rounded transition-colors"
            >
              {isSaving ? 'Saving...' : 'Save'}
            </button>
            <button
              onClick={handleCancel}
              disabled={isSaving}
              className="flex-1 bg-slate-700 hover:bg-slate-600 disabled:bg-slate-800 text-slate-200 px-4 py-2 rounded transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      onClick={onSelect}
      className={`group relative bg-gradient-to-br ${theme.gradient} rounded-xl p-6 cursor-pointer transition-all duration-300 hover:scale-105 hover:shadow-2xl overflow-hidden ${
        isActive ? `ring-4 ${theme.ring} ring-offset-2 ring-offset-slate-950` : ''
      }`}
    >
      {/* Large numbered badge in background */}
      <div className="absolute top-2 right-2 text-8xl font-bold text-white/10 select-none pointer-events-none">
        {canvasNumber}
      </div>

      {/* Action buttons (visible on hover) */}
      <div className="absolute top-3 right-3 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
        <button
          onClick={handleEdit}
          className="p-2 bg-white/20 hover:bg-white/30 backdrop-blur-sm rounded-lg transition-colors"
          title="Edit canvas"
        >
          <Edit2 className="w-4 h-4 text-white" />
        </button>
        <button
          onClick={onDelete}
          className="p-2 bg-white/20 hover:bg-red-500/80 backdrop-blur-sm rounded-lg transition-colors"
          title="Delete canvas"
        >
          <Trash2 className="w-4 h-4 text-white" />
        </button>
      </div>

      {/* Content */}
      <div className="relative z-10 flex flex-col h-full">
        {/* Canvas name */}
        <h3 className="text-xl font-bold text-white mb-2 pr-20 line-clamp-2">
          {canvas.name}
        </h3>

        {/* Description */}
        {canvas.description && (
          <p className="text-sm text-white/80 mb-4 line-clamp-3 flex-1">
            {canvas.description}
          </p>
        )}

        {/* Metadata */}
        <div className="text-xs text-white/60 mb-4">
          Updated {new Date(canvas.updated_at).toLocaleDateString()}
        </div>

        {/* Open button */}
        <button
          onClick={(e) => {
            e.stopPropagation();
            onSelect();
          }}
          className="w-full bg-white/20 hover:bg-white/30 backdrop-blur-sm text-white font-medium py-2 px-4 rounded-lg transition-colors flex items-center justify-center gap-2"
        >
          <FolderOpen className="w-4 h-4" />
          Open Canvas
        </button>
      </div>

      {/* Active indicator */}
      {isActive && (
        <div className="absolute top-3 left-3 bg-blue-500 text-white text-xs font-bold px-2 py-1 rounded">
          ACTIVE
        </div>
      )}
    </div>
  );
};
