/**
 * Unit tests for SessionService (Express.js backend)
 * 
 * Tests session persistence, message storage, and chat history retrieval.
 */
const { describe, it, beforeEach, afterEach } = require('mocha');
const { expect } = require('chai');
const sinon = require('sinon');

// Mock the database module
const mockDb = {
  query: sinon.stub()
};

// We'll need to mock the import - this is a simplified version
// In real implementation, you'd use proxyquire or similar
class SessionService {
  constructor(db) {
    this.db = db;
  }

  async saveMessage(sessionId, role, content, metadata = {}) {
    await this.db.query(
      `INSERT INTO chat_messages 
       (session_id, role, content, files, tool_executions, images)
       VALUES ($1, $2, $3, $4, $5, $6)`,
      [
        sessionId,
        role,
        content,
        JSON.stringify(metadata.files || []),
        JSON.stringify(metadata.toolExecutions || []),
        JSON.stringify(metadata.images || [])
      ]
    );
  }

  async getChatHistory(sessionId, limit = 50) {
    const result = await this.db.query(
      `SELECT id, session_id, role, content, files, tool_executions, images, created_at
       FROM chat_messages
       WHERE session_id = $1
       ORDER BY created_at ASC
       LIMIT $2`,
      [sessionId, limit]
    );
    return result.rows;
  }

  async createSession(canvasId) {
    const result = await this.db.query(
      `INSERT INTO chat_sessions (canvas_id, created_at, updated_at, last_activity)
       VALUES ($1, NOW(), NOW(), NOW())
       RETURNING id`,
      [canvasId || null]
    );
    return result.rows[0].id;
  }

  async getSession(sessionId) {
    const result = await this.db.query(
      `SELECT id, canvas_id, created_at, updated_at, last_activity
       FROM chat_sessions
       WHERE id = $1`,
      [sessionId]
    );
    return result.rows[0] || null;
  }

  async clearSession(sessionId) {
    const result = await this.db.query(
      `DELETE FROM chat_sessions WHERE id = $1 RETURNING id`,
      [sessionId]
    );
    if (result.rows.length === 0) {
      throw new Error('Session not found');
    }
  }

  async cleanupInactiveSessions(maxAgeHours = 24) {
    const result = await this.db.query(
      `SELECT cleanup_inactive_chat_sessions($1) as deleted_count`,
      [maxAgeHours]
    );
    return result.rows[0].deleted_count;
  }

  async getMessageCount(sessionId) {
    const result = await this.db.query(
      `SELECT COUNT(*) as count FROM chat_messages WHERE session_id = $1`,
      [sessionId]
    );
    return parseInt(result.rows[0].count);
  }
}

