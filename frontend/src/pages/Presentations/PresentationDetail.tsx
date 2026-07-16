import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { CheckCircle2, Download, Loader2, RefreshCw } from 'lucide-react'

import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import {
  downloadPresentation,
  getPresentation,
  regeneratePresentation,
} from '@/api/presentations'
import type { PresentationStatus, SlideChart, SlideContent, SlideLayout } from '@/types'

const IN_PROGRESS_STATUSES = new Set<PresentationStatus>(['draft', 'generating'])

const LAYOUT_LABELS: Record<SlideLayout, string> = {
  section_header: 'Section header',
  bullets: 'Bullets',
  two_column: 'Two column',
  chart: 'Chart',
}

function StatusPill({ status }: { status: PresentationStatus }) {
  const map: Record<PresentationStatus, string> = {
    approved: 'bg-green-500/10 text-green-600 dark:text-green-500',
    ready: 'bg-amber-500/10 text-amber-600 dark:text-amber-500',
    failed: 'bg-red-500/10 text-red-600 dark:text-red-500',
    draft: 'bg-primary/10 text-primary',
    generating: 'bg-primary/10 text-primary',
  }
  const label =
    status === 'ready' ? 'Awaiting approval' : status.charAt(0).toUpperCase() + status.slice(1)
  return (
    <span
      className={cn(
        'flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[11px] font-semibold',
        map[status]
      )}
    >
      {status === 'generating' && <Loader2 className="size-3 animate-spin" />}
      {label}
    </span>
  )
}

function MiniBarChart({ chart }: { chart: SlideChart }) {
  const max = Math.max(...chart.values, 1)
  return (
    <div className="flex flex-col gap-2">
      <p className="text-xs font-medium text-muted-foreground">{chart.series_name}</p>
      <div className="flex h-40 items-end gap-2">
        {chart.values.map((v, i) => (
          <div key={i} className="flex flex-1 flex-col items-center justify-end gap-1">
            <span className="text-[11px] font-semibold">{v}</span>
            <div
              className="w-full rounded-t bg-primary transition-all"
              style={{ height: `${Math.max((v / max) * 100, 4)}%` }}
            />
          </div>
        ))}
      </div>
      <div className="flex gap-2">
        {chart.categories.map((c, i) => (
          <span key={i} className="flex-1 truncate text-center text-[11px] text-muted-foreground">
            {c}
          </span>
        ))}
      </div>
    </div>
  )
}

function SlideBody({ slide }: { slide: SlideContent }) {
  if (slide.layout === 'section_header') {
    return (
      <div className="flex min-h-40 flex-col items-center justify-center rounded-xl bg-primary p-8 text-center text-primary-foreground">
        <p className="text-2xl font-bold tracking-tight">{slide.title}</p>
        {slide.bullets[0] && <p className="mt-2 text-sm italic opacity-90">{slide.bullets[0]}</p>}
      </div>
    )
  }
  if (slide.layout === 'chart' && slide.chart) {
    return <MiniBarChart chart={slide.chart} />
  }
  if (slide.layout === 'two_column') {
    return (
      <div className="grid gap-4 sm:grid-cols-2">
        {[slide.left_column, slide.right_column].map((col, c) => (
          <ul key={c} className="flex flex-col gap-1.5">
            {col.map((item, j) => (
              <li key={j} className="flex items-start gap-2 text-sm">
                <CheckCircle2 className="mt-0.5 size-4 flex-none text-primary" />
                {item}
              </li>
            ))}
          </ul>
        ))}
      </div>
    )
  }
  return (
    <ul className="flex flex-col gap-2">
      {slide.bullets.map((bullet, j) => (
        <li key={j} className="flex items-start gap-2 text-sm">
          <CheckCircle2 className="mt-0.5 size-4 flex-none text-primary" />
          {bullet}
        </li>
      ))}
    </ul>
  )
}

export default function PresentationDetail() {
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()

  const { data: presentation } = useQuery({
    queryKey: ['presentations', id],
    queryFn: () => getPresentation(id!),
    enabled: !!id,
    refetchInterval: (query) =>
      query.state.data && IN_PROGRESS_STATUSES.has(query.state.data.status) ? 3000 : false,
  })

  const regenerateMutation = useMutation({
    mutationFn: () => regeneratePresentation(id!),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['presentations', id] }),
  })

  if (!presentation) {
    return <p className="text-sm text-muted-foreground">Loading…</p>
  }

  const canRegenerate = presentation.status !== 'generating' && !regenerateMutation.isPending

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between sm:gap-4">
        <div className="flex flex-col gap-2">
          <h1 className="text-2xl font-semibold tracking-tight">
            {presentation.title || 'Untitled presentation'}
          </h1>
          <div className="flex items-center gap-3 text-sm text-muted-foreground">
            <StatusPill status={presentation.status} />
            <span>{new Date(presentation.created_at).toLocaleDateString()}</span>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          {presentation.status === 'approved' && (
            <Button
              onClick={() =>
                downloadPresentation(presentation.id, `${presentation.title || 'presentation'}.pptx`)
              }
            >
              <Download className="size-4" />
              Download .pptx
            </Button>
          )}
          <Button variant="outline" disabled={!canRegenerate} onClick={() => regenerateMutation.mutate()}>
            <RefreshCw className={cn('size-4', regenerateMutation.isPending && 'animate-spin')} />
            Regenerate
          </Button>
        </div>
      </div>

      {presentation.instructions && (
        <p className="text-sm text-muted-foreground">
          <span className="font-medium text-foreground">Focus requested: </span>
          {presentation.instructions}
        </p>
      )}

      {presentation.status === 'failed' && (
        <Card className="border-destructive/40 bg-destructive/5 p-4 text-sm text-destructive">
          {presentation.failure_reason}
        </Card>
      )}

      {presentation.status === 'ready' && (
        <Card className="border-amber-500/40 bg-amber-500/5 p-4 text-sm text-muted-foreground">
          This presentation is ready and waiting for your approval before it can be downloaded.
          Review the slides below, then head to the{' '}
          <Link to="/approvals" className="font-medium text-primary underline">
            Approvals
          </Link>{' '}
          page.
        </Card>
      )}

      {IN_PROGRESS_STATUSES.has(presentation.status) && (
        <Card className="flex items-center gap-2 p-4 text-sm text-muted-foreground">
          <Loader2 className="size-4 animate-spin" /> Generating outline…
        </Card>
      )}

      {presentation.structured_content && (
        <div className="flex flex-col gap-4">
          {presentation.structured_content.slides.map((slide, i) => (
            <Card key={i} className="overflow-hidden">
              <div className="flex items-center justify-between gap-2 border-b bg-muted/30 px-4 py-2.5">
                <div className="flex items-center gap-2">
                  <span className="flex size-5 items-center justify-center rounded bg-foreground text-[11px] font-bold text-background">
                    {i + 1}
                  </span>
                  <span className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                    {LAYOUT_LABELS[slide.layout]}
                  </span>
                </div>
                <span className="truncate text-xs text-muted-foreground">{slide.title}</span>
              </div>
              <div className="flex flex-col gap-3 p-4">
                {slide.layout !== 'section_header' && (
                  <p className="font-semibold text-primary">{slide.title}</p>
                )}
                <SlideBody slide={slide} />
                {slide.speaker_notes && (
                  <div className="rounded-lg bg-muted/40 p-3">
                    <p className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                      Speaker notes
                    </p>
                    <p className="mt-1 text-xs italic text-muted-foreground">
                      {slide.speaker_notes}
                    </p>
                  </div>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
