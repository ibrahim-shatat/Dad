import { useEffect } from 'react'
import type { ReactNode } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'

import AppShell from '@/components/layout/AppShell'
import InstallPrompt from '@/components/InstallPrompt'
import Login from '@/pages/Auth/Login'
import Dashboard from '@/pages/Dashboard/Dashboard'
import Briefing from '@/pages/Briefing/Briefing'
import Calendar from '@/pages/Calendar/Calendar'
import Assistant from '@/pages/Assistant/Assistant'
import Admin from '@/pages/Admin/Admin'
import Documents from '@/pages/Documents/Documents'
import DocumentDetail from '@/pages/Documents/DocumentDetail'
import Presentations from '@/pages/Presentations/Presentations'
import PresentationDetail from '@/pages/Presentations/PresentationDetail'
import Email from '@/pages/Email/Email'
import Meetings from '@/pages/Meetings/Meetings'
import MeetingDetail from '@/pages/Meetings/MeetingDetail'
import Approvals from '@/pages/Approvals/Approvals'
import { useAuthStore } from '@/store/authStore'
import { fetchCurrentUser, refresh } from '@/api/auth'

function ProtectedRoute({ children }: { children: ReactNode }) {
  const user = useAuthStore((s) => s.user)
  const isBootstrapping = useAuthStore((s) => s.isBootstrapping)

  if (isBootstrapping) {
    return (
      <div className="flex min-h-svh items-center justify-center text-sm text-muted-foreground">
        Loading…
      </div>
    )
  }
  if (!user) {
    return <Navigate to="/login" replace />
  }
  return <>{children}</>
}

export default function App() {
  const setSession = useAuthStore((s) => s.setSession)
  const setAccessToken = useAuthStore((s) => s.setAccessToken)
  const setBootstrapping = useAuthStore((s) => s.setBootstrapping)

  useEffect(() => {
    let cancelled = false

    async function bootstrap() {
      try {
        const { access_token } = await refresh()
        if (cancelled) return
        setAccessToken(access_token)
        const user = await fetchCurrentUser()
        if (cancelled) return
        setSession(access_token, user)
      } catch {
        // No valid refresh cookie — user needs to log in.
      } finally {
        if (!cancelled) setBootstrapping(false)
      }
    }

    bootstrap()
    return () => {
      cancelled = true
    }
  }, [setSession, setAccessToken, setBootstrapping])

  return (
    <>
      <InstallPrompt />
      <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route
        element={
          <ProtectedRoute>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/briefing" element={<Briefing />} />
        <Route path="/documents" element={<Documents />} />
        <Route path="/documents/:id" element={<DocumentDetail />} />
        <Route path="/presentations" element={<Presentations />} />
        <Route path="/presentations/:id" element={<PresentationDetail />} />
        <Route path="/email" element={<Email />} />
        <Route path="/meetings" element={<Meetings />} />
        <Route path="/meetings/:id" element={<MeetingDetail />} />
        <Route path="/calendar" element={<Calendar />} />
        <Route path="/assistant" element={<Assistant />} />
        <Route path="/admin" element={<Admin />} />
        <Route path="/approvals" element={<Approvals />} />
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </>
  )
}
