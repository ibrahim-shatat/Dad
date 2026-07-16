import { apiClient } from '@/api/client'
import type { ApprovalItemType, ApprovalQueueItem, ApprovalStatus } from '@/types'

interface ListParams {
  status?: ApprovalStatus
  type?: ApprovalItemType
}

export async function listApprovals(params: ListParams = {}): Promise<ApprovalQueueItem[]> {
  const query: Record<string, string> = {}
  if (params.status) query.status_filter = params.status
  if (params.type) query.type_filter = params.type
  const response = await apiClient.get<ApprovalQueueItem[]>('/approvals', {
    params: Object.keys(query).length ? query : undefined,
  })
  return response.data
}

export async function approveItem(id: string, note?: string): Promise<ApprovalQueueItem> {
  const response = await apiClient.post<ApprovalQueueItem>(`/approvals/${id}/approve`, { note })
  return response.data
}

export async function rejectItem(id: string, reason: string): Promise<ApprovalQueueItem> {
  const response = await apiClient.post<ApprovalQueueItem>(`/approvals/${id}/reject`, { reason })
  return response.data
}
