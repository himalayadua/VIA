// API Client for Via Canvas Backend
// Replaces Supabase client with REST API calls

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:3000';

interface ApiError {
  error: string;
  message?: string;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const config: RequestInit = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const error: ApiError = await response.json();
        throw new Error(error.message || error.error || 'API request failed');
      }

      return await response.json();
    } catch (error) {
      console.error(`API Error [${endpoint}]:`, error);
      throw error;
    }
  }

  // Canvas endpoints
  async getCanvases() {
    return this.request<any[]>('/api/canvases');
  }

  async getCanvas(id: string) {
    return this.request<any>(`/api/canvases/${id}`);
  }

  async createCanvas(data: { name: string; description?: string }) {
    return this.request<any>('/api/canvases', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateCanvas(id: string, data: { name?: string; description?: string }) {
    return this.request<any>(`/api/canvases/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteCanvas(id: string) {
    return this.request<any>(`/api/canvases/${id}`, {
      method: 'DELETE',
    });
  }

  // Node endpoints
  async getNodes(canvasId: string) {
    return this.request<any[]>(`/api/nodes?canvas_id=${canvasId}`);
  }

  async getNode(id: string) {
    return this.request<any>(`/api/nodes/${id}`);
  }

  async createNode(data: {
    canvas_id: string;
    parent_id?: string | null;
    title?: string;
    content?: string;
    card_type?: string;
    card_data?: any;
    tags?: string[];
    position_x?: number;
    position_y?: number;
    width?: number;
    height?: number;
    type?: string;
    style?: any;
  }) {
    return this.request<any>('/api/nodes', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateNode(id: string, data: {
    title?: string;
    content?: string;
    card_type?: string;
    card_data?: any;
    tags?: string[];
    position_x?: number;
    position_y?: number;
    width?: number;
    height?: number;
    parent_id?: string | null;
    style?: any;
  }) {
    return this.request<any>(`/api/nodes/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteNode(id: string) {
    return this.request<any>(`/api/nodes/${id}`, {
      method: 'DELETE',
    });
  }

  async batchUpdateNodes(updates: Array<{
    id: string;
    position_x: number;
    position_y: number;
  }>) {
    return this.request<any[]>('/api/nodes/batch', {
      method: 'POST',
      body: JSON.stringify({ updates }),
    });
  }

  // Connection endpoints
  async getConnections(canvasId: string) {
    return this.request<any[]>(`/api/connections?canvas_id=${canvasId}`);
  }

  async createConnection(data: {
    canvas_id: string;
    source_id: string;
    target_id: string;
    type?: string;
    animated?: boolean;
    style?: any;
  }) {
    return this.request<any>('/api/connections', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async deleteConnection(id: string) {
    return this.request<any>(`/api/connections/${id}`, {
      method: 'DELETE',
    });
  }

  // Snapshot endpoints
  async getSnapshots(canvasId: string) {
    return this.request<any[]>(`/api/snapshots?canvas_id=${canvasId}`);
  }

  async createSnapshot(data: {
    canvas_id: string;
    snapshot_data: {
      nodes: any[];
      edges: any[];
      viewport: any;
      metadata?: any;
    };
  }) {
    return this.request<any>('/api/snapshots', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async deleteSnapshot(id: string) {
    return this.request<any>(`/api/snapshots/${id}`, {
      method: 'DELETE',
    });
  }

  // Health check
  async healthCheck() {
    return this.request<{ status: string; database: string }>('/health');
  }

  // Merge cards
  async mergeCards(sourceCardId: string, targetCardId: string) {
    return this.request<any>('/api/nodes/merge', {
      method: 'POST',
      body: JSON.stringify({
        source_card_id: sourceCardId,
        target_card_id: targetCardId
      }),
    });
  }

  // Learning Actions
  async executeLearningAction(
    action: string,
    cardId: string,
    params: { canvas_id: string; create_card_option?: boolean; [key: string]: any }
  ) {
    const endpoints: Record<string, string> = {
      'find-gaps': `/api/ai/cards/${cardId}/find-gaps`,
      'simplify': `/api/ai/cards/${cardId}/simplify`,
      'go-deeper': `/api/ai/cards/${cardId}/go-deeper`,
      'find-examples': `/api/ai/cards/${cardId}/find-examples`,
      'challenge': `/api/ai/cards/${cardId}/challenge`,
      'connect-dots': `/api/ai/cards/${cardId}/connect-dots`,
      'update': `/api/ai/cards/${cardId}/update`,
      'action-plan': `/api/ai/cards/${cardId}/action-plan`
    };

    const endpoint = endpoints[action];
    if (!endpoint) {
      throw new Error(`Unknown learning action: ${action}`);
    }

    return this.request<any>(endpoint, {
      method: 'POST',
      body: JSON.stringify(params)
    });
  }
}

export const api = new ApiClient(API_BASE_URL);
export default api;
