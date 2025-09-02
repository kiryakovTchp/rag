import { 
  User, 
  Document, 
  Job, 
  SearchQuery, 
  SearchResponse, 
  ApiKey, 
  Usage,
 
} from '@/types'

// Export apiClient for use in other services
export { apiClient } from './apiClient'

class ApiService {
  private baseUrl: string
  private token: string | null

  constructor() {
    this.baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    this.token = localStorage.getItem('auth_token')
  }

  private getHeaders(): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    }

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`
    }

    return headers
  }

  private async request<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`
    const response = await fetch(url, {
      ...options,
      headers: this.getHeaders(),
    })

    if (!response.ok) {
      if (response.status === 401) {
        // Token expired, clear it
        localStorage.removeItem('auth_token')
        localStorage.removeItem('user_data')
        throw new Error('Unauthorized')
      }
      throw new Error(`API Error: ${response.status}`)
    }

    return response.json()
  }

  // Auth methods
  async login(email: string, password: string): Promise<{ user: User; token: string }> {
    const response = await this.request<{ user: User; token: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
    
    this.token = response.token
    localStorage.setItem('auth_token', response.token)
    return response
  }

  async register(name: string, email: string, password: string): Promise<{ user: User; token: string }> {
    const response = await this.request<{ user: User; token: string }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ name, email, password }),
    })
    
    this.token = response.token
    localStorage.setItem('auth_token', response.token)
    return response
  }

  async getProfile(): Promise<User> {
    return this.request<User>('/auth/profile')
  }

  async updateProfile(data: Partial<User>): Promise<User> {
    return this.request<User>('/auth/profile', {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  // Document methods
  async getDocuments(): Promise<Document[]> {
    return this.request<Document[]>('/documents')
  }

  async uploadDocument(formData: FormData): Promise<{ document: Document; job: Job }> {
    const url = `${this.baseUrl}/ingest`
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
      },
      body: formData,
    })

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.status}`)
    }

    return response.json()
  }

  async getDocument(id: string): Promise<Document> {
    return this.request<Document>(`/documents/${id}`)
  }

  // Job methods
  async getJobs(): Promise<Job[]> {
    return this.request<Job[]>('/jobs')
  }

  async getJob(id: string): Promise<Job> {
    return this.request<Job>(`/jobs/${id}`)
  }

  // Search methods
  async search(query: SearchQuery): Promise<SearchResponse> {
    return this.request<SearchResponse>('/query', {
      method: 'POST',
      body: JSON.stringify(query),
    })
  }

  // API Key methods
  async getApiKeys(): Promise<ApiKey[]> {
    return this.request<ApiKey[]>('/keys')
  }

  async createApiKey(name: string): Promise<ApiKey> {
    return this.request<ApiKey>('/keys', {
      method: 'POST',
      body: JSON.stringify({ name }),
    })
  }

  async revokeApiKey(id: string): Promise<void> {
    await this.request(`/keys/${id}`, {
      method: 'DELETE',
    })
  }

  // Usage methods
  async getUsage(): Promise<Usage> {
    return this.request<Usage>('/usage')
  }

  // Health check
  async healthCheck(): Promise<{ status: string }> {
    return this.request<{ status: string }>('/healthz')
  }

  // Update token (called from AuthContext)
  updateToken(token: string) {
    this.token = token
  }

  // Clear token (called on logout)
  clearToken() {
    this.token = null
  }
}

export const apiService = new ApiService()
