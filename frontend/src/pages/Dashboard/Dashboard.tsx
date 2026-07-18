import { useQuery } from '@tanstack/react-query'
import { Link, useNavigate } from 'react-router-dom'
import {
  ArrowRight,
  Calendar,
  FileText,
  ListChecks,
  Mail,
  Presentation,
  Send,
  Sparkles,
} from 'lucide-react'

import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import ApprovalQueueList from '@/components/ApprovalQueue/ApprovalQueueList'
import { fetchDashboard } from '@/api/dashboard'
import { useAuthStore } from '@/store/authStore'
import type { AttentionItem } from '@/types'

const TONE_STYLE: Record<AttentionItem['tone'], string> = {
  urgent: 'bg-red-500/10 text-red-600 dark:text-red-400',
  warning: 'bg-amber-500/10 text-amber-600 dark:text-amber-500',
  default: 'bg-primary/10 text-primary',
}

const KIND_ICON: Record<AttentionItem['kind'], typeof Mail> = {
  email: Mail,
  approval: Send,
  deadline: ListChecks,
  event: Calendar,
  task: ListChecks,
  document: FileText,
  presentation: Presentation,
}

function formatWhen(iso: string): string {
  const d = new Date(iso)
  const sameDay = d.toDateString() === new Date().toDateString()
  return sameDay
    ? d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : d.toLocaleDateString([], { month: 'short', day: 'numeric' })
}

const STAT_CARDS = [
  { key: 'documents_awaiting_review', label: 'Documents awaiting review', icon: FileText, to: '/documents', urgent: false },
  { key: 'presentations_in_progress', label: 'Presentations in progress', icon: Presentation, to: '/presentations', urgent: false },
  { key: 'open_action_items', label: 'Open action items', icon: ListChecks, to: '/meetings', urgent: false },
  { key: 'unread_urgent_emails', label: 'Unread urgent emails', icon: Mail, to: '/email', urgent: true },
] as const

function greeting(): string {
  const h = new Date().getHours()
  if (h < 12) return 'Good morning'
  if (h < 18) return 'Good afternoon'
  return 'Good evening'
}

export default function Dashboard() {
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)
  const { data } = useQuery({ queryKey: ['dashboard'], queryFn: fetchDashboard })

  const firstName = user?.full_name?.split(' ')[0] ?? 'there'
  const today = new Date().toLocaleDateString(undefined, {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
  })

  const attentionItems = data?.needs_attention ?? []
  const workItems = data?.needs_work ?? []

  return (
    <div className="flex flex-col gap-6">
      {/* Greeting */}
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">
          {greeting()}, {firstName}.
        </h1>
        <p className="text-sm text-muted-foreground">Here's your executive summary for {today}.</p>
      </div>

      {/* What needs your attention — one ranked feed across emails, approvals, deadlines, meetings */}
      <Card className="border-primary/20 bg-primary/5">
        <CardContent className="flex flex-col gap-4 p-5 sm:p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-primary">
              <Sparkles className="size-5" />
              <span className="text-lg font-semibold">What needs your attention</span>
            </div>
            <span className="rounded-full bg-primary/10 px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wide text-primary">
              AI
            </span>
          </div>

          {attentionItems.length === 0 ? (
            <p className="text-sm leading-relaxed text-foreground/90">
              {data
                ? "You're all caught up. Nothing is pressing right now."
                : 'Gathering your priorities…'}
            </p>
          ) : (
            <>
              <p className="text-sm leading-relaxed text-foreground/90">
                {attentionItems.length} thing{attentionItems.length > 1 ? 's' : ''} may need you
                today — ranked by urgency.
              </p>
              <div className="flex flex-col gap-2">
                {attentionItems.map((item, i) => (
                  <AttentionRow key={i} item={item} onClick={() => navigate(item.link)} />
                ))}
              </div>
            </>
          )}

          <Button className="self-start" onClick={() => navigate('/briefing')}>
            Open full briefing <ArrowRight className="size-4" />
          </Button>
        </CardContent>
      </Card>

      {/* What needs work — the director's own in-progress queue */}
      {workItems.length > 0 && (
        <Card>
          <CardContent className="flex flex-col gap-3 p-5">
            <div className="flex items-center gap-2">
              <ListChecks className="size-5 text-primary" />
              <span className="text-base font-semibold">What needs work</span>
            </div>
            <p className="text-sm text-muted-foreground">
              Tasks, documents, and presentations in progress.
            </p>
            <div className="flex flex-col gap-2">
              {workItems.map((item, i) => (
                <AttentionRow key={i} item={item} onClick={() => navigate(item.link)} />
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Stat cards */}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {STAT_CARDS.map(({ key, label, icon: Icon, to, urgent }) => {
          const value = data?.[key] ?? 0
          const hot = urgent && value > 0
          return (
            <Link key={key} to={to}>
              <Card className="h-full transition-colors hover:bg-muted/40">
                <CardContent className="flex flex-col gap-3 p-4">
                  <div
                    className={cn(
                      'flex size-9 items-center justify-center rounded-lg',
                      hot ? 'bg-red-500/10 text-red-500' : 'bg-primary/10 text-primary'
                    )}
                  >
                    <Icon className="size-5" />
                  </div>
                  <div>
                    <p className={cn('text-2xl font-semibold', hot && 'text-red-500')}>
                      {data ? value : '—'}
                    </p>
                    <p className="text-xs text-muted-foreground">{label}</p>
                  </div>
                </CardContent>
              </Card>
            </Link>
          )
        })}
      </div>

      {/* Approvals + deadlines */}
      <div className="grid gap-6 lg:grid-cols-2">
        <section className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold">Pending approvals</h2>
            <Link to="/approvals" className="text-xs font-medium text-primary hover:underline">
              View all
            </Link>
          </div>
          <ApprovalQueueList limit={4} compact />
        </section>

        <section className="flex flex-col gap-3">
          <h2 className="text-base font-semibold">Upcoming deadlines</h2>
          {!data || data.upcoming_deadlines.length === 0 ? (
            <p className="text-sm text-muted-foreground">Nothing due soon.</p>
          ) : (
            <div className="flex flex-col gap-2">
              {data.upcoming_deadlines.map((d) => (
                <Link key={d.id} to={`/meetings/${d.meeting_id}`}>
                  <Card className="transition-colors hover:bg-muted/40">
                    <CardContent className="flex items-center justify-between gap-3 p-3.5 text-sm">
                      <div className="min-w-0">
                        <p className="truncate">{d.description}</p>
                        <p className="truncate text-xs text-muted-foreground">
                          {d.owner} · {d.meeting_title} ·{' '}
                          {d.type === 'decision' ? 'decision' : 'action item'}
                        </p>
                      </div>
                      <p className="flex-none text-xs font-medium text-muted-foreground">
                        {d.due_date}
                      </p>
                    </CardContent>
                  </Card>
                </Link>
              ))}
            </div>
          )}
        </section>
      </div>

      {/* Ask the assistant */}
      <Card>
        <CardContent className="flex flex-col gap-3 p-5">
          <div className="flex items-center gap-2">
            <Sparkles className="size-4 text-primary" />
            <h2 className="text-base font-semibold">Ask Dad anything</h2>
          </div>
          <p className="text-sm text-muted-foreground">
            "What needs my approval today?" · "Summarize my open action items"
          </p>
          <button
            type="button"
            onClick={() => navigate('/assistant')}
            className="flex items-center justify-between gap-2 rounded-md border border-input bg-muted/40 px-3.5 py-2.5 text-left text-sm text-muted-foreground transition-colors hover:border-primary"
          >
            Message Dad…
            <Send className="size-4 flex-none text-primary" />
          </button>
        </CardContent>
      </Card>
    </div>
  )
}

function AttentionRow({ item, onClick }: { item: AttentionItem; onClick: () => void }) {
  const Icon = KIND_ICON[item.kind]
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex items-center gap-3 rounded-lg bg-background/70 px-3 py-2.5 text-left transition-colors hover:bg-background"
    >
      <span
        className={cn(
          'flex size-8 flex-none items-center justify-center rounded-lg',
          TONE_STYLE[item.tone]
        )}
      >
        <Icon className="size-4" />
      </span>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium">{item.title}</p>
        <p className="truncate text-xs text-muted-foreground">{item.subtitle}</p>
      </div>
      <div className="flex flex-none flex-col items-end gap-1">
        <span
          className={cn(
            'rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide',
            TONE_STYLE[item.tone]
          )}
        >
          {item.badge}
        </span>
        {item.when && (
          <span className="text-[10px] text-muted-foreground">{formatWhen(item.when)}</span>
        )}
      </div>
    </button>
  )
}
