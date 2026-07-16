import { useState } from 'react'
import { Check, FileText, Mail, Pencil, Presentation, Share2, X } from 'lucide-react'

import { cn } from '@/lib/utils'
import { Card, CardContent, CardFooter, CardHeader } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import EmailDraftEditor from '@/components/ApprovalQueue/EmailDraftEditor'
import type { ApprovalQueueItem } from '@/types'

const ITEM_TYPE_META: Record<
  ApprovalQueueItem['item_type'],
  { label: string; icon: typeof Mail }
> = {
  email_draft: { label: 'Email draft', icon: Mail },
  presentation_export: { label: 'Presentation export', icon: Presentation },
  document_share: { label: 'Document share', icon: Share2 },
  dummy: { label: 'Test item', icon: FileText },
}

interface Props {
  item: ApprovalQueueItem
  onApprove: (id: string) => void
  onReject: (id: string, reason: string) => void
  isMutating?: boolean
}

function StatusPill({ status }: { status: ApprovalQueueItem['status'] }) {
  if (status === 'approved') {
    return (
      <span className="flex items-center gap-1 rounded-full bg-green-500/10 px-2.5 py-0.5 text-[11px] font-semibold text-green-600 dark:text-green-500">
        <Check className="size-3" /> Approved
      </span>
    )
  }
  if (status === 'rejected') {
    return (
      <span className="flex items-center gap-1 rounded-full bg-red-500/10 px-2.5 py-0.5 text-[11px] font-semibold text-red-600 dark:text-red-500">
        <X className="size-3" /> Rejected
      </span>
    )
  }
  return (
    <span className="rounded-full bg-primary/10 px-2.5 py-0.5 text-[11px] font-semibold text-primary">
      Pending review
    </span>
  )
}

export default function ApprovalQueueItemCard({ item, onApprove, onReject, isMutating }: Props) {
  const [rejecting, setRejecting] = useState(false)
  const [reason, setReason] = useState('')
  const [editing, setEditing] = useState(false)

  const isPending = item.status === 'pending'
  const isEmailDraft = item.item_type === 'email_draft'
  const meta = ITEM_TYPE_META[item.item_type]
  const Icon = meta.icon

  return (
    <Card className="flex flex-col">
      <CardHeader className="flex-row items-start gap-3 space-y-0 pb-3">
        <div className="flex size-9 flex-none items-center justify-center rounded-lg bg-primary/10 text-primary">
          <Icon className="size-4" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="font-semibold leading-tight">{meta.label}</p>
          <p className="mt-0.5 text-xs text-muted-foreground">
            Requested by {item.requested_by_name ?? 'someone'} ·{' '}
            {new Date(item.created_at).toLocaleString()}
          </p>
        </div>
        <StatusPill status={item.status} />
      </CardHeader>

      <CardContent className="flex flex-1 flex-col gap-2 pb-4">
        <div className="rounded-lg border bg-muted/30 px-3 py-2.5 text-sm">{item.preview_text}</div>

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
        <CardFooter className="flex-col items-stretch gap-3 border-t pt-4">
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
            <div className="flex items-center justify-between gap-2">
              {isEmailDraft ? (
                <Button size="sm" variant="ghost" onClick={() => setEditing(true)}>
                  <Pencil className="size-3.5" />
                  Edit draft
                </Button>
              ) : (
                <span />
              )}
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  disabled={isMutating}
                  onClick={() => setRejecting(true)}
                  className={cn('border-destructive/40 text-destructive hover:bg-destructive/10')}
                >
                  Reject
                </Button>
                <Button size="sm" disabled={isMutating} onClick={() => onApprove(item.id)}>
                  Approve
                </Button>
              </div>
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
