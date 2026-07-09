import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate, Link } from 'react-router-dom'
import { Presentation as PresentationIcon } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { listDocuments } from '@/api/documents'
import { createPresentation, listPresentations } from '@/api/presentations'
import type { PresentationStatus } from '@/types'

const STATUS_LABELS: Record<PresentationStatus, string> = {
  draft: 'Draft',
  generating: 'Generating…',
  ready: 'Awaiting approval',
  approved: 'Approved',
  failed: 'Failed',
}

const IN_PROGRESS_STATUSES = new Set<PresentationStatus>(['draft', 'generating'])
const DOCUMENT_SOURCE_STATUSES = new Set(['extracted', 'reviewing', 'reviewed'])

export default function Presentations() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [sourceMode, setSourceMode] = useState<'document' | 'notes'>('document')
  const [sourceDocumentId, setSourceDocumentId] = useState('')
  const [sourceText, setSourceText] = useState('')
  const [title, setTitle] = useState('')
  const [instructions, setInstructions] = useState('')

  const { data: documents } = useQuery({ queryKey: ['documents'], queryFn: listDocuments })
  const usableDocuments = documents?.filter((d) => DOCUMENT_SOURCE_STATUSES.has(d.status)) ?? []

  const { data: presentations } = useQuery({
    queryKey: ['presentations'],
    queryFn: listPresentations,
    refetchInterval: (query) => {
      const hasInProgress = query.state.data?.some((p) => IN_PROGRESS_STATUSES.has(p.status))
      return hasInProgress ? 3000 : false
    },
  })

  const createMutation = useMutation({
    mutationFn: createPresentation,
    onSuccess: (presentation) => {
      queryClient.invalidateQueries({ queryKey: ['presentations'] })
      navigate(`/presentations/${presentation.id}`)
    },
  })

  const canSubmit =
    sourceMode === 'document' ? !!sourceDocumentId : sourceText.trim().length > 0

  const handleSubmit = () => {
    createMutation.mutate({
      source_document_id: sourceMode === 'document' ? sourceDocumentId : undefined,
      source_text: sourceMode === 'notes' ? sourceText.trim() : undefined,
      title: title.trim() || undefined,
      instructions: instructions.trim() || undefined,
    })
  }

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-semibold">Presentations</h1>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">New presentation</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <div className="flex gap-2">
            <Button
              type="button"
              variant={sourceMode === 'document' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setSourceMode('document')}
            >
              From a document
            </Button>
            <Button
              type="button"
              variant={sourceMode === 'notes' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setSourceMode('notes')}
            >
              From pasted notes
            </Button>
          </div>

          {sourceMode === 'document' ? (
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="source-document">Source document</Label>
              {usableDocuments.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No documents ready to use yet — upload one on the Documents page first.
                </p>
              ) : (
                <select
                  id="source-document"
                  className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  value={sourceDocumentId}
                  onChange={(e) => setSourceDocumentId(e.target.value)}
                >
                  <option value="">Select a document…</option>
                  {usableDocuments.map((doc) => (
                    <option key={doc.id} value={doc.id}>
                      {doc.filename}
                    </option>
                  ))}
                </select>
              )}
            </div>
          ) : (
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="source-text">Notes</Label>
              <Textarea
                id="source-text"
                className="min-h-32"
                placeholder="Paste meeting notes, a summary, or any raw content to build the deck from…"
                value={sourceText}
                onChange={(e) => setSourceText(e.target.value)}
              />
            </div>
          )}

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="title">
              Title <span className="text-muted-foreground">(optional — AI will suggest one otherwise)</span>
            </Label>
            <Input id="title" value={title} onChange={(e) => setTitle(e.target.value)} />
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="pres-instructions">
              Anything specific to focus on? <span className="text-muted-foreground">(optional)</span>
            </Label>
            <Textarea
              id="pres-instructions"
              placeholder='e.g. "keep it to 5 slides for a board meeting" or "focus on budget impact"'
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
            />
          </div>

          <div>
            <Button disabled={!canSubmit || createMutation.isPending} onClick={handleSubmit}>
              {createMutation.isPending ? 'Generating…' : 'Generate presentation'}
            </Button>
          </div>
          {createMutation.isError && (
            <p className="text-sm text-destructive">Something went wrong creating the presentation.</p>
          )}
        </CardContent>
      </Card>

      {!presentations || presentations.length === 0 ? (
        <div className="flex flex-col items-center gap-3 rounded-lg border border-dashed p-12 text-center">
          <PresentationIcon className="size-8 text-muted-foreground" />
          <p className="max-w-md text-sm text-muted-foreground">
            Generate your first presentation from a reviewed document or pasted notes above.
          </p>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {presentations.map((p) => (
            <Link key={p.id} to={`/presentations/${p.id}`}>
              <Card className="transition-colors hover:bg-muted/50">
                <CardHeader className="flex-row items-center justify-between gap-2 space-y-0">
                  <CardTitle className="text-base">{p.title || 'Untitled presentation'}</CardTitle>
                  <Badge variant={p.status === 'failed' ? 'destructive' : 'muted'}>
                    {STATUS_LABELS[p.status]}
                  </Badge>
                </CardHeader>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
