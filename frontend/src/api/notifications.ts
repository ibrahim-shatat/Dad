import { apiClient } from '@/api/client'
import type { Notification } from '@/types'

export async function listNotifications(): Promise<Notification[]> {
  const response = await apiClient.get<Notification[]>('/notifications')
  return response.data
}

export async function fetchUnreadCount(): Promise<number> {
  const response = await apiClient.get<{ count: number }>('/notifications/unread-count')
  return response.data.count
}

export async function markNotificationRead(id: string): Promise<void> {
  await apiClient.post(`/notifications/${id}/read`)
}

export async function markAllNotificationsRead(): Promise<void> {
  await apiClient.post('/notifications/read-all')
}
