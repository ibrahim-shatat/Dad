import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { Copy, RefreshCw } from 'lucide-react'

import { Badge, type BadgeProps } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  getMeeting,
  regenerateMeeting,
  updateActionItemStatus,
  updateDecisionStatus,
} from '@/api/meetings'
import type { ActionItemStatus, DecisionStatus, EmailDraft } from '@/types'

const ACTION_ITEM_CYCLE: Record<ActionItemStatus, ActionItemStatus> = {
  open: 'in_progress',
  in_progress: 'done',
  done: 'open',
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

const DECISION_VARIANT: Record<DecisionStatus, BadgeProps['variant']> = {
  pending: 'default',
  decided: 'muted',
  deferred: 'outline',
}

function FollowUpEmail({ draft }: { draft: EmailDraft }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(`Subject: ${draft.subject}\n\n${draft.body}`)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between gap-2 space-y-0">
        <CardTitle className="text-base">Suggested follow-up email</CardTitle>
        <Badge variant={draft.status === 'rejected' ? 'destructive' : 'muted'}>
          {draft.status === 'pending_approval' ? 'Awaiting approval' : draft.status}
        </Badge>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <p className="text-sm font-medium">{draft.subject}</p>
        <p className="whitespace-pre-wrap text-sm text-muted-foreground">{draft.body}</p>

        {draft.status === 'pending_approval' && (
          <p className="text-sm text-muted-foreground">
            This draft needs your approval before it can be copied and sent. Head to the{' '}
            <Link to="/approvals" className="underline">
              Approvals
            </Link>{' '}
            page to approve or reject it.
          </p>
        )}
        {draft.status === 'approved' && (
          <div>
            <Button size="sm" onClick={handleCopy}>
              <Copy className="size-4" />
              {copied ? 'Copied!' : 'Copy to clipboard'}
            </Button>
          </div>
        )}
        {draft.status === 'rejected' && (
          <p className="text-sm text-muted-foreground">This draft was rejected.</p>
        )}
      </CardContent>
    </Card>
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

  const regenerateMutation = useMutation({
    mutationFn: () => regenerateMeeting(id!),
    onSuccess: invalidate,
  })
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

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between sm:gap-4">
        <div>
          <h1 className="text-2xl font-semibold">{meeting.title}</h1>
          <p className="text-xs text-muted-foreground">{meeting.meeting_date}</p>
          <Badge variant={meeting.status === 'failed' ? 'destructive' : 'muted'} className="mt-2">
            {meeting.status}
          </Badge>
        </div>
        <Button
          variant="outline"
          className="self-start"
          disabled={meeting.status === 'processing' || regenerateMutation.isPending}
          onClick={() => regenerateMutation.mutate()}
        >
          <RefreshCw className="size-4" />
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
        <p className="text-sm text-destructive">{meeting.failure_reason}</p>
      )}
      {meeting.status === 'processing' && (
        <p className="text-sm text-muted-foreground">Processing meeting notes…</p>
      )}

      {meeting.summary && (
        <Card>
          <CardHeader>
            <CardTitle>Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm">{meeting.summary}</p>
          </CardContent>
        </Card>
      )}

      {meeting.action_items.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Action items</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-2">
            {meeting.action_items.map((item) => (
              <div
                key={item.id}
                className="flex items-center justify-between gap-3 rounded-md border p-3 text-sm"
              >
                <div>
                  <p>{item.description}</p>
                  <p className="text-xs text-muted-foreground">
                    {item.owner}
                    {item.due_date ? ` · due ${item.due_date}` : ''}
                  </p>
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  disabled={actionItemMutation.isPending}
                  onClick={() =>
                    actionItemMutation.mutate({
                      itemId: item.id,
                      status: ACTION_ITEM_CYCLE[item.status],
                    })
                  }
                >
                  {ACTION_ITEM_LABELS[item.status]}
                </Button>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {meeting.decisions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Decisions</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-2">
            {meeting.decisions.map((decision) => (
              <div
                key={decision.id}
                className="flex items-center justify-between gap-3 rounded-md border p-3 text-sm"
              >
                <div>
                  <p>{decision.description}</p>
                  <p className="text-xs text-muted-foreground">
                    {decision.decided_by}
                    {decision.deadline ? ` · deadline ${decision.deadline}` : ''}
                  </p>
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  disabled={decisionMutation.isPending}
                  onClick={() =>
                    decisionMutation.mutate({
                      decisionId: decision.id,
                      status: DECISION_CYCLE[decision.status],
                    })
                  }
                >
                  <Badge variant={DECISION_VARIANT[decision.status]}>{decision.status}</Badge>
                </Button>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {meeting.email_drafts.map((draft) => (
        <FollowUpEmail key={draft.id} draft={draft} />
      ))}
    </div>
  )
}
