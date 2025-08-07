const API_BASE = 'http://localhost:8000';

export interface GetResultsParams {
  stream_id?: string;
  limit?: number;
  alert_level?: string;
}

class ApiService {
  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`API request failed: ${response.statusText}`);
    }

    return response.json();
  }

  async getStreams() {
    return this.request<{ streams: any[]; total: number }>('/streams');
  }

  async createStream(config: any) {
    return this.request('/streams', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async startStream(streamId: string) {
    return this.request(`/streams/${streamId}/start`, {
      method: 'POST',
    });
  }

  async stopStream(streamId: string) {
    return this.request(`/streams/${streamId}/stop`, {
      method: 'POST',
    });
  }

  async deleteStream(streamId: string) {
    return this.request(`/streams/${streamId}`, {
      method: 'DELETE',
    });
  }

  async getAIModels() {
    return this.request<{ models: Record<string, any>; total: number }>('/ai-models');
  }

  async getResults(params: GetResultsParams = {}) {
    const searchParams = new URLSearchParams();
    if (params.stream_id) searchParams.append('stream_id', params.stream_id);
    if (params.limit) searchParams.append('limit', params.limit.toString());
    if (params.alert_level) searchParams.append('alert_level', params.alert_level);

    const query = searchParams.toString();
    return this.request<{ results: any[]; total: number; filters: any }>(`/results${query ? `?${query}` : ''}`);
  }

  async getDashboardStats() {
    return this.request<any>('/dashboard/stats');
  }

  async getHealth() {
    return this.request<{ status: string; timestamp: string }>('/health');
  }
}

export const api = new ApiService();