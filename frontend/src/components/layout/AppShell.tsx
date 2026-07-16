import { useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard,
  Sun,
  FileText,
  Presentation,
  Mail,
  CalendarCheck,
  CalendarClock,
  ClipboardCheck,
  Sparkles,
  ShieldCheck,
  LogOut,
  Menu,
  X,
} from 'lucide-react'

import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import NotificationBell from '@/components/NotificationBell'
import { useAuthStore } from '@/store/authStore'
import { logout as apiLogout } from '@/api/auth'

const NAV_ITEMS = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/briefing', label: 'Daily briefing', icon: Sun },
  { to: '/assistant', label: 'Assistant', icon: Sparkles },
  { to: '/documents', label: 'Documents', icon: FileText },
  { to: '/presentations', label: 'Presentations', icon: Presentation },
  { to: '/email', label: 'Email', icon: Mail },
  { to: '/meetings', label: 'Meetings', icon: CalendarCheck },
  { to: '/calendar', label: 'Calendar', icon: CalendarClock },
  { to: '/approvals', label: 'Approvals', icon: ClipboardCheck },
]

const ADMIN_NAV_ITEM = { to: '/admin', label: 'Admin', icon: ShieldCheck }

export default function AppShell() {
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)
  const clearSession = useAuthStore((s) => s.clearSession)
  const [open, setOpen] = useState(false)

  const navItems = user?.role === 'admin' ? [...NAV_ITEMS, ADMIN_NAV_ITEM] : NAV_ITEMS

  const handleLogout = async () => {
    try {
      await apiLogout()
    } finally {
      clearSession()
      navigate('/login', { replace: true })
    }
  }

  return (
    <div className="flex min-h-svh flex-col md:flex-row">
      {/* Mobile top bar */}
      <header className="sticky top-0 z-20 flex items-center gap-3 border-b bg-card px-4 py-2.5 md:hidden">
        <button
          type="button"
          onClick={() => setOpen(true)}
          aria-label="Open menu"
          className="-ml-1 rounded-md p-1 text-foreground hover:bg-muted"
        >
          <Menu className="size-5" />
        </button>
        <p className="text-sm font-semibold">AI Executive Assistant</p>
        <div className="ml-auto">
          <NotificationBell />
        </div>
      </header>

      {/* Backdrop (mobile, when drawer open) */}
      {open && (
        <div
          className="fixed inset-0 z-30 bg-black/40 md:hidden"
          onClick={() => setOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Sidebar: slide-in drawer on mobile, static on desktop */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-40 flex w-64 shrink-0 flex-col border-r bg-card transition-transform duration-200 md:static md:z-auto md:w-60 md:translate-x-0',
          open ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex items-center justify-between border-b p-4">
          <p className="text-sm font-semibold">AI Executive Assistant</p>
          <button
            type="button"
            onClick={() => setOpen(false)}
            aria-label="Close menu"
            className="rounded-md p-1 text-muted-foreground hover:bg-muted md:hidden"
          >
            <X className="size-5" />
          </button>
        </div>
        <nav className="flex flex-1 flex-col gap-1 overflow-y-auto p-2">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              onClick={() => setOpen(false)}
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

      <div className="flex min-w-0 flex-1 flex-col">
        {/* Desktop top bar (mobile has its own above) */}
        <header className="hidden items-center justify-end border-b bg-card px-6 py-2 md:flex">
          <NotificationBell />
        </header>
        <main className="min-w-0 flex-1 overflow-y-auto p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
