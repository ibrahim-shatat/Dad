import { apiClient } from '@/api/client'

export async function getVapidPublicKey(): Promise<string> {
  const res = await apiClient.get<{ key: string }>('/push/vapid-public-key')
  return res.data.key
}

export async function subscribePush(subscription: PushSubscriptionJSON): Promise<void> {
  await apiClient.post('/push/subscribe', subscription)
}

export async function unsubscribePush(endpoint: string): Promise<void> {
  await apiClient.post('/push/unsubscribe', { endpoint })
}
