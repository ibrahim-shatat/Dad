import { apiClient } from '@/api/client'
import type { CalendarEvent } from '@/types'

export async function listCalendarEvents(includePast = false): Promise<CalendarEvent[]> {
  const response = await apiClient.get<CalendarEvent[]>('/calendar/events', {
    params: includePast ? { include_past: true } : undefined,
  })
  return response.data
}

export async function getCalendarEvent(id: string): Promise<CalendarEvent> {
  const response = await apiClient.get<CalendarEvent>(`/calendar/events/${id}`)
  return response.data
}

export async function syncCalendars(): Promise<{ accounts: number }> {
  const response = await apiClient.post<{ accounts: number }>('/calendar/sync')
  return response.data
}

export async function generateEventPrep(id: string): Promise<void> {
  await apiClient.post(`/calendar/events/${id}/prep`)
}

export async function draftEventFollowUp(id: string): Promise<void> {
  await apiClient.post(`/calendar/events/${id}/follow-up`)
}
