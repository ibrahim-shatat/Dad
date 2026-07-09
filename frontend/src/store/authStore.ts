import { create } from 'zustand'

import type { User } from '@/types'

interface AuthState {
  accessToken: string | null
  user: User | null
  isBootstrapping: boolean
  setSession: (accessToken: string, user: User) => void
  setAccessToken: (accessToken: string | null) => void
  clearSession: () => void
  setBootstrapping: (value: boolean) => void
}

// accessToken deliberately lives only in memory (not localStorage) since this app
// handles company email/document content — refresh happens via an httpOnly cookie.
export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  user: null,
  isBootstrapping: true,
  setSession: (accessToken, user) => set({ accessToken, user }),
  setAccessToken: (accessToken) => set({ accessToken }),
  clearSession: () => set({ accessToken: null, user: null }),
  setBootstrapping: (value) => set({ isBootstrapping: value }),
}))
