import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard,
  FileText,
  Presentation,
  Mail,
  CalendarCheck,
  ClipboardCheck,
  LogOut,
} from 'lucide-react'

import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { useAuthStore } from '@/store/authStore'
import { logout as apiLogout } from '@/api/auth'

const NAV_ITEMS = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/documents', label: 'Documents', icon: FileText },
  { to: '/presentations', label: 'Presentations', icon: Presentation },
  { to: '/email', label: 'Email', icon: Mail },
  { to: '/meetings', label: 'Meetings', icon: CalendarCheck },
  { to: '/approvals', label: 'Approvals', icon: ClipboardCheck },
]

export default function AppShell() {
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)
  const clearSession = useAuthStore((s) => s.clearSession)

  const handleLogout = async () => {
    try {
      await apiLogout()
    } finally {
      clearSession()
      navigate('/login', { replace: true })
    }
  }

  return (
    <div className="flex min-h-svh">
      <aside className="flex w-60 shrink-0 flex-col border-r bg-card">
        <div className="border-b p-4">
          <p className="text-sm font-semibold">AI Executive Assistant</p>
        </div>
        <nav className="flex flex-1 flex-col gap-1 p-2">
          {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'text-foreground hover:bg-muted'
                )
              }
            >
              <Icon className="size-4" />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t p-3">
          <p className="truncate px-1 text-xs text-muted-foreground">{user?.full_name}</p>
          <p className="truncate px-1 text-xs text-muted-foreground capitalize">{user?.role}</p>
          <Button
            variant="ghost"
            size="sm"
            className="mt-1 w-full justify-start"
            onClick={handleLogout}
          >
            <LogOut className="size-4" />
            Log out
          </Button>
        </div>
      </aside>
      <main className="flex-1 overflow-y-auto p-6">
        <Outlet />
      </main>
    </div>
  )
}
