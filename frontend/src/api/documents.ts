import { apiClient } from '@/api/client'
import type { DocumentItem } from '@/types'

export async function listDocuments(): Promise<DocumentItem[]> {
  const response = await apiClient.get<DocumentItem[]>('/documents')
  return response.data
}

export async function getDocument(id: string): Promise<DocumentItem> {
  const response = await apiClient.get<DocumentItem>(`/documents/${id}`)
  return response.data
}

export async function uploadDocument(file: File, instructions?: string): Promise<DocumentItem> {
  const formData = new FormData()
  formData.append('file', file)
  if (instructions) formData.append('instructions', instructions)
  const response = await apiClient.post<DocumentItem>('/documents', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return response.data
}

export async function acknowledgeDisclaimer(id: string): Promise<DocumentItem> {
  const response = await apiClient.post<DocumentItem>(`/documents/${id}/review/ack`)
  return response.data
}
