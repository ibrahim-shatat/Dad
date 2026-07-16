import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Check, RefreshCw, Sparkles, Sun } from 'lucide-react'

import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { fetchTodayBriefing, generateBriefing, toggleBriefingItem } from '@/api/briefing'
import type { BriefingItem } from '@/types'

const SEVERITY_DOT: Record<string, string> = {
  high: 'bg-red-500',
  medium: 'bg-amber-500',
  low: 'bg-muted-foreground',
}

export default function Briefing() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  const { data: briefing, isLoading, isError } = useQuery({
    queryKey: ['briefing', 'today'],
    queryFn: fetchTodayBriefing,
  })

  const setBriefing = (updated: typeof briefing) =>
    queryClient.setQueryData(['briefing', 'today'], updated)

  const generateMutation = useMutation({
    mutationFn: generateBriefing,
    onSuccess: setBriefing,
  })

  const toggleMutation = useMutation({
    mutationFn: ({ key, handled }: { key: string; handled: boolean }) =>
      toggleBriefingItem(key, handled),
    onSuccess: setBriefing,
  })

  if (isLoading) {
    return <p className="text-sm text-muted-foreground">Loading your briefing…</p>
  }
  if (isError || !briefing) {
    return <p className="text-sm text-destructive">Could not load your briefing.</p>
  }

  const dateLabel = new Date(briefing.briefing_date + 'T00:00:00').toLocaleDateString(undefined, {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
  })
  const activeSections = briefing.sections.filter((s) => s.items.length > 0)
  const allHandled = briefing.total_items > 0 && briefing.handled_items === briefing.total_items

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <div className="mt-0.5 rounded-xl bg-primary/10 p-2 text-primary">
            <Sun className="size-5" />
          </div>
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Daily briefing</h1>
            <p className="text-sm text-muted-foreground">{dateLabel}</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          {briefing.total_items > 0 && (
            <div className="hidden flex-col items-end gap-1 sm:flex">
              <span className="text-xs text-muted-foreground">
                {briefing.handled_items}/{briefing.total_items} handled
              </span>
              <div className="h-1.5 w-28 overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full rounded-full bg-primary transition-all"
                  style={{ width: `${(briefing.handled_items / briefing.total_items) * 100}%` }}
                />
              </div>
            </div>
          )}
          <Button
            onClick={() => generateMutation.mutate()}
            disabled={generateMutation.isPending}
            size="sm"
          >
            {generateMutation.isPending ? (
              <RefreshCw className="size-4 animate-spin" />
            ) : briefing.generated_at ? (
              <RefreshCw className="size-4" />
            ) : (
              <Sparkles className="size-4" />
            )}
            {generateMutation.isPending
              ? 'Writing…'
              : briefing.generated_at
                ? 'Regenerate'
                : 'Generate briefing'}
          </Button>
        </div>
      </div>

      {/* Mobile progress bar */}
      {briefing.total_items > 0 && (
        <div className="flex items-center gap-3 text-sm text-muted-foreground sm:hidden">
          <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
            <div
              className="h-full rounded-full bg-primary transition-all"
              style={{ width: `${(briefing.handled_items / briefing.total_items) * 100}%` }}
            />
          </div>
          <span className="whitespace-nowrap">
            {briefing.handled_items}/{briefing.total_items} handled
          </span>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.35fr)] lg:items-start">
        {/* AI summary */}
        <Card className="lg:sticky lg:top-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Sparkles className="size-4 text-primary" />
              Executive summary
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            {briefing.summary ? (
              <p className="text-sm leading-relaxed">{briefing.summary}</p>
            ) : (
              <p className="text-sm text-muted-foreground">
                No summary yet. Tap <span className="font-medium">Generate briefing</span> and Claude
                will write a start-of-day overview of everything below.
              </p>
            )}
            {briefing.top_priorities.length > 0 && (
              <div className="flex flex-col gap-2">
                <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  Top priorities
                </p>
                <ol className="flex flex-col gap-2">
                  {briefing.top_priorities.map((p, i) => (
                    <li key={i} className="flex items-start gap-2.5 text-sm">
                      <span className="flex size-5 flex-none items-center justify-center rounded-full bg-primary/10 text-[11px] font-semibold text-primary">
                        {i + 1}
                      </span>
                      <span>{p}</span>
                    </li>
                  ))}
                </ol>
              </div>
            )}
            {briefing.generated_at && (
              <p className="text-[11px] text-muted-foreground">
                Generated {new Date(briefing.generated_at).toLocaleString()}
              </p>
            )}
          </CardContent>
        </Card>

        {/* Item sections */}
        <div className="flex flex-col gap-6">
          {allHandled && (
            <Card>
              <CardContent className="flex items-center gap-3 py-6 text-sm">
                <Check className="size-5 text-green-600" />
                You've cleared everything on today's briefing. Nice work.
              </CardContent>
            </Card>
          )}

          {activeSections.length === 0 ? (
            <Card>
              <CardContent className="py-10 text-center text-sm text-muted-foreground">
                Nothing needs your attention right now — no urgent emails, approvals, due action
                items, or document risks.
              </CardContent>
            </Card>
          ) : (
            activeSections.map((section) => (
              <div key={section.id} className="flex flex-col gap-2">
                <h2 className="text-sm font-semibold text-muted-foreground">
                  {section.label}
                  <span className="ml-2 font-normal">({section.items.length})</span>
                </h2>
                <div className="flex flex-col gap-2">
                  {section.items.map((item) => (
                    <BriefingItemRow
                      key={item.key}
                      item={item}
                      disabled={toggleMutation.isPending}
                      onToggle={() =>
                        toggleMutation.mutate({ key: item.key, handled: !item.handled })
                      }
                      onOpen={() => item.link && navigate(item.link)}
                    />
                  ))}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

interface RowProps {
  item: BriefingItem
  disabled?: boolean
  onToggle: () => void
  onOpen: () => void
}

function BriefingItemRow({ item, disabled, onToggle, onOpen }: RowProps) {
  return (
    <div
      className={cn(
        'flex items-start gap-3 rounded-lg border bg-card px-3 py-3 transition-opacity',
        item.handled && 'opacity-55'
      )}
    >
      <button
        type="button"
        onClick={onToggle}
        disabled={disabled}
        aria-label={item.handled ? 'Mark as not handled' : 'Mark as handled'}
        className={cn(
          'mt-0.5 flex size-5 flex-none items-center justify-center rounded-full border transition-colors',
          item.handled
            ? 'border-primary bg-primary text-primary-foreground'
            : 'border-muted-foreground/40 hover:border-primary'
        )}
      >
        {item.handled && <Check className="size-3.5" />}
      </button>

      <button type="button" onClick={onOpen} className="min-w-0 flex-1 text-left">
        <div className="flex items-center gap-2">
          {item.severity && (
            <span
              className={cn(
                'size-2 flex-none rounded-full',
                SEVERITY_DOT[item.severity] ?? 'bg-muted-foreground'
              )}
            />
          )}
          <p className={cn('truncate text-sm font-medium', item.handled && 'line-through')}>
            {item.title}
          </p>
        </div>
        {item.subtitle && (
          <p className="mt-0.5 truncate text-xs text-muted-foreground">{item.subtitle}</p>
        )}
        {item.detail && (
          <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">{item.detail}</p>
        )}
      </button>
    </div>
  )
}
