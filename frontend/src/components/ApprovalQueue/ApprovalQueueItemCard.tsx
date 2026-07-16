import { useState } from 'react'
import { Pencil } from 'lucide-react'

import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import EmailDraftEditor from '@/components/ApprovalQueue/EmailDraftEditor'
import type { ApprovalQueueItem } from '@/types'

const ITEM_TYPE_LABELS: Record<ApprovalQueueItem['item_type'], string> = {
  email_draft: 'Email draft',
  presentation_export: 'Presentation export',
  document_share: 'Document share',
  dummy: 'Test item',
}

const STATUS_BADGE: Record<
  ApprovalQueueItem['status'],
  { label: string; variant: 'default' | 'muted' | 'destructive' }
> = {
  pending: { label: 'Pending', variant: 'muted' },
  approved: { label: 'Approved', variant: 'default' },
  rejected: { label: 'Rejected', variant: 'destructive' },
}

interface Props {
  item: ApprovalQueueItem
  onApprove: (id: string) => void
  onReject: (id: string, reason: string) => void
  isMutating?: boolean
}

export default function ApprovalQueueItemCard({ item, onApprove, onReject, isMutating }: Props) {
  const [rejecting, setRejecting] = useState(false)
  const [reason, setReason] = useState('')
  const [editing, setEditing] = useState(false)

  const isPending = item.status === 'pending'
  const isEmailDraft = item.item_type === 'email_draft'
  const badge = STATUS_BADGE[item.status]

  return (
    <Card>
      <CardHeader className="flex-row items-start justify-between gap-2 space-y-0">
        <div className="flex flex-col gap-1">
          <CardTitle className="text-base">{ITEM_TYPE_LABELS[item.item_type]}</CardTitle>
          <p className="text-xs text-muted-foreground">
            Requested by {item.requested_by_name ?? 'someone'} ·{' '}
            {new Date(item.created_at).toLocaleString()}
          </p>
        </div>
        <Badge variant={badge.variant}>{badge.label}</Badge>
      </CardHeader>

      <CardContent className="flex flex-col gap-2">
        <p className="text-sm text-muted-foreground">{item.preview_text}</p>

        {!isPending && (
          <div className="rounded-md bg-muted/60 px-3 py-2 text-xs text-muted-foreground">
            {item.status === 'approved' ? 'Approved' : 'Rejected'} by{' '}
            {item.reviewed_by_name ?? 'a reviewer'}
            {item.reviewed_at && ` · ${new Date(item.reviewed_at).toLocaleString()}`}
            {item.review_note && (
              <p className="mt-1 text-foreground">
                {item.status === 'rejected' ? 'Reason: ' : 'Note: '}
                {item.review_note}
              </p>
            )}
          </div>
        )}
      </CardContent>

      {isPending && (
        <CardFooter className="flex-col items-stretch gap-3">
          {rejecting ? (
            <div className="flex flex-col gap-2">
              <Textarea
                autoFocus
                placeholder="Why are you rejecting this? (required)"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
              />
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="destructive"
                  disabled={isMutating || reason.trim().length === 0}
                  onClick={() => onReject(item.id, reason.trim())}
                >
                  Confirm reject
                </Button>
                <Button size="sm" variant="outline" onClick={() => setRejecting(false)}>
                  Cancel
                </Button>
              </div>
            </div>
          ) : (
            <div className="flex flex-wrap gap-2">
              <Button size="sm" disabled={isMutating} onClick={() => onApprove(item.id)}>
                Approve
              </Button>
              <Button
                size="sm"
                variant="outline"
                disabled={isMutating}
                onClick={() => setRejecting(true)}
              >
                Reject
              </Button>
              {isEmailDraft && (
                <Button size="sm" variant="ghost" onClick={() => setEditing(true)}>
                  <Pencil className="mr-1 size-3.5" />
                  Edit draft
                </Button>
              )}
            </div>
          )}
        </CardFooter>
      )}

      {editing && (
        <EmailDraftEditor draftId={item.reference_id} onClose={() => setEditing(false)} />
      )}
    </Card>
  )
}
