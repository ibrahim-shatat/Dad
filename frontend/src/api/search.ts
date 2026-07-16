import { apiClient } from '@/api/client'
import type { ChatResponse, SearchResult } from '@/types'

export async function searchWorkspace(q: string): Promise<SearchResult[]> {
  const response = await apiClient.get<SearchResult[]>('/search', { params: { q } })
  return response.data
}

export async function askAssistant(question: string): Promise<ChatResponse> {
  const response = await apiClient.post<ChatResponse>('/search/chat', { question })
  return response.data
}
