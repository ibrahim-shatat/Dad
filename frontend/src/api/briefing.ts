import { apiClient } from '@/api/client'
import type { Briefing } from '@/types'

export async function fetchTodayBriefing(): Promise<Briefing> {
  const response = await apiClient.get<Briefing>('/briefing/today')
  return response.data
}

export async function generateBriefing(): Promise<Briefing> {
  const response = await apiClient.post<Briefing>('/briefing/generate')
  return response.data
}

export async function toggleBriefingItem(key: string, handled: boolean): Promise<Briefing> {
  const response = await apiClient.post<Briefing>('/briefing/items/toggle', { key, handled })
  return response.data
}
