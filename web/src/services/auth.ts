import { apiClient } from './api'
import { User } from '@/types'

export type { User }

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
}

/**
 * Register a new user
 */
export async function register(data: RegisterRequest): Promise<User> {
  const response = await apiClient.post<User>('/auth/register', data)
  return response.data
}

/**
 * Login user and get access token
 */
export async function login(data: LoginRequest): Promise<LoginResponse> {
  const response = await apiClient.post<LoginResponse>('/auth/login', data)
  return response.data
}

/**
 * Get current user information
 */
export async function getMe(): Promise<User> {
  const response = await apiClient.get<User>('/auth/me')
  return response.data
}
