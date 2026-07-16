import { useQuery } from '@tanstack/react-query'
import { Link, useNavigate } from 'react-router-dom'
import {
  ArrowRight,
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

  const pending = data?.pending_approvals.length ?? 0
  const urgentEmails = data?.unread_urgent_emails ?? 0
  const deadlines = data?.upcoming_deadlines.length ?? 0
  const attention = pending + urgentEmails + deadlines

  return (
    <div className="flex flex-col gap-6">
      {/* Greeting */}
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">
          {greeting()}, {firstName}.
        </h1>
        <p className="text-sm text-muted-foreground">Here's your executive summary for {today}.</p>
      </div>

      {/* Daily briefing hero */}
      <Card className="border-primary/20 bg-primary/5">
        <CardContent className="flex flex-col gap-4 p-5 sm:p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-primary">
              <Sparkles className="size-5" />
              <span className="text-lg font-semibold">Daily briefing</span>
            </div>
            <span className="rounded-full bg-primary/10 px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wide text-primary">
              AI
            </span>
          </div>
          <p className="text-sm leading-relaxed text-foreground/90">
            {attention > 0
              ? `You have ${attention} item${attention > 1 ? 's' : ''} that may need your attention today — across approvals, deadlines, and urgent email.`
              : "You're all caught up. Nothing is pressing right now."}
          </p>
          {urgentEmails > 0 && (
            <div className="flex items-start gap-2 rounded-lg bg-background/70 px-3 py-2.5">
              <span className="mt-1 size-2 flex-none rounded-full bg-red-500" />
              <p className="text-sm">
                <span className="font-medium">
                  {urgentEmails} urgent email{urgentEmails > 1 ? 's' : ''}
                </span>{' '}
                <span className="text-muted-foreground">flagged and unread.</span>
              </p>
            </div>
          )}
          <Button className="self-start" onClick={() => navigate('/briefing')}>
            Open briefing <ArrowRight className="size-4" />
          </Button>
        </CardContent>
      </Card>

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
