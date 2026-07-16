import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import { AlertTriangle, Check, Copy, Loader2, Sparkles } from 'lucide-react'

import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { acknowledgeDisclaimer, getDocument } from '@/api/documents'
import type { DocumentStatus, RiskFlag } from '@/types'

const IN_PROGRESS_STATUSES = new Set<DocumentStatus>([
  'uploaded',
  'extracting',
  'extracted',
  'reviewing',
])

const SEVERITY: Record<string, { label: string; tile: string; text: string }> = {
  high: { label: 'High risk', tile: 'bg-red-500 text-white', text: 'text-red-600 dark:text-red-500' },
  medium: {
    label: 'Medium risk',
    tile: 'bg-amber-500 text-white',
    text: 'text-amber-600 dark:text-amber-500',
  },
  low: { label: 'Low risk', tile: 'bg-muted-foreground text-background', text: 'text-muted-foreground' },
}

function StatusPill({ status }: { status: DocumentStatus }) {
  if (status === 'reviewed')
    return (
      <span className="flex items-center gap-1 rounded-full bg-green-500/10 px-2.5 py-0.5 text-[11px] font-semibold text-green-600 dark:text-green-500">
        <Check className="size-3" /> Reviewed
      </span>
    )
  if (status === 'failed')
    return (
      <span className="rounded-full bg-red-500/10 px-2.5 py-0.5 text-[11px] font-semibold text-red-600 dark:text-red-500">
        Failed
      </span>
    )
  return (
    <span className="flex items-center gap-1 rounded-full bg-primary/10 px-2.5 py-0.5 text-[11px] font-semibold capitalize text-primary">
      <Loader2 className="size-3 animate-spin" /> {status}
    </span>
  )
}

function RiskFlagRow({ flag }: { flag: RiskFlag }) {
  const s = SEVERITY[flag.severity] ?? SEVERITY.low
  return (
    <div className="flex gap-3 rounded-lg border bg-muted/20 p-3">
      <div className={cn('flex size-9 flex-none items-center justify-center rounded-lg', s.tile)}>
        <AlertTriangle className="size-4" />
      </div>
      <div className="min-w-0">
        <p className={cn('text-[11px] font-semibold uppercase tracking-wide', s.text)}>{s.label}</p>
        <p className="font-medium">{flag.category}</p>
        <p className="mt-0.5 text-sm text-muted-foreground">{flag.description}</p>
      </div>
    </div>
  )
}

export default function DocumentDetail() {
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()
  const [copied, setCopied] = useState(false)

  const { data: document } = useQuery({
    queryKey: ['documents', id],
    queryFn: () => getDocument(id!),
    enabled: !!id,
    refetchInterval: (query) =>
      query.state.data && IN_PROGRESS_STATUSES.has(query.state.data.status) ? 3000 : false,
  })

  const ackMutation = useMutation({
    mutationFn: () => acknowledgeDisclaimer(id!),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['documents', id] }),
  })

  if (!document) {
    return <p className="text-sm text-muted-foreground">Loading…</p>
  }

  const ext = document.filename.includes('.')
    ? document.filename.split('.').pop()!.toUpperCase()
    : 'DOC'

  const copyRewrite = () => {
    if (!document.review?.suggested_rewrite) return
    navigator.clipboard.writeText(document.review.suggested_rewrite)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex flex-col gap-2">
        <div className="flex items-center gap-3">
          <span className="rounded-md bg-primary/10 px-2 py-0.5 text-[11px] font-bold text-primary">
            {ext}
          </span>
          <h1 className="text-2xl font-semibold tracking-tight">{document.filename}</h1>
        </div>
        <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
          <StatusPill status={document.status} />
          <span>{new Date(document.created_at).toLocaleDateString()}</span>
        </div>
        {document.instructions && (
          <p className="text-sm text-muted-foreground">
            <span className="font-medium text-foreground">Focus requested: </span>
            {document.instructions}
          </p>
        )}
      </div>

      {document.status === 'failed' && (
        <Card className="border-destructive/40 bg-destructive/5">
          <CardContent className="pt-6 text-sm text-destructive">
            {document.failure_reason}
          </CardContent>
        </Card>
      )}

      {!document.review && document.status !== 'failed' && (
        <Card>
          <CardContent className="flex items-center gap-2 pt-6 text-sm text-muted-foreground">
            <Loader2 className="size-4 animate-spin" /> Review in progress…
          </CardContent>
        </Card>
      )}

      {document.review && (
        <>
          {!document.review.disclaimer_ack && (
            <Card className="border-amber-500/40 bg-amber-500/5">
              <CardContent className="pt-6">
                <p className="text-sm text-muted-foreground">
                  This review is generated by AI for informational purposes only. It is not legal or
                  financial advice and does not replace review by a qualified professional. Verify
                  all flagged risks and suggested language before relying on them.
                </p>
                <Button
                  size="sm"
                  className="mt-3"
                  disabled={ackMutation.isPending}
                  onClick={() => ackMutation.mutate()}
                >
                  I understand
                </Button>
              </CardContent>
            </Card>
          )}

          <div className="grid gap-6 lg:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)] lg:items-start">
            <div className="flex flex-col gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Sparkles className="size-4 text-primary" />
                    Executive summary
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm leading-relaxed">{document.review.executive_summary}</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <AlertTriangle className="size-4 text-amber-500" />
                    Risk flags
                    <span className="text-sm font-normal text-muted-foreground">
                      ({document.review.risk_flags.length})
                    </span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="flex flex-col gap-3">
                  {document.review.risk_flags.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No risks flagged.</p>
                  ) : (
                    document.review.risk_flags.map((flag, i) => <RiskFlagRow key={i} flag={flag} />)
                  )}
                </CardContent>
              </Card>
            </div>

            {document.review.suggested_rewrite && (
              <Card className="lg:sticky lg:top-6">
                <CardHeader className="flex-row items-center justify-between space-y-0">
                  <CardTitle className="text-base">Suggested rewrite</CardTitle>
                  <button
                    type="button"
                    onClick={copyRewrite}
                    className="flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium text-muted-foreground hover:bg-muted"
                  >
                    {copied ? <Check className="size-3.5 text-green-600" /> : <Copy className="size-3.5" />}
                    {copied ? 'Copied' : 'Copy'}
                  </button>
                </CardHeader>
                <CardContent>
                  <p className="whitespace-pre-wrap rounded-lg border-l-2 border-primary/60 bg-muted/40 py-2 pl-3 text-sm leading-relaxed">
                    {document.review.suggested_rewrite}
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        </>
      )}
    </div>
  )
}
