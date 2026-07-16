import { apiClient } from '@/api/client'
import type { AuditLogEntry, SystemHealth, User, UserRole } from '@/types'

export async function listUsers(): Promise<User[]> {
  const response = await apiClient.get<User[]>('/users')
  return response.data
}

export interface CreateUserPayload {
  email: string
  password: string
  full_name: string
  role: UserRole
}

export async function createUser(payload: CreateUserPayload): Promise<User> {
  const response = await apiClient.post<User>('/users', payload)
  return response.data
}

export interface UpdateUserPayload {
  full_name?: string
  role?: UserRole
  is_active?: boolean
}

export async function updateUser(id: string, payload: UpdateUserPayload): Promise<User> {
  const response = await apiClient.patch<User>(`/users/${id}`, payload)
  return response.data
}

export async function fetchAuditLog(limit = 100): Promise<AuditLogEntry[]> {
  const response = await apiClient.get<AuditLogEntry[]>('/admin/audit', { params: { limit } })
  return response.data
}

export async function fetchSystemHealth(): Promise<SystemHealth> {
  const response = await apiClient.get<SystemHealth>('/admin/health')
  return response.data
}
