import { useQueryClient, useMutation, useQuery } from '@tanstack/react-query'

import ApprovalQueueItemCard from '@/components/ApprovalQueue/ApprovalQueueItemCard'
import { approveItem, listApprovals, rejectItem } from '@/api/approvals'

interface Props {
  /** Cap the number of items shown (used for the dashboard widget). Omit to show all. */
  limit?: number
}

export default function ApprovalQueueList({ limit }: Props) {
  const queryClient = useQueryClient()

  const { data, isLoading, isError } = useQuery({
    queryKey: ['approvals', 'pending'],
    queryFn: () => listApprovals('pending'),
    refetchInterval: 15_000,
  })

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['approvals'] })

  const approveMutation = useMutation({ mutationFn: approveItem, onSuccess: invalidate })
  const rejectMutation = useMutation({ mutationFn: rejectItem, onSuccess: invalidate })

  if (isLoading) {
    return <p className="text-sm text-muted-foreground">Loading approval queue…</p>
  }
  if (isError) {
    return <p className="text-sm text-destructive">Could not load the approval queue.</p>
  }

  const items = limit ? data?.slice(0, limit) : data

  if (!items || items.length === 0) {
    return <p className="text-sm text-muted-foreground">Nothing pending approval.</p>
  }

  const isMutating = approveMutation.isPending || rejectMutation.isPending

  return (
    <div className="flex flex-col gap-3">
      {items.map((item) => (
        <ApprovalQueueItemCard
          key={item.id}
          item={item}
          isMutating={isMutating}
          onApprove={(id) => approveMutation.mutate(id)}
          onReject={(id) => rejectMutation.mutate(id)}
        />
      ))}
    </div>
  )
}
