/**
 * Chat Utilities
 * 
 * Helper functions for chat message processing and grouping.
 */

import { Message } from '../store/chatStore';

export interface MessageGroup {
  type: 'user' | 'assistant';
  messages: Message[];
}

/**
 * Groups consecutive messages by sender (user or assistant)
 * This creates "turns" in the conversation where consecutive assistant
 * messages are grouped together with a single avatar.
 */
export function groupMessagesByTurn(messages: Message[]): MessageGroup[] {
  if (messages.length === 0) {
    return [];
  }

  const groups: MessageGroup[] = [];
  let currentGroup: MessageGroup | null = null;

  for (const message of messages) {
    const messageType = message.role === 'user' ? 'user' : 'assistant';

    // If this is the first message or sender changed, start a new group
    if (!currentGroup || currentGroup.type !== messageType) {
      currentGroup = {
        type: messageType,
        messages: [message]
      };
      groups.push(currentGroup);
    } else {
      // Same sender, add to current group
      currentGroup.messages.push(message);
    }
  }

  return groups;
}

/**
 * Checks if a message is from the assistant
 */
export function isAssistantMessage(message: Message): boolean {
  return message.role === 'assistant' || message.role === 'system';
}

/**
 * Checks if a message is from the user
 */
export function isUserMessage(message: Message): boolean {
  return message.role === 'user';
}
