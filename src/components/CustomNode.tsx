import { memo, useState } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { GripVertical, Plus, Trash2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { useCanvasStore } from '../store/canvasStore';

export const CustomNode = memo(({ id, data, selected }: NodeProps) => {
  const [isEditing, setIsEditing] = useState(false);
  const [content, setContent] = useState(data.label || '');
  const { updateNode, deleteNode, addNode, nodes } = useCanvasStore();

  const handleDoubleClick = () => {
    setIsEditing(true);
  };

  const handleBlur = async () => {
    setIsEditing(false);
    if (content !== data.label) {
      await updateNode(id, { label: content });
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && e.ctrlKey) {
      handleBlur();
    } else if (e.key === 'Escape') {
      setContent(data.label || '');
      setIsEditing(false);
    }
  };

  const handleAddChild = async () => {
    const node = nodes.find(n => n.id === id);
    if (!node) return;

    const childrenCount = nodes.filter(n => n.data.parentId === id).length;
    const angle = (childrenCount * 60) % 360;
    const distance = 250;
    const x = node.position.x + Math.cos((angle * Math.PI) / 180) * distance;
    const y = node.position.y + Math.sin((angle * Math.PI) / 180) * distance;

    await addNode({
      type: 'custom',
      position: { x, y },
      data: { label: 'New Node', parentId: id }
    });
  };

  const handleDelete = async () => {
    await deleteNode(id);
  };

  return (
    <div
      className={`relative group bg-gradient-to-br from-slate-900 to-slate-800 rounded-lg shadow-2xl transition-all duration-200 ${selected ? 'ring-2 ring-blue-500 shadow-blue-500/50' : 'hover:shadow-xl'
        }`}
      style={{
        minWidth: '300px',
        minHeight: '150px',
        maxWidth: '500px'
      }}
      onDoubleClick={handleDoubleClick}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 !bg-blue-500 !border-2 !border-slate-900"
      />
      <Handle
        type="target"
        position={Position.Left}
        className="w-3 h-3 !bg-blue-500 !border-2 !border-slate-900"
      />

      <div className="absolute -top-2 -left-2 opacity-0 group-hover:opacity-100 transition-opacity cursor-move">
        <div className="bg-slate-700 rounded p-1">
          <GripVertical className="w-4 h-4 text-slate-300" />
        </div>
      </div>

      <div className="absolute -top-2 -right-2 opacity-0 group-hover:opacity-100 transition-opacity flex gap-1">
        <button
          onClick={handleAddChild}
          className="bg-green-600 hover:bg-green-700 rounded p-1 transition-colors"
          title="Add Child Node"
        >
          <Plus className="w-4 h-4 text-white" />
        </button>
        <button
          onClick={handleDelete}
          className="bg-red-600 hover:bg-red-700 rounded p-1 transition-colors"
          title="Delete Node"
        >
          <Trash2 className="w-4 h-4 text-white" />
        </button>
      </div>

      <div className="p-4">
        {isEditing ? (
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            onBlur={handleBlur}
            onKeyDown={handleKeyDown}
            className="w-full h-32 bg-slate-800 text-slate-100 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none font-mono text-sm"
            autoFocus
            placeholder="Enter content (supports Markdown)..."
          />
        ) : (
          <div className="prose prose-invert prose-sm max-w-none">
            <ReactMarkdown>{content || 'Double-click to edit'}</ReactMarkdown>
          </div>
        )}
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        className="w-3 h-3 !bg-green-500 !border-2 !border-slate-900"
      />
      <Handle
        type="source"
        position={Position.Right}
        className="w-3 h-3 !bg-green-500 !border-2 !border-slate-900"
      />
    </div>
  );
});

CustomNode.displayName = 'CustomNode';
