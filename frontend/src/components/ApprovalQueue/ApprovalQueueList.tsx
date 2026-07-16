import { useState } from 'react'
import { useQueryClient, useMutation, useQuery } from '@tanstack/react-query'

import ApprovalQueueItemCard from '@/components/ApprovalQueue/ApprovalQueueItemCard'
import { cn } from '@/lib/utils'
import { approveItem, listApprovals, rejectItem } from '@/api/approvals'
import type { ApprovalItemType, ApprovalStatus } from '@/types'

interface Props {
  /** Cap the number of items shown (used for the dashboard widget). Omit to show all. */
  limit?: number
  /** Dashboard widget mode: pending only, no filter bar. */
  compact?: boolean
}

type StatusTab = ApprovalStatus | 'all'

const STATUS_TABS: { value: StatusTab; label: string }[] = [
  { value: 'pending', label: 'Pending' },
  { value: 'approved', label: 'Approved' },
  { value: 'rejected', label: 'Rejected' },
  { value: 'all', label: 'All' },
]

const TYPE_OPTIONS: { value: ApprovalItemType | 'all'; label: string }[] = [
  { value: 'all', label: 'All types' },
  { value: 'email_draft', label: 'Email drafts' },
  { value: 'presentation_export', label: 'Presentation exports' },
  { value: 'document_share', label: 'Document shares' },
]

export default function ApprovalQueueList({ limit, compact }: Props) {
  const queryClient = useQueryClient()
  const [statusTab, setStatusTab] = useState<StatusTab>('pending')
  const [typeFilter, setTypeFilter] = useState<ApprovalItemType | 'all'>('all')

  const effectiveStatus: StatusTab = compact ? 'pending' : statusTab
  const effectiveType = compact ? 'all' : typeFilter

  const { data, isLoading, isError } = useQuery({
    queryKey: ['approvals', effectiveStatus, effectiveType],
    queryFn: () =>
      listApprovals({
        status: effectiveStatus === 'all' ? undefined : effectiveStatus,
        type: effectiveType === 'all' ? undefined : effectiveType,
      }),
    refetchInterval: 15_000,
  })

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['approvals'] })

  const approveMutation = useMutation({
    mutationFn: ({ id, note }: { id: string; note?: string }) => approveItem(id, note),
    onSuccess: invalidate,
  })
  const rejectMutation = useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) => rejectItem(id, reason),
    onSuccess: invalidate,
  })

  const isMutating = approveMutation.isPending || rejectMutation.isPending
  const items = limit ? data?.slice(0, limit) : data

  return (
    <div className="flex flex-col gap-4">
      {!compact && (
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-wrap gap-1 rounded-lg bg-muted p-1">
            {STATUS_TABS.map((tab) => (
              <button
                key={tab.value}
                type="button"
                onClick={() => setStatusTab(tab.value)}
                className={cn(
                  'rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
                  statusTab === tab.value
                    ? 'bg-background text-foreground shadow-sm'
                    : 'text-muted-foreground hover:text-foreground'
                )}
              >
                {tab.label}
              </button>
            ))}
          </div>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value as ApprovalItemType | 'all')}
            className="h-9 rounded-md border border-input bg-background px-3 text-sm"
          >
            {TYPE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      )}

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading approval queue…</p>
      ) : isError ? (
        <p className="text-sm text-destructive">Could not load the approval queue.</p>
      ) : !items || items.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          {compact || statusTab === 'pending' ? 'Nothing pending approval.' : 'No items here.'}
        </p>
      ) : (
        <div className="flex flex-col gap-3">
          {items.map((item) => (
            <ApprovalQueueItemCard
              key={item.id}
              item={item}
              isMutating={isMutating}
              onApprove={(id) => approveMutation.mutate({ id })}
              onReject={(id, reason) => rejectMutation.mutate({ id, reason })}
            />
          ))}
        </div>
      )}
    </div>
  )
}
