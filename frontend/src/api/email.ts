import { apiClient } from '@/api/client'
import type { EmailAccount, EmailDraft, EmailMessageItem } from '@/types'

export interface EmailDraftUpdate {
  to_addresses?: string[]
  cc_addresses?: string[]
  subject?: string
  body?: string
}

export async function getEmailDraft(id: string): Promise<EmailDraft> {
  const response = await apiClient.get<EmailDraft>(`/email/drafts/${id}`)
  return response.data
}

export async function updateEmailDraft(id: string, patch: EmailDraftUpdate): Promise<EmailDraft> {
  const response = await apiClient.patch<EmailDraft>(`/email/drafts/${id}`, patch)
  return response.data
}

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

export async function disconnectAccount(accountId: string): Promise<void> {
  await apiClient.delete(`/email/accounts/${accountId}`)
}

export async function listEmailMessages(
  accountId?: string,
  includeHidden = false
): Promise<EmailMessageItem[]> {
  const params: Record<string, string | boolean> = {}
  if (accountId) params.account_id = accountId
  if (includeHidden) params.include_hidden = true
  const response = await apiClient.get<EmailMessageItem[]>('/email/messages', {
    params: Object.keys(params).length ? params : undefined,
  })
  return response.data
}

export async function hideMessage(messageId: string): Promise<void> {
  await apiClient.post(`/email/messages/${messageId}/hide`)
}

export async function unhideMessage(messageId: string): Promise<void> {
  await apiClient.post(`/email/messages/${messageId}/unhide`)
}

export async function getEmailMessage(id: string): Promise<EmailMessageItem> {
  const response = await apiClient.get<EmailMessageItem>(`/email/messages/${id}`)
  return response.data
}

export interface EmailMessageBody {
  sender: string
  subject: string
  body: string
}

export async function getEmailMessageBody(id: string): Promise<EmailMessageBody> {
  const response = await apiClient.get<EmailMessageBody>(`/email/messages/${id}/body`)
  return response.data
}

export async function draftReply(messageId: string, instructions?: string): Promise<void> {
  await apiClient.post(`/email/messages/${messageId}/draft-reply`, { instructions })
}
