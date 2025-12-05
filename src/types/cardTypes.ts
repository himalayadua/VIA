import { FileText, CheckSquare, Video, Link as LinkIcon, Clock } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

// Card Type Enum
export enum CardType {
  RICH_TEXT = 'rich_text',
  TODO = 'todo',
  VIDEO = 'video',
  LINK = 'link',
  REMINDER = 'reminder'
}

// Base Card Data Interface
export interface BaseCardData {
  title: string;
  cardType: CardType;
  tags: string[];
  createdAt: string;
  updatedAt: string;
  collapsed?: boolean;
  parentId?: string | null;
}

// Type-Specific Data Interfaces
export interface RichTextData extends BaseCardData {
  cardType: CardType.RICH_TEXT;
  content: string; // Markdown content
}

export interface TodoItem {
  id: string;
  text: string;
  completed: boolean;
}

export interface TodoData extends BaseCardData {
  cardType: CardType.TODO;
  items: TodoItem[];
  progress: number; // 0-100
}

export interface VideoData extends BaseCardData {
  cardType: CardType.VIDEO;
  videoUrl: string;
  videoId?: string; // Extracted YouTube ID
  thumbnail?: string;
}

export interface LinkData extends BaseCardData {
  cardType: CardType.LINK;
  url: string;
  description: string;
  favicon?: string;
}

export interface ReminderData extends BaseCardData {
  cardType: CardType.REMINDER;
  reminderDate: string; // ISO date string
  reminderTime: string;
  description: string;
}

// Union Type for all card data
export type CardData = RichTextData | TodoData | VideoData | LinkData | ReminderData;

// Card Theme Configuration
export interface CardTheme {
  background: string; // Solid vibrant color (Tailwind class)
  headerBg: string; // Darker semi-transparent
  textColor: string;
  accentColor: string;
  icon: LucideIcon;
  borderColor: string;
}

export const CARD_THEMES: Record<CardType, CardTheme> = {
  [CardType.RICH_TEXT]: {
    background: 'bg-emerald-500',
    headerBg: 'bg-emerald-900/40',
    textColor: 'text-white',
    accentColor: 'text-emerald-200',
    icon: FileText,
    borderColor: 'border-emerald-600'
  },
  [CardType.TODO]: {
    background: 'bg-blue-500',
    headerBg: 'bg-blue-900/40',
    textColor: 'text-white',
    accentColor: 'text-blue-200',
    icon: CheckSquare,
    borderColor: 'border-blue-600'
  },
  [CardType.VIDEO]: {
    background: 'bg-purple-500',
    headerBg: 'bg-purple-900/40',
    textColor: 'text-white',
    accentColor: 'text-purple-200',
    icon: Video,
    borderColor: 'border-purple-600'
  },
  [CardType.LINK]: {
    background: 'bg-orange-500',
    headerBg: 'bg-orange-900/40',
    textColor: 'text-white',
    accentColor: 'text-orange-200',
    icon: LinkIcon,
    borderColor: 'border-orange-600'
  },
  [CardType.REMINDER]: {
    background: 'bg-amber-500',
    headerBg: 'bg-amber-900/40',
    textColor: 'text-white',
    accentColor: 'text-amber-200',
    icon: Clock,
    borderColor: 'border-amber-600'
  }
};

// Helper function to get card type display name
export function getCardTypeDisplayName(type: CardType): string {
  const names: Record<CardType, string> = {
    [CardType.RICH_TEXT]: 'Rich Text',
    [CardType.TODO]: 'Todo List',
    [CardType.VIDEO]: 'Video',
    [CardType.LINK]: 'Link',
    [CardType.REMINDER]: 'Reminder'
  };
  return names[type];
}

// Helper function to validate card type
export function isValidCardType(type: string): type is CardType {
  return Object.values(CardType).includes(type as CardType);
}

// Helper function to get default card data for a type
export function getDefaultCardData(type: CardType): Partial<CardData> {
  const baseData = {
    title: '',
    cardType: type,
    tags: [],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  };

  switch (type) {
    case CardType.RICH_TEXT:
      return {
        ...baseData,
        content: ''
      } as RichTextData;
    
    case CardType.TODO:
      return {
        ...baseData,
        items: [],
        progress: 0
      } as TodoData;
    
    case CardType.VIDEO:
      return {
        ...baseData,
        videoUrl: '',
        videoId: undefined,
        thumbnail: undefined
      } as VideoData;
    
    case CardType.LINK:
      return {
        ...baseData,
        url: '',
        description: ''
      } as LinkData;
    
    case CardType.REMINDER:
      return {
        ...baseData,
        reminderDate: '',
        reminderTime: '',
        description: ''
      } as ReminderData;
    
    default:
      return baseData;
  }
}

// Helper function to extract YouTube video ID from URL
export function extractYouTubeId(url: string): string | null {
  const patterns = [
    /(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)/,
    /youtube\.com\/embed\/([^&\n?#]+)/,
    /youtube\.com\/v\/([^&\n?#]+)/
  ];

  for (const pattern of patterns) {
    const match = url.match(pattern);
    if (match && match[1]) {
      return match[1];
    }
  }

  return null;
}

// Helper function to validate URL
export function isValidUrl(url: string): boolean {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

// Helper function to calculate todo progress
export function calculateTodoProgress(items: TodoItem[]): number {
  if (items.length === 0) return 0;
  const completed = items.filter(item => item.completed).length;
  return Math.round((completed / items.length) * 100);
}
