import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { Check, Copy, Gavel, Loader2, Mail, RefreshCw, Sparkles } from 'lucide-react'

import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  getMeeting,
  regenerateMeeting,
  updateActionItemStatus,
  updateDecisionStatus,
} from '@/api/meetings'
import type {
  ActionItem,
  ActionItemStatus,
  Decision,
  DecisionStatus,
  EmailDraft,
  MeetingStatus,
} from '@/types'

const ACTION_ITEM_CYCLE: Record<ActionItemStatus, ActionItemStatus> = {
  open: 'in_progress',
  in_progress: 'done',
  done: 'open',
}
const ACTION_ITEM_STYLE: Record<ActionItemStatus, string> = {
  open: 'bg-muted text-muted-foreground',
  in_progress: 'bg-amber-500/10 text-amber-600 dark:text-amber-500',
  done: 'bg-green-500/10 text-green-600 dark:text-green-500',
}
const ACTION_ITEM_LABELS: Record<ActionItemStatus, string> = {
  open: 'Open',
  in_progress: 'In progress',
  done: 'Done',
}

const DECISION_CYCLE: Record<DecisionStatus, DecisionStatus> = {
  pending: 'decided',
  decided: 'deferred',
  deferred: 'pending',
}
const DECISION_STYLE: Record<DecisionStatus, string> = {
  pending: 'bg-amber-500/10 text-amber-600 dark:text-amber-500',
  decided: 'bg-green-500/10 text-green-600 dark:text-green-500',
  deferred: 'bg-muted text-muted-foreground',
}

function initials(name: string): string {
  return name
    .split(' ')
    .map((p) => p[0])
    .filter(Boolean)
    .slice(0, 2)
    .join('')
    .toUpperCase()
}

function MeetingStatusPill({ status }: { status: MeetingStatus }) {
  if (status === 'processed')
    return (
      <span className="flex items-center gap-1 rounded-full bg-green-500/10 px-2.5 py-0.5 text-[11px] font-semibold text-green-600 dark:text-green-500">
        <Check className="size-3" /> Processed
      </span>
    )
  if (status === 'failed')
    return (
      <span className="rounded-full bg-red-500/10 px-2.5 py-0.5 text-[11px] font-semibold text-red-600 dark:text-red-500">
        Failed
      </span>
    )
  return (
    <span className="flex items-center gap-1 rounded-full bg-primary/10 px-2.5 py-0.5 text-[11px] font-semibold text-primary">
      <Loader2 className="size-3 animate-spin" /> Processing
    </span>
  )
}

function FollowUpEmail({ draft }: { draft: EmailDraft }) {
  const [copied, setCopied] = useState(false)
  const handleCopy = async () => {
    await navigator.clipboard.writeText(`Subject: ${draft.subject}\n\n${draft.body}`)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }
  return (
    <Card className="lg:sticky lg:top-6">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Mail className="size-4 text-primary" />
          Draft follow-up email
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <div className="rounded-lg bg-muted/40 p-3">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
            Subject
          </p>
          <p className="mt-0.5 text-sm font-medium">{draft.subject}</p>
          <p className="mt-2 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
            Preview
          </p>
          <p className="mt-0.5 line-clamp-4 whitespace-pre-wrap text-sm text-muted-foreground">
            {draft.body}
          </p>
        </div>

        {draft.status === 'pending_approval' && (
          <div className="rounded-lg bg-primary/5 p-3">
            <p className="text-sm text-muted-foreground">
              Waiting in the approval queue. Review required before sending.
            </p>
            <Button asChild size="sm" className="mt-2 w-full">
              <Link to="/approvals">View in Approvals</Link>
            </Button>
          </div>
        )}
        {draft.status === 'approved' && (
          <Button size="sm" onClick={handleCopy}>
            <Copy className="size-4" />
            {copied ? 'Copied!' : 'Copy to clipboard'}
          </Button>
        )}
        {draft.status === 'rejected' && (
          <p className="text-sm text-muted-foreground">This draft was rejected.</p>
        )}
      </CardContent>
    </Card>
  )
}

function ActionItemRow({
  item,
  disabled,
  onCycle,
}: {
  item: ActionItem
  disabled: boolean
  onCycle: () => void
}) {
  const overdue =
    item.due_date && item.status !== 'done' && item.due_date < new Date().toISOString().slice(0, 10)
  return (
    <div className="flex flex-wrap items-center gap-3 rounded-lg border bg-muted/20 p-3">
      <p className="min-w-[60%] flex-1 text-sm">{item.description}</p>
      <div className="flex items-center gap-2">
        <span className="flex size-6 items-center justify-center rounded-full bg-primary/10 text-[10px] font-semibold text-primary">
          {initials(item.owner)}
        </span>
        <span className="text-xs text-muted-foreground">{item.owner}</span>
      </div>
      {item.due_date && (
        <span className={cn('text-xs', overdue ? 'font-medium text-red-500' : 'text-muted-foreground')}>
          {item.due_date}
        </span>
      )}
      <button
        type="button"
        disabled={disabled}
        onClick={onCycle}
        className={cn(
          'rounded-full px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide transition-opacity hover:opacity-80 disabled:opacity-50',
          ACTION_ITEM_STYLE[item.status]
        )}
      >
        {ACTION_ITEM_LABELS[item.status]}
      </button>
    </div>
  )
}

