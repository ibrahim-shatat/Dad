import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Bell, BellRing } from 'lucide-react'

import { cn } from '@/lib/utils'
import type { Notification, NotificationType } from '@/types'

const TYPE_LABELS: Record<NotificationType, string> = {
  document_reviewed: 'Document reviewed',
  meeting_processed: 'Meeting processed',
  approval_pending: 'Approval pending',
  approval_approved: 'Approval approved',
  approval_rejected: 'Approval rejected',
  urgent_email: 'Urgent email',
}
import {
  fetchUnreadCount,
  listNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from '@/api/notifications'
import { disablePush, enablePush, isPushEnabled, pushSupported } from '@/lib/push'

function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const s = Math.round(diff / 1000)
  if (s < 60) return 'just now'
  const m = Math.round(s / 60)
  if (m < 60) return `${m}m ago`
  const h = Math.round(m / 60)
  if (h < 24) return `${h}h ago`
  const d = Math.round(h / 24)
  return `${d}d ago`
}

export default function NotificationBell() {
  const [open, setOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data: unread = 0 } = useQuery({
    queryKey: ['notifications', 'unread'],
    queryFn: fetchUnreadCount,
    refetchInterval: 30000,
  })

  const { data: notifications = [] } = useQuery({
    queryKey: ['notifications', 'list'],
    queryFn: listNotifications,
    enabled: open,
  })

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['notifications', 'unread'] })
    queryClient.invalidateQueries({ queryKey: ['notifications', 'list'] })
  }

  const readMutation = useMutation({ mutationFn: markNotificationRead, onSuccess: invalidate })
  const readAllMutation = useMutation({ mutationFn: markAllNotificationsRead, onSuccess: invalidate })

  const [pushOn, setPushOn] = useState(false)
  const [pushBusy, setPushBusy] = useState(false)
  const supported = pushSupported()

  useEffect(() => {
    if (open) isPushEnabled().then(setPushOn)
  }, [open])

  const togglePush = async () => {
    setPushBusy(true)
    try {
      if (pushOn) {
        await disablePush()
        setPushOn(false)
      } else {
        const result = await enablePush()
        if (result === 'enabled') setPushOn(true)
        else if (result === 'denied')
          alert('Notifications are blocked. Enable them for this site in your browser settings.')
      }
    } catch {
      alert('Could not update push notifications. Please try again.')
    } finally {
      setPushBusy(false)
    }
  }

  // Close on outside click.
  useEffect(() => {
    if (!open) return
    const onClick = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onClick)
    return () => document.removeEventListener('mousedown', onClick)
  }, [open])

  const handleClick = (n: Notification) => {
    if (!n.is_read) readMutation.mutate(n.id)
    setOpen(false)
    if (n.link) navigate(n.link)
  }

  return (
    <div className="relative" ref={containerRef}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-label="Notifications"
        className="relative rounded-md p-2 text-foreground hover:bg-muted"
      >
        <Bell className="size-5" />
        {unread > 0 && (
          <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-semibold text-white">
            {unread > 9 ? '9+' : unread}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 z-50 mt-2 w-80 max-w-[calc(100vw-1.5rem)] overflow-hidden rounded-xl border bg-card shadow-lg">
          <div className="flex items-center justify-between border-b px-4 py-2.5">
            <p className="text-sm font-semibold">Notifications</p>
            {notifications.some((n) => !n.is_read) && (
              <button
                type="button"
                onClick={() => readAllMutation.mutate()}
                className="text-xs font-medium text-primary hover:underline"
              >
                Mark all read
              </button>
            )}
          </div>

          <div className="max-h-96 overflow-y-auto">
            {notifications.length === 0 ? (
              <p className="px-4 py-8 text-center text-sm text-muted-foreground">
                No notifications yet.
              </p>
            ) : (
              notifications.map((n) => (
                <button
                  key={n.id}
                  type="button"
                  onClick={() => handleClick(n)}
                  className={cn(
                    'flex w-full flex-col gap-0.5 border-b px-4 py-3 text-left transition-colors last:border-b-0 hover:bg-muted/50',
                    !n.is_read && 'bg-primary/5'
                  )}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span
                      className={cn(
                        'text-[10px] font-bold uppercase tracking-wide',
                        !n.is_read ? 'text-primary' : 'text-muted-foreground'
                      )}
                    >
                      {TYPE_LABELS[n.type]}
                    </span>
                    <div className="flex items-center gap-2">
                      <span className="text-[11px] text-muted-foreground">
                        {relativeTime(n.created_at)}
                      </span>
                      {!n.is_read && <span className="size-2 flex-none rounded-full bg-primary" />}
                    </div>
                  </div>
                  <p className="text-sm font-semibold leading-tight">{n.title}</p>
                  {n.body && <p className="line-clamp-2 text-xs text-muted-foreground">{n.body}</p>}
                </button>
              ))
            )}
          </div>

          {supported && (
            <div className="border-t px-4 py-2.5">
              <button
                type="button"
                onClick={togglePush}
                disabled={pushBusy}
                className="flex w-full items-center justify-center gap-2 rounded-md py-1.5 text-xs font-medium text-primary hover:bg-muted disabled:opacity-60"
              >
                <BellRing className="size-3.5" />
                {pushBusy
                  ? 'Working…'
                  : pushOn
                    ? 'Phone push on — tap to turn off'
                    : 'Enable phone notifications'}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
