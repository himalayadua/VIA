import { memo, useState } from 'react';
import { NodeProps } from 'reactflow';
import { Plus, Check } from 'lucide-react';
import { BaseNode } from './BaseNode';
import { CardType, TodoItem, calculateTodoProgress } from '../../types/cardTypes';

export const TodoNode = memo(({ id, data, selected }: NodeProps) => {
  const [title, setTitle] = useState(data.title || 'Todo List');
  const [items, setItems] = useState<TodoItem[]>(data.items || []);
  const [newItemText, setNewItemText] = useState('');
  const [isEditingTitle, setIsEditingTitle] = useState(false);

  const progress = calculateTodoProgress(items);

  const handleToggleItem = (itemId: string) => {
    const updatedItems = items.map(item =>
      item.id === itemId ? { ...item, completed: !item.completed } : item
    );
    setItems(updatedItems);
    if (data.onUpdateItems) {
      data.onUpdateItems(updatedItems);
    }
  };

  const handleAddItem = () => {
    if (!newItemText.trim()) return;

    const newItem: TodoItem = {
      id: Date.now().toString(),
      text: newItemText,
      completed: false
    };

    const updatedItems = [...items, newItem];
    setItems(updatedItems);
    setNewItemText('');
    
    if (data.onUpdateItems) {
      data.onUpdateItems(updatedItems);
    }
  };

  const handleDeleteItem = (itemId: string) => {
    const updatedItems = items.filter(item => item.id !== itemId);
    setItems(updatedItems);
    if (data.onUpdateItems) {
      data.onUpdateItems(updatedItems);
    }
  };

  const handleTitleBlur = () => {
    setIsEditingTitle(false);
    if (data.onUpdateTitle) {
      data.onUpdateTitle(title);
    }
  };

  return (
    <BaseNode
      id={id}
      selected={selected}
      cardType={CardType.TODO}
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

        {/* Progress Bar */}
        <div className="space-y-1">
          <div className="flex justify-between text-xs text-white/70">
            <span>{items.filter(i => i.completed).length} of {items.length} completed</span>
            <span>{progress}%</span>
          </div>
          <div className="w-full h-2 bg-white/20 rounded-full overflow-hidden">
            <div
              className="h-full bg-white/80 transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Todo Items */}
        <div className="space-y-2 max-h-48 overflow-y-auto">
          {items.map((item) => (
            <div
              key={item.id}
              className="flex items-start gap-2 group hover:bg-white/5 rounded p-2 transition-colors"
            >
              <button
                onClick={() => handleToggleItem(item.id)}
                className={`flex-shrink-0 w-5 h-5 rounded border-2 flex items-center justify-center transition-colors ${
                  item.completed
                    ? 'bg-white/90 border-white/90'
                    : 'border-white/50 hover:border-white/70'
                }`}
              >
                {item.completed && <Check className="w-3 h-3 text-blue-600" />}
              </button>
              <span
                className={`flex-1 text-sm ${
                  item.completed ? 'line-through text-white/50' : 'text-white'
                }`}
              >
                {item.text}
              </span>
              <button
                onClick={() => handleDeleteItem(item.id)}
                className="opacity-0 group-hover:opacity-100 text-white/50 hover:text-red-400 transition-all text-xs"
              >
                ×
              </button>
            </div>
          ))}
        </div>

        {/* Add Item Input */}
        <div className="flex gap-2">
          <input
            type="text"
            value={newItemText}
            onChange={(e) => setNewItemText(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAddItem()}
            placeholder="Add new item..."
            className="flex-1 bg-white/10 text-white text-sm rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-white/30"
          />
          <button
            onClick={handleAddItem}
            className="bg-white/20 hover:bg-white/30 rounded p-2 transition-colors"
            title="Add item"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
      </div>
    </BaseNode>
  );
});

TodoNode.displayName = 'TodoNode';
