import { apiClient } from '@/api/client'
import type { ActionItemStatus, DecisionStatus, MeetingItem } from '@/types'

interface CreateMeetingPayload {
  title: string
  source_text: string
  meeting_date?: string
  instructions?: string
}

export async function listMeetings(): Promise<MeetingItem[]> {
  const response = await apiClient.get<MeetingItem[]>('/meetings')
  return response.data
}

export async function getMeeting(id: string): Promise<MeetingItem> {
  const response = await apiClient.get<MeetingItem>(`/meetings/${id}`)
  return response.data
}

export async function createMeeting(payload: CreateMeetingPayload): Promise<MeetingItem> {
  const response = await apiClient.post<MeetingItem>('/meetings', payload)
  return response.data
}

export async function regenerateMeeting(id: string): Promise<MeetingItem> {
  const response = await apiClient.post<MeetingItem>(`/meetings/${id}/regenerate`)
  return response.data
}

export async function updateActionItemStatus(
  meetingId: string,
  itemId: string,
  status: ActionItemStatus
): Promise<MeetingItem> {
  const response = await apiClient.patch<MeetingItem>(
    `/meetings/${meetingId}/action-items/${itemId}`,
    { status }
  )
  return response.data
}

export async function updateDecisionStatus(
  meetingId: string,
  decisionId: string,
  status: DecisionStatus
): Promise<MeetingItem> {
  const response = await apiClient.patch<MeetingItem>(
    `/meetings/${meetingId}/decisions/${decisionId}`,
    { status }
  )
  return response.data
}
