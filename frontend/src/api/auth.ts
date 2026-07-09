import { apiClient } from '@/api/client'
import type { User } from '@/types'

interface TokenResponse {
  access_token: string
  token_type: string
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  const body = new URLSearchParams()
  body.set('username', email)
  body.set('password', password)

  const response = await apiClient.post<TokenResponse>('/auth/login', body, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  return response.data
}

export async function fetchCurrentUser(): Promise<User> {
  const response = await apiClient.get<User>('/users/me')
  return response.data
}

export async function refresh(): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>('/auth/refresh')
  return response.data
}

export async function logout(): Promise<void> {
  await apiClient.post('/auth/logout')
}