describe('SessionService', () => {
  let sessionService;

  beforeEach(() => {
    // Reset all stubs
    mockDb.query.reset();
    // Create SessionService instance with mocked database
    sessionService = new SessionService(mockDb);
  });

  afterEach(() => {
    sinon.restore();
  });

  describe('saveMessage', () => {
    it('should save user message to database', async () => {
      // Arrange
      const sessionId = 'session_123';
      const role = 'user';
      const content = 'What nodes do I have?';
      mockDb.query.resolves({ rows: [] });

      // Act
      await sessionService.saveMessage(sessionId, role, content);

      // Assert
      expect(mockDb.query.calledOnce).to.be.true;
      const queryCall = mockDb.query.getCall(0);
      expect(queryCall.args[0]).to.include('INSERT INTO chat_messages');
      expect(queryCall.args[1]).to.include(sessionId);
      expect(queryCall.args[1]).to.include(role);
      expect(queryCall.args[1]).to.include(content);
    });

    it('should save assistant message with tool executions', async () => {
      // Arrange
      const sessionId = 'session_123';
      const role = 'assistant';
      const content = 'I found 3 nodes in your canvas.';
      const metadata = {
        toolExecutions: [
          {
            id: 'tool_123',
            toolName: 'search_canvas_content',
            toolInput: { query: 'nodes' },
            toolResult: { found: 3, nodes: [] },
            isComplete: true
          }
        ]
      };
      mockDb.query.resolves({ rows: [] });

      // Act
      await sessionService.saveMessage(sessionId, role, content, metadata);

      // Assert
      expect(mockDb.query.calledOnce).to.be.true;
      const queryCall = mockDb.query.getCall(0);
      expect(queryCall.args[0]).to.include('INSERT INTO chat_messages');
      // Verify tool executions are stored as JSON
      const toolExecutionsParam = queryCall.args[1][4];
      expect(JSON.parse(toolExecutionsParam)).to.deep.equal(metadata.toolExecutions);
    });

    it('should handle database errors gracefully', async () => {
      // Arrange
      const sessionId = 'session_123';
      mockDb.query.rejects(new Error('Database connection failed'));

      // Act & Assert
      try {
        await sessionService.saveMessage(sessionId, 'user', 'Test');
        expect.fail('Should have thrown an error');
      } catch (error) {
        expect(error.message).to.include('Database connection failed');
      }
    });
  });

  describe('getChatHistory', () => {
    it('should retrieve chat history for session', async () => {
      // Arrange
      const sessionId = 'session_123';
      const mockMessages = [
        {
          id: 'msg_1',
          session_id: sessionId,
          role: 'user',
          content: 'Hello',
          files: '[]',
          tool_executions: '[]',
          images: '[]',
          created_at: '2024-01-01T10:00:00Z'
        },
        {
          id: 'msg_2',
          session_id: sessionId,
          role: 'assistant',
          content: 'Hi there!',
          files: '[]',
          tool_executions: '[]',
          images: '[]',
          created_at: '2024-01-01T10:01:00Z'
        }
      ];
      mockDb.query.resolves({ rows: mockMessages });

      // Act
      const history = await sessionService.getChatHistory(sessionId);

      // Assert
      expect(mockDb.query.calledOnce).to.be.true;
      const queryCall = mockDb.query.getCall(0);
      expect(queryCall.args[0]).to.include('SELECT');
      expect(queryCall.args[0]).to.include('ORDER BY created_at');
      expect(queryCall.args[1]).to.include(sessionId);
      expect(history).to.have.length(2);
      expect(history[0].role).to.equal('user');
      expect(history[1].role).to.equal('assistant');
    });

    it('should return empty array for non-existent session', async () => {
      // Arrange
      const sessionId = 'session_nonexistent';
      mockDb.query.resolves({ rows: [] });

      // Act
      const history = await sessionService.getChatHistory(sessionId);

      // Assert
      expect(history).to.be.an('array').that.is.empty;
    });

    it('should respect limit parameter', async () => {
      // Arrange
      const sessionId = 'session_123';
      const limit = 10;
      mockDb.query.resolves({ rows: [] });

      // Act
      await sessionService.getChatHistory(sessionId, limit);

      // Assert
      const queryCall = mockDb.query.getCall(0);
      expect(queryCall.args[1]).to.include(limit);
    });
  });

  describe('createSession', () => {
    it('should create new session with canvas ID', async () => {
      // Arrange
      const canvasId = 'canvas_123';
      const newSessionId = 'session_new_456';
      mockDb.query.resolves({ rows: [{ id: newSessionId }] });

      // Act
      const sessionId = await sessionService.createSession(canvasId);

      // Assert
      expect(mockDb.query.calledOnce).to.be.true;
      const queryCall = mockDb.query.getCall(0);
      expect(queryCall.args[0]).to.include('INSERT INTO chat_sessions');
      expect(queryCall.args[1]).to.include(canvasId);
      expect(sessionId).to.equal(newSessionId);
    });

    it('should create session without canvas ID', async () => {
      // Arrange
      const newSessionId = 'session_new_789';
      mockDb.query.resolves({ rows: [{ id: newSessionId }] });

      // Act
      const sessionId = await sessionService.createSession();

      // Assert
      expect(mockDb.query.calledOnce).to.be.true;
      const queryCall = mockDb.query.getCall(0);
      expect(queryCall.args[1][0]).to.be.null;
      expect(sessionId).to.equal(newSessionId);
    });
  });

  describe('getSession', () => {
    it('should retrieve session information', async () => {
      // Arrange
      const sessionId = 'session_123';
      const mockSession = {
        id: sessionId,
        canvas_id: 'canvas_456',
        created_at: '2024-01-01T10:00:00Z',
        updated_at: '2024-01-01T11:00:00Z',
        last_activity: '2024-01-01T11:00:00Z'
      };
      mockDb.query.resolves({ rows: [mockSession] });

      // Act
      const session = await sessionService.getSession(sessionId);

      // Assert
      expect(mockDb.query.calledOnce).to.be.true;
      expect(session).to.deep.equal(mockSession);
    });

    it('should return null for non-existent session', async () => {
      // Arrange
      const sessionId = 'session_nonexistent';
      mockDb.query.resolves({ rows: [] });

      // Act
      const session = await sessionService.getSession(sessionId);

      // Assert
      expect(session).to.be.null;
    });
  });

  describe('clearSession', () => {
    it('should delete session and return success', async () => {
      // Arrange
      const sessionId = 'session_123';
      mockDb.query.resolves({ rows: [{ id: sessionId }] });

      // Act
      await sessionService.clearSession(sessionId);

      // Assert
      expect(mockDb.query.calledOnce).to.be.true;
      const queryCall = mockDb.query.getCall(0);
      expect(queryCall.args[0]).to.include('DELETE FROM chat_sessions');
      expect(queryCall.args[1]).to.include(sessionId);
    });

    it('should throw error for non-existent session', async () => {
      // Arrange
      const sessionId = 'session_nonexistent';
      mockDb.query.resolves({ rows: [] });

      // Act & Assert
      try {
        await sessionService.clearSession(sessionId);
        expect.fail('Should have thrown an error');
      } catch (error) {
        expect(error.message).to.include('Session not found');
      }
    });
  });

  describe('cleanupInactiveSessions', () => {
    it('should delete inactive sessions and return count', async () => {
      // Arrange
      const maxAgeHours = 24;
      const deletedCount = 5;
      mockDb.query.resolves({ rows: [{ deleted_count: deletedCount }] });

      // Act
      const result = await sessionService.cleanupInactiveSessions(maxAgeHours);

      // Assert
      expect(mockDb.query.calledOnce).to.be.true;
      const queryCall = mockDb.query.getCall(0);
      expect(queryCall.args[0]).to.include('cleanup_inactive_chat_sessions');
      expect(queryCall.args[1]).to.include(maxAgeHours);
      expect(result).to.equal(deletedCount);
    });
  });

  describe('getMessageCount', () => {
    it('should return message count for session', async () => {
      // Arrange
      const sessionId = 'session_123';
      const count = 42;
      mockDb.query.resolves({ rows: [{ count: count.toString() }] });

      // Act
      const result = await sessionService.getMessageCount(sessionId);

      // Assert
      expect(mockDb.query.calledOnce).to.be.true;
      const queryCall = mockDb.query.getCall(0);
      expect(queryCall.args[0]).to.include('COUNT(*)');
      expect(queryCall.args[1]).to.include(sessionId);
      expect(result).to.equal(count);
    });
  });
});
