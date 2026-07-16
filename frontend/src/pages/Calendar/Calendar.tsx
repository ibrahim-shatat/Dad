import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { CalendarClock, MapPin, RefreshCw, Sparkles, Send, Users } from 'lucide-react'

import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { listEmailAccounts } from '@/api/email'
import {
  draftEventFollowUp,
  generateEventPrep,
  listCalendarEvents,
  syncCalendars,
} from '@/api/calendar'
import type { CalendarEvent } from '@/types'

function dayKey(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    weekday: 'long',
    month: 'short',
    day: 'numeric',
  })
}

function timeLabel(event: CalendarEvent): string {
  if (event.is_all_day) return 'All day'
  const start = new Date(event.start_time).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  })
  if (!event.end_time) return start
  const end = new Date(event.end_time).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  })
  return `${start} – ${end}`
}

export default function Calendar() {
  const queryClient = useQueryClient()
  const [pendingPrep, setPendingPrep] = useState<Set<string>>(new Set())
  const [followedUp, setFollowedUp] = useState<Set<string>>(new Set())

  const { data: accounts } = useQuery({
    queryKey: ['email', 'accounts'],
    queryFn: listEmailAccounts,
  })

  const { data: events, isLoading } = useQuery({
    queryKey: ['calendar', 'events'],
    queryFn: () => listCalendarEvents(true),
    // Poll while a prep brief is still being written so it appears when ready.
    refetchInterval: pendingPrep.size > 0 ? 4000 : false,
  })

  // Clear pending flags once the brief actually lands.
  useEffect(() => {
    if (!events || pendingPrep.size === 0) return
    const stillPending = new Set(
      [...pendingPrep].filter((id) => !events.find((e) => e.id === id)?.prep_brief)
    )
    if (stillPending.size !== pendingPrep.size) setPendingPrep(stillPending)
  }, [events, pendingPrep])

  const syncMutation = useMutation({
    mutationFn: syncCalendars,
    onSuccess: () => {
      // The sync runs in the background; refetch shortly after.
      setTimeout(() => queryClient.invalidateQueries({ queryKey: ['calendar'] }), 2500)
    },
  })

  const prepMutation = useMutation({
    mutationFn: generateEventPrep,
    onSuccess: (_data, id) => setPendingPrep((s) => new Set(s).add(id)),
  })

  const followUpMutation = useMutation({
    mutationFn: draftEventFollowUp,
    onSuccess: (_data, id) => {
      setFollowedUp((s) => new Set(s).add(id))
      queryClient.invalidateQueries({ queryKey: ['approvals'] })
    },
  })

  const hasAccount = accounts && accounts.length > 0
  const now = Date.now()

  const grouped = (events ?? []).reduce<Record<string, CalendarEvent[]>>((acc, ev) => {
    const key = dayKey(ev.start_time)
    ;(acc[key] ??= []).push(ev)
    return acc
  }, {})

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <div className="mt-0.5 rounded-lg bg-primary/10 p-2 text-primary">
            <CalendarClock className="size-5" />
          </div>
          <div>
            <h1 className="text-2xl font-semibold">Calendar</h1>
            <p className="text-sm text-muted-foreground">
              Upcoming meetings from your connected account, with AI prep briefs and follow-ups.
            </p>
          </div>
        </div>
        {hasAccount && (
          <Button
            onClick={() => syncMutation.mutate()}
            disabled={syncMutation.isPending}
            size="sm"
            variant="outline"
          >
            <RefreshCw className={cn('size-4', syncMutation.isPending && 'animate-spin')} />
            {syncMutation.isPending ? 'Syncing…' : 'Sync'}
          </Button>
        )}
      </div>

      {!hasAccount ? (
        <Card>
          <CardContent className="flex flex-col items-start gap-3 py-8">
            <p className="text-sm text-muted-foreground">
              No connected calendar yet. Connect a Google or Outlook account to pull in your
              meetings — the same connection powers email and calendar.
            </p>
            <Button asChild size="sm">
              <Link to="/email">Connect an account</Link>
            </Button>
          </CardContent>
        </Card>
      ) : isLoading ? (
        <p className="text-sm text-muted-foreground">Loading your calendar…</p>
      ) : events && events.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-start gap-3 py-8">
            <p className="text-sm text-muted-foreground">
              No events synced yet. Tap <span className="font-medium">Sync</span> to pull your
              upcoming meetings.
            </p>
          </CardContent>
        </Card>
      ) : (
        Object.entries(grouped).map(([day, dayEvents]) => (
          <div key={day} className="flex flex-col gap-2">
            <h2 className="text-sm font-semibold text-muted-foreground">{day}</h2>
            <div className="flex flex-col gap-3">
              {dayEvents.map((event) => {
                const isPast = new Date(event.end_time ?? event.start_time).getTime() < now
                const generating = pendingPrep.has(event.id)
                return (
                  <Card key={event.id}>
                    <CardContent className="flex flex-col gap-3 py-4">
                      <div className="flex flex-wrap items-baseline justify-between gap-2">
                        <p className="font-medium">{event.title}</p>
                        <span className="text-xs font-medium text-muted-foreground">
                          {timeLabel(event)}
                        </span>
                      </div>

                      <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
                        {event.location && (
                          <span className="flex items-center gap-1">
                            <MapPin className="size-3.5" />
                            {event.location}
                          </span>
                        )}
                        {event.attendees.length > 0 && (
                          <span className="flex items-center gap-1">
                            <Users className="size-3.5" />
                            {event.attendees.length} attendee
                            {event.attendees.length > 1 ? 's' : ''}
                          </span>
                        )}
                      </div>

                      {event.prep_brief && (
                        <div className="rounded-md border bg-muted/40 p-3">
                          <p className="mb-1 flex items-center gap-1.5 text-xs font-semibold text-primary">
                            <Sparkles className="size-3.5" />
                            Prep brief
                          </p>
                          <p className="whitespace-pre-wrap text-sm leading-relaxed">
                            {event.prep_brief}
                          </p>
                        </div>
                      )}

                      <div className="flex flex-wrap gap-2">
                        {!isPast && (
                          <Button
                            size="sm"
                            variant="outline"
                            disabled={generating}
                            onClick={() => prepMutation.mutate(event.id)}
                          >
                            {generating ? (
                              <RefreshCw className="size-3.5 animate-spin" />
                            ) : (
                              <Sparkles className="size-3.5" />
                            )}
                            {generating
                              ? 'Writing…'
                              : event.prep_brief
                                ? 'Regenerate prep'
                                : 'Generate prep brief'}
                          </Button>
                        )}
                        {isPast && (
                          <Button
                            size="sm"
                            variant="outline"
                            disabled={followUpMutation.isPending || followedUp.has(event.id)}
                            onClick={() => followUpMutation.mutate(event.id)}
                          >
                            <Send className="size-3.5" />
                            {followedUp.has(event.id)
                              ? 'Follow-up sent to approvals'
                              : 'Draft follow-up email'}
                          </Button>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          </div>
        ))
      )}
    </div>
  )
}
