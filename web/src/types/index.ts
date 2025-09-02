// User types
export interface User {
  id: number
  email: string
  name?: string
  plan?: 'free' | 'team' | 'pro'
  tenant_id?: string
  role: string
  created_at: string
  updated_at?: string
}

// Document types
export interface Document {
  id: string
  name: string
  size: number
  status: 'parse_started' | 'parse_done' | 'failed'
  created_at: string
  updated_at?: string
  tenant_id?: string
  file_type?: string
  pages?: number
  chunks?: number
}

// Job types
export interface Job {
  id: string
  document_id: string
  status: 'queued' | 'running' | 'done' | 'failed'
  progress: number
  kind: 'ingest' | 'chunk' | 'embed' | 'index'
  created_at: string
  started_at?: string
  completed_at?: string
  error?: string
  tenant_id?: string
}

// Search types
export interface SearchQuery {
  question: string
  top_k?: number
  rerank?: boolean
  bm25?: boolean
  tenant_id?: string
}

export interface SearchResult {
  doc_id: string
  chunk_id: string
  page?: number
  score: number
  snippet: string
  breadcrumbs?: string[]
  source?: string
}

export interface SearchResponse {
  matches: SearchResult[]
  usage?: {
    in_tokens: number
    out_tokens: number
  }
}

// API Key types
export interface ApiKey {
  id: string
  name: string
  key: string
  created_at: string
  last_used?: string
  permissions?: string[]
}

// Usage types
export interface Usage {
  documents: {
    total: number
    limit: number
  }
  queries: {
    total: number
    limit: number
  }
  storage: {
    used: number
    limit: number
  }
}

// WebSocket types
export interface WebSocketMessage {
  event: string
  job_id?: string
  document_id?: string
  type?: string
  progress?: number
  tenant_id?: string
  ts: string
  error?: string
  metadata?: Record<string, any>
}

export interface WebSocketError {
  code: number
  reason: string
  timestamp: string
}

// Form types
export interface LoginForm {
  email: string
  password: string
}

export interface RegisterForm {
  name: string
  email: string
  password: string
  confirmPassword: string
}

export interface UploadForm {
  file: File
  description?: string
}
