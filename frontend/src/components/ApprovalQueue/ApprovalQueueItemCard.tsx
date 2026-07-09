import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import type { ApprovalQueueItem } from '@/types'

const ITEM_TYPE_LABELS: Record<ApprovalQueueItem['item_type'], string> = {
  email_draft: 'Email draft',
  presentation_export: 'Presentation export',
  document_share: 'Document share',
  dummy: 'Test item',
}

interface Props {
  item: ApprovalQueueItem
  onApprove: (id: string) => void
  onReject: (id: string) => void
  isMutating?: boolean
}

export default function ApprovalQueueItemCard({ item, onApprove, onReject, isMutating }: Props) {
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between gap-2 space-y-0">
        <CardTitle className="text-base">{ITEM_TYPE_LABELS[item.item_type]}</CardTitle>
        <Badge variant="muted">{new Date(item.created_at).toLocaleString()}</Badge>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">{item.preview_text}</p>
      </CardContent>
      <CardFooter>
        <Button size="sm" disabled={isMutating} onClick={() => onApprove(item.id)}>
          Approve
        </Button>
        <Button
          size="sm"
          variant="outline"
          disabled={isMutating}
          onClick={() => onReject(item.id)}
        >
          Reject
        </Button>
      </CardFooter>
    </Card>
  )
}