function DecisionCard({
  decision,
  disabled,
  onCycle,
}: {
  decision: Decision
  disabled: boolean
  onCycle: () => void
}) {
  return (
    <div className="flex gap-3 rounded-lg border bg-muted/20 p-3">
      <div className="flex size-8 flex-none items-center justify-center rounded-full bg-green-500/10 text-green-600 dark:text-green-500">
        <Check className="size-4" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="font-medium">{decision.description}</p>
        <p className="text-xs text-muted-foreground">
          Decider: {decision.decided_by}
          {decision.deadline ? ` · ${decision.deadline}` : ''}
        </p>
        <button
          type="button"
          disabled={disabled}
          onClick={onCycle}
          className={cn(
            'mt-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wide hover:opacity-80 disabled:opacity-50',
            DECISION_STYLE[decision.status]
          )}
        >
          {decision.status}
        </button>
      </div>
    </div>
  )
}

export default function MeetingDetail() {
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()

  const { data: meeting } = useQuery({
    queryKey: ['meetings', id],
    queryFn: () => getMeeting(id!),
    enabled: !!id,
    refetchInterval: (query) => (query.state.data?.status === 'processing' ? 3000 : false),
  })

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['meetings', id] })
  const regenerateMutation = useMutation({ mutationFn: () => regenerateMeeting(id!), onSuccess: invalidate })
  const actionItemMutation = useMutation({
    mutationFn: ({ itemId, status }: { itemId: string; status: ActionItemStatus }) =>
      updateActionItemStatus(id!, itemId, status),
    onSuccess: invalidate,
  })
  const decisionMutation = useMutation({
    mutationFn: ({ decisionId, status }: { decisionId: string; status: DecisionStatus }) =>
      updateDecisionStatus(id!, decisionId, status),
    onSuccess: invalidate,
  })

  if (!meeting) {
    return <p className="text-sm text-muted-foreground">Loading…</p>
  }

  const draft = meeting.email_drafts[0]

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between sm:gap-4">
        <div className="flex flex-col gap-2">
          <h1 className="text-2xl font-semibold tracking-tight">{meeting.title}</h1>
          <div className="flex items-center gap-3 text-sm text-muted-foreground">
            <MeetingStatusPill status={meeting.status} />
            <span>{meeting.meeting_date}</span>
          </div>
        </div>
        <Button
          variant="outline"
          className="self-start"
          disabled={meeting.status === 'processing' || regenerateMutation.isPending}
          onClick={() => regenerateMutation.mutate()}
        >
          <RefreshCw className={cn('size-4', regenerateMutation.isPending && 'animate-spin')} />
          Regenerate
        </Button>
      </div>

      {meeting.instructions && (
        <p className="text-sm text-muted-foreground">
          <span className="font-medium text-foreground">Focus requested: </span>
          {meeting.instructions}
        </p>
      )}

      {meeting.status === 'failed' && (
        <Card className="border-destructive/40 bg-destructive/5 p-4 text-sm text-destructive">
          {meeting.failure_reason}
        </Card>
      )}
      {meeting.status === 'processing' && (
        <Card className="flex items-center gap-2 p-4 text-sm text-muted-foreground">
          <Loader2 className="size-4 animate-spin" /> Processing meeting notes…
        </Card>
      )}

      {/* Summary + draft */}
      {meeting.summary && (
        <div
          className={cn(
            'grid gap-6 lg:items-start',
            draft && 'lg:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)]'
          )}
        >
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Sparkles className="size-4 text-primary" />
                AI summary
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm leading-relaxed">{meeting.summary}</p>
            </CardContent>
          </Card>
          {draft && <FollowUpEmail draft={draft} />}
        </div>
      )}

      {meeting.action_items.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              Action items{' '}
              <span className="font-normal text-muted-foreground">
                ({meeting.action_items.length})
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-2">
            {meeting.action_items.map((item) => (
              <ActionItemRow
                key={item.id}
                item={item}
                disabled={actionItemMutation.isPending}
                onCycle={() =>
                  actionItemMutation.mutate({ itemId: item.id, status: ACTION_ITEM_CYCLE[item.status] })
                }
              />
            ))}
          </CardContent>
        </Card>
      )}

      {meeting.decisions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Gavel className="size-4 text-primary" />
              Key decisions
            </CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-2">
            {meeting.decisions.map((decision) => (
              <DecisionCard
                key={decision.id}
                decision={decision}
                disabled={decisionMutation.isPending}
                onCycle={() =>
                  decisionMutation.mutate({
                    decisionId: decision.id,
                    status: DECISION_CYCLE[decision.status],
                  })
                }
              />
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
