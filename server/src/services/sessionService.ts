/**
 * Session Service
 * 
 * Service layer for managing chat sessions and messages in PostgreSQL.
 * Provides clean abstraction for database operations.
 */

import { db } from '../db.js';

export interface MessageMetadata {
  files?: any[];
  toolExecutions?: any[];
  images?: any[];
}

export interface ChatMessage {
  id: string;
  session_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  files: any[];
  tool_executions: any[];
  images: any[];
  created_at: Date;
}

export interface ChatSession {
  id: string;
  canvas_id: string | null;
  created_at: Date;
  updated_at: Date;
  last_activity: Date;
}

export class SessionService {
  /**
   * Save a message to PostgreSQL
   * 
   * @param sessionId - Session ID
   * @param role - Message role (user, assistant, system)
   * @param content - Message content
   * @param metadata - Optional metadata (files, tool executions, images)
   */
  async saveMessage(
    sessionId: string,
    role: 'user' | 'assistant' | 'system',
    content: string,
    metadata?: MessageMetadata
  ): Promise<void> {
    try {
      await db.query(
        `INSERT INTO chat_messages 
         (session_id, role, content, files, tool_executions, images)
         VALUES ($1, $2, $3, $4, $5, $6)`,
        [
          sessionId,
          role,
          content,
          JSON.stringify(metadata?.files || []),
          JSON.stringify(metadata?.toolExecutions || []),
          JSON.stringify(metadata?.images || [])
        ]
      );
      
      console.log(`[SessionService] Saved ${role} message to session ${sessionId}`);
    } catch (error) {
      console.error('[SessionService] Error saving message:', error);
      throw error;
    }
  }

  /**
   * Get chat history for a session
   * 
   * @param sessionId - Session ID
   * @param limit - Maximum number of messages to return (default: 50)
   * @returns Array of chat messages
   */
  async getChatHistory(sessionId: string, limit = 50): Promise<ChatMessage[]> {
    try {
      const result = await db.query(
        `SELECT id, session_id, role, content, files, tool_executions, images, created_at
         FROM chat_messages
         WHERE session_id = $1
         ORDER BY created_at ASC
         LIMIT $2`,
        [sessionId, limit]
      );

      return result.rows;
    } catch (error) {
      console.error('[SessionService] Error fetching chat history:', error);
      throw error;
    }
  }

  /**
   * Create a new chat session
   * 
   * @param canvasId - Optional canvas ID to associate with session
   * @returns Session ID
   */
  async createSession(canvasId?: string): Promise<string> {
    try {
      const result = await db.query(
        `INSERT INTO chat_sessions (canvas_id, created_at, updated_at, last_activity)
         VALUES ($1, NOW(), NOW(), NOW())
         RETURNING id`,
        [canvasId || null]
      );

      const sessionId = result.rows[0].id;
      console.log(`[SessionService] Created session ${sessionId}`);
      return sessionId;
    } catch (error) {
      console.error('[SessionService] Error creating session:', error);
      throw error;
    }
  }

  /**
   * Get session information
   * 
   * @param sessionId - Session ID
   * @returns Session information or null if not found
   */
  async getSession(sessionId: string): Promise<ChatSession | null> {
    try {
      const result = await db.query(
        `SELECT id, canvas_id, created_at, updated_at, last_activity
         FROM chat_sessions
         WHERE id = $1`,
        [sessionId]
      );

      return result.rows[0] || null;
    } catch (error) {
      console.error('[SessionService] Error fetching session:', error);
      throw error;
    }
  }

  /**
   * Clear a session and all its messages
   * 
   * @param sessionId - Session ID to clear
   */
  async clearSession(sessionId: string): Promise<void> {
    try {
      const result = await db.query(
        `DELETE FROM chat_sessions WHERE id = $1 RETURNING id`,
        [sessionId]
      );

      if (result.rows.length === 0) {
        throw new Error('Session not found');
      }

      console.log(`[SessionService] Cleared session ${sessionId}`);
    } catch (error) {
      console.error('[SessionService] Error clearing session:', error);
      throw error;
    }
  }

  /**
   * Cleanup inactive sessions
   * 
   * @param maxAgeHours - Maximum age in hours before session is considered inactive
   * @returns Number of sessions deleted
   */
  async cleanupInactiveSessions(maxAgeHours = 24): Promise<number> {
    try {
      const result = await db.query(
        `SELECT cleanup_inactive_chat_sessions($1) as deleted_count`,
        [maxAgeHours]
      );

      const deletedCount = result.rows[0].deleted_count;
      console.log(`[SessionService] Cleaned up ${deletedCount} inactive sessions`);
      return deletedCount;
    } catch (error) {
      console.error('[SessionService] Error cleaning up sessions:', error);
      throw error;
    }
  }

  /**
   * Get message count for a session
   * 
   * @param sessionId - Session ID
   * @returns Number of messages in session
   */
  async getMessageCount(sessionId: string): Promise<number> {
    try {
      const result = await db.query(
        `SELECT COUNT(*) as count FROM chat_messages WHERE session_id = $1`,
        [sessionId]
      );

      return parseInt(result.rows[0].count);
    } catch (error) {
      console.error('[SessionService] Error getting message count:', error);
      throw error;
    }
  }
}

// Export singleton instance
export const sessionService = new SessionService();

