import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { Download, RefreshCw } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  downloadPresentation,
  getPresentation,
  regeneratePresentation,
} from '@/api/presentations'
import type { PresentationStatus, SlideLayout } from '@/types'

const IN_PROGRESS_STATUSES = new Set<PresentationStatus>(['draft', 'generating'])

const LAYOUT_LABELS: Record<SlideLayout, string> = {
  section_header: 'Section',
  bullets: 'Content',
  two_column: 'Two column',
  chart: 'Chart',
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
        <div>
          <h1 className="text-2xl font-semibold">{presentation.title || 'Untitled presentation'}</h1>
          <Badge variant={presentation.status === 'failed' ? 'destructive' : 'muted'} className="mt-2">
            {presentation.status}
          </Badge>
        </div>
        <div className="flex flex-wrap gap-2">
          {presentation.status === 'approved' && (
            <Button
              onClick={() =>
                downloadPresentation(presentation.id, `${presentation.title || 'presentation'}.pptx`)
              }
            >
              <Download className="size-4" />
              Download
            </Button>
          )}
          <Button variant="outline" disabled={!canRegenerate} onClick={() => regenerateMutation.mutate()}>
            <RefreshCw className="size-4" />
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
        <p className="text-sm text-destructive">{presentation.failure_reason}</p>
      )}

      {presentation.status === 'ready' && (
        <p className="text-sm text-muted-foreground">
          This presentation is ready and waiting for your approval before it can be downloaded.
          Review the outline below, then head to the{' '}
          <Link to="/approvals" className="underline">
            Approvals
          </Link>{' '}
          page to approve or reject it.
        </p>
      )}

      {IN_PROGRESS_STATUSES.has(presentation.status) && (
        <p className="text-sm text-muted-foreground">Generating outline…</p>
      )}

      {presentation.structured_content && (
        <div className="flex flex-col gap-3">
          {presentation.structured_content.slides.map((slide, i) => (
            <Card key={i}>
              <CardHeader className="flex-row items-center justify-between gap-2 space-y-0">
                <CardTitle className="text-base">
                  {i + 1}. {slide.title}
                </CardTitle>
                <Badge variant="muted">{LAYOUT_LABELS[slide.layout]}</Badge>
              </CardHeader>
              <CardContent className="flex flex-col gap-3 text-sm">
                {slide.layout === 'two_column' ? (
                  <div className="grid grid-cols-2 gap-4">
                    <ul className="list-disc space-y-1 pl-4">
                      {slide.left_column.map((item, j) => (
                        <li key={j}>{item}</li>
                      ))}
                    </ul>
                    <ul className="list-disc space-y-1 pl-4">
                      {slide.right_column.map((item, j) => (
                        <li key={j}>{item}</li>
                      ))}
                    </ul>
                  </div>
                ) : slide.layout === 'chart' && slide.chart ? (
                  <p className="text-muted-foreground">
                    Chart — {slide.chart.series_name}: {slide.chart.categories.join(', ')}
                  </p>
                ) : slide.bullets.length > 0 ? (
                  <ul className="list-disc space-y-1 pl-4">
                    {slide.bullets.map((bullet, j) => (
                      <li key={j}>{bullet}</li>
                    ))}
                  </ul>
                ) : null}

                {slide.speaker_notes && (
                  <p className="border-t pt-2 text-xs text-muted-foreground">
                    Speaker notes: {slide.speaker_notes}
                  </p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
