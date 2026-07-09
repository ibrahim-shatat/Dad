import { apiClient } from '@/api/client'
import type { ApprovalQueueItem, ApprovalStatus } from '@/types'

export async function listApprovals(statusFilter?: ApprovalStatus): Promise<ApprovalQueueItem[]> {
  const response = await apiClient.get<ApprovalQueueItem[]>('/approvals', {
    params: statusFilter ? { status_filter: statusFilter } : undefined,
  })
  return response.data
}

export async function approveItem(id: string): Promise<ApprovalQueueItem> {
  const response = await apiClient.post<ApprovalQueueItem>(`/approvals/${id}/approve`)
  return response.data
}

export async function rejectItem(id: string): Promise<ApprovalQueueItem> {
  const response = await apiClient.post<ApprovalQueueItem>(`/approvals/${id}/reject`)
  return response.data
}
