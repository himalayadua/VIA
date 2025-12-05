/**
 * Chat Error Handler
 * 
 * Centralized error handling utility for chat operations.
 * Provides user-friendly error messages and determines retry-ability.
 */

export enum ChatErrorType {
  NETWORK = 'network',
  TIMEOUT = 'timeout',
  AUTH = 'authentication',
  FILE_UPLOAD = 'file_upload',
  FILE_SIZE = 'file_size',
  FILE_TYPE = 'file_type',
  TOOL_EXECUTION = 'tool_execution',
  SERVER = 'server',
  UNKNOWN = 'unknown'
}

export interface ChatError {
  type: ChatErrorType;
  message: string;
  originalError?: Error;
  retryable: boolean;
  details?: string;
}

export class ChatErrorHandler {
  /**
   * Handle any error and convert to ChatError
   */
  static handleError(error: unknown, context?: string): ChatError {
    // Network errors
    if (this.isNetworkError(error)) {
      return {
        type: ChatErrorType.NETWORK,
        message: 'Unable to connect to chat service. Please try again.',
        originalError: error instanceof Error ? error : undefined,
        retryable: true
      };
    }

    // Timeout errors
    if (this.isTimeoutError(error)) {
      return {
        type: ChatErrorType.TIMEOUT,
        message: 'Request timed out. Please try again.',
        originalError: error instanceof Error ? error : undefined,
        retryable: true
      };
    }

    // Authentication errors
    if (this.isAuthError(error)) {
      return {
        type: ChatErrorType.AUTH,
        message: 'Authentication failed. Please check your API key.',
        originalError: error instanceof Error ? error : undefined,
        retryable: false
      };
    }

    // Server errors
    if (this.isServerError(error)) {
      return {
        type: ChatErrorType.SERVER,
        message: 'Server error occurred. Please try again later.',
        originalError: error instanceof Error ? error : undefined,
        retryable: true
      };
    }

    // Extract error message if available
    let message = 'An unexpected error occurred.';
    if (error instanceof Error) {
      message = error.message || message;
    } else if (typeof error === 'string') {
      message = error;
    }

    // Add context if provided
    if (context) {
      message = `${context}: ${message}`;
    }

    return {
      type: ChatErrorType.UNKNOWN,
      message,
      originalError: error instanceof Error ? error : undefined,
      retryable: true
    };
  }

  /**
   * Format error message for display
   */
  static formatErrorMessage(error: ChatError): string {
    return error.message;
  }

  /**
   * Check if error is network-related
   */
  static isNetworkError(error: unknown): boolean {
    if (error instanceof Error) {
      const message = error.message.toLowerCase();
      return (
        message.includes('network') ||
        message.includes('fetch') ||
        message.includes('connection') ||
        message.includes('failed to fetch') ||
        error.name === 'NetworkError' ||
        error.name === 'TypeError' && message.includes('fetch')
      );
    }
    return false;
  }

  /**
   * Check if error is timeout
   */
  static isTimeoutError(error: unknown): boolean {
    if (error instanceof Error) {
      const message = error.message.toLowerCase();
      return (
        message.includes('timeout') ||
        message.includes('timed out') ||
        error.name === 'TimeoutError'
      );
    }
    return false;
  }

  /**
   * Check if error is authentication-related
   */
  static isAuthError(error: unknown): boolean {
    if (error instanceof Error) {
      const message = error.message.toLowerCase();
      return (
        message.includes('unauthorized') ||
        message.includes('authentication') ||
        message.includes('api key') ||
        message.includes('401')
      );
    }
    return false;
  }

  /**
   * Check if error is server error
   */
  static isServerError(error: unknown): boolean {
    if (error instanceof Error) {
      const message = error.message.toLowerCase();
      return (
        message.includes('500') ||
        message.includes('502') ||
        message.includes('503') ||
        message.includes('504') ||
        message.includes('server error') ||
        message.includes('internal server')
      );
    }
    return false;
  }

  /**
   * Create file upload error
   */
  static createFileUploadError(reason: string): ChatError {
    return {
      type: ChatErrorType.FILE_UPLOAD,
      message: `File upload failed: ${reason}`,
      retryable: false
    };
  }

  /**
   * Create file size error
   */
  static createFileSizeError(fileName: string, maxSizeMB: number): ChatError {
    return {
      type: ChatErrorType.FILE_SIZE,
      message: `File "${fileName}" is too large. Maximum size is ${maxSizeMB}MB.`,
      retryable: false,
      details: fileName
    };
  }

  /**
   * Create file type error
   */
  static createFileTypeError(fileName: string, allowedTypes: string): ChatError {
    return {
      type: ChatErrorType.FILE_TYPE,
      message: `File type not supported. Please upload ${allowedTypes}.`,
      retryable: false,
      details: fileName
    };
  }

  /**
   * Create tool execution error
   */
  static createToolExecutionError(toolName: string, reason?: string): ChatError {
    const message = reason
      ? `Tool execution failed: ${toolName} - ${reason}`
      : `Tool execution failed: ${toolName}`;

    return {
      type: ChatErrorType.TOOL_EXECUTION,
      message,
      retryable: false,
      details: toolName
    };
  }
}

/**
 * File validation utilities
 */
export const FILE_VALIDATION = {
  MAX_IMAGE_SIZE: 5 * 1024 * 1024, // 5MB
  MAX_PDF_SIZE: 10 * 1024 * 1024, // 10MB
  ALLOWED_IMAGE_TYPES: ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp'],
  ALLOWED_DOCUMENT_TYPES: ['application/pdf'],

  /**
   * Validate a single file
   */
  validateFile(file: File): { valid: boolean; error?: ChatError } {
    // Check file type
    const isImage = this.ALLOWED_IMAGE_TYPES.includes(file.type);
    const isDocument = this.ALLOWED_DOCUMENT_TYPES.includes(file.type);

    if (!isImage && !isDocument) {
      return {
        valid: false,
        error: ChatErrorHandler.createFileTypeError(
          file.name,
          'PNG, JPEG, GIF, WebP, or PDF files'
        )
      };
    }

    // Check file size
    const maxSize = isImage ? this.MAX_IMAGE_SIZE : this.MAX_PDF_SIZE;
    const maxSizeMB = maxSize / (1024 * 1024);

    if (file.size > maxSize) {
      return {
        valid: false,
        error: ChatErrorHandler.createFileSizeError(file.name, maxSizeMB)
      };
    }

    return { valid: true };
  },

  /**
   * Validate multiple files
   */
  validateFiles(files: File[]): { valid: boolean; error?: ChatError } {
    for (const file of files) {
      const result = this.validateFile(file);
      if (!result.valid) {
        return result;
      }
    }
    return { valid: true };
  },

  /**
   * Get human-readable file size
   */
  formatFileSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }
};
