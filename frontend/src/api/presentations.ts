import { apiClient } from '@/api/client'
import type { PresentationItem } from '@/types'

interface CreatePresentationPayload {
  source_document_id?: string
  source_text?: string
  title?: string
  instructions?: string
}

export async function listPresentations(): Promise<PresentationItem[]> {
  const response = await apiClient.get<PresentationItem[]>('/presentations')
  return response.data
}

export async function getPresentation(id: string): Promise<PresentationItem> {
  const response = await apiClient.get<PresentationItem>(`/presentations/${id}`)
  return response.data
}

export async function createPresentation(payload: CreatePresentationPayload): Promise<PresentationItem> {
  const response = await apiClient.post<PresentationItem>('/presentations', payload)
  return response.data
}

export async function regeneratePresentation(id: string): Promise<PresentationItem> {
  const response = await apiClient.post<PresentationItem>(`/presentations/${id}/regenerate`)
  return response.data
}

export async function downloadPresentation(id: string, filename: string): Promise<void> {
  const response = await apiClient.get(`/presentations/${id}/download`, { responseType: 'blob' })
  const url = window.URL.createObjectURL(new Blob([response.data]))
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}
