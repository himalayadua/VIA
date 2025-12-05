import { memo, useState } from 'react';
import { NodeProps } from 'reactflow';
import { Calendar, Clock } from 'lucide-react';
import { BaseNode } from './BaseNode';
import { CardType } from '../../types/cardTypes';

export const ReminderNode = memo(({ id, data, selected }: NodeProps) => {
  const [title, setTitle] = useState(data.title || 'Reminder');
  const [reminderDate, setReminderDate] = useState(data.reminderDate || '');
  const [reminderTime, setReminderTime] = useState(data.reminderTime || '');
  const [description, setDescription] = useState(data.description || '');
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [isEditingDescription, setIsEditingDescription] = useState(false);

  const handleTitleBlur = () => {
    setIsEditingTitle(false);
    if (data.onUpdateTitle) {
      data.onUpdateTitle(title);
    }
  };

  const handleDateTimeChange = (date?: string, time?: string) => {
    if (data.onUpdateReminder) {
      data.onUpdateReminder(
        date !== undefined ? date : reminderDate,
        time !== undefined ? time : reminderTime,
        description
      );
    }
  };

  const handleDescriptionBlur = () => {
    setIsEditingDescription(false);
    if (data.onUpdateReminder) {
      data.onUpdateReminder(reminderDate, reminderTime, description);
    }
  };

  const formatDateTime = () => {
    if (!reminderDate) return null;
    
    const date = new Date(reminderDate);
    const dateStr = date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric', 
      year: 'numeric' 
    });
    
    return reminderTime ? `${dateStr} at ${reminderTime}` : dateStr;
  };

  return (
    <BaseNode
      id={id}
      selected={selected}
      cardType={CardType.REMINDER}
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

        {/* Date and Time Pickers */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-white/70" />
            <input
              type="date"
              value={reminderDate}
              onChange={(e) => {
                setReminderDate(e.target.value);
                handleDateTimeChange(e.target.value, undefined);
              }}
              className="flex-1 bg-white/10 text-white text-sm rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-white/30"
            />
          </div>
          
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-white/70" />
            <input
              type="time"
              value={reminderTime}
              onChange={(e) => {
                setReminderTime(e.target.value);
                handleDateTimeChange(undefined, e.target.value);
              }}
              className="flex-1 bg-white/10 text-white text-sm rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-white/30"
            />
          </div>
        </div>

        {/* Formatted Display */}
        {formatDateTime() && (
          <div className="bg-white/10 rounded px-3 py-2 text-sm font-medium">
            {formatDateTime()}
          </div>
        )}

        {/* Description */}
        {isEditingDescription ? (
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            onBlur={handleDescriptionBlur}
            placeholder="Add a description..."
            className="w-full h-20 bg-white/10 text-white text-sm rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-white/30 resize-none"
            autoFocus
          />
        ) : description ? (
          <p
            onClick={() => setIsEditingDescription(true)}
            className="text-sm text-white/80 cursor-pointer hover:bg-white/5 rounded p-2 transition-colors"
          >
            {description}
          </p>
        ) : (
          <button
            onClick={() => setIsEditingDescription(true)}
            className="text-sm text-white/50 hover:text-white/70 transition-colors"
          >
            + Add description
          </button>
        )}
      </div>
    </BaseNode>
  );
});

ReminderNode.displayName = 'ReminderNode';
