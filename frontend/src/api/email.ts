import { apiClient } from '@/api/client'
import type { EmailAccount, EmailMessageItem } from '@/types'

export async function listEmailAccounts(): Promise<EmailAccount[]> {
  const response = await apiClient.get<EmailAccount[]>('/email/accounts')
  return response.data
}

export async function getGmailAuthorizationUrl(): Promise<string> {
  const response = await apiClient.get<{ authorization_url: string }>('/email/gmail/connect')
  return response.data.authorization_url
}

export async function getOutlookAuthorizationUrl(): Promise<string> {
  const response = await apiClient.get<{ authorization_url: string }>('/email/outlook/connect')
  return response.data.authorization_url
}

export async function syncAccount(accountId: string): Promise<void> {
  await apiClient.post(`/email/accounts/${accountId}/sync`)
}

export async function listEmailMessages(accountId?: string): Promise<EmailMessageItem[]> {
  const response = await apiClient.get<EmailMessageItem[]>('/email/messages', {
    params: accountId ? { account_id: accountId } : undefined,
  })
  return response.data
}

export async function getEmailMessage(id: string): Promise<EmailMessageItem> {
  const response = await apiClient.get<EmailMessageItem>(`/email/messages/${id}`)
  return response.data
}

export async function draftReply(messageId: string, instructions?: string): Promise<void> {
  await apiClient.post(`/email/messages/${messageId}/draft-reply`, { instructions })
}
