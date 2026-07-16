import { useState } from 'react'
import type { ChangeEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Check, FileText, Loader2, Upload, X } from 'lucide-react'

import { Button, buttonVariants } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { cn } from '@/lib/utils'
import { listDocuments, uploadDocument } from '@/api/documents'
import type { DocumentItem, DocumentStatus } from '@/types'

const STATUS_LABELS: Record<DocumentStatus, string> = {
  uploaded: 'Uploaded',
  extracting: 'Extracting',
  extracted: 'Extracted',
  reviewing: 'Reviewing',
  reviewed: 'Reviewed',
  failed: 'Failed',
}

const IN_PROGRESS_STATUSES = new Set<DocumentStatus>([
  'uploaded',
  'extracting',
  'extracted',
  'reviewing',
])

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function StatusBadge({ status }: { status: DocumentStatus }) {
  if (status === 'reviewed') {
    return (
      <span className="flex items-center gap-1 rounded-full bg-green-500/10 px-2.5 py-0.5 text-[11px] font-semibold text-green-600 dark:text-green-500">
        <Check className="size-3" /> Reviewed
      </span>
    )
  }
  if (status === 'failed') {
    return (
      <span className="flex items-center gap-1 rounded-full bg-red-500/10 px-2.5 py-0.5 text-[11px] font-semibold text-red-600 dark:text-red-500">
        <X className="size-3" /> Failed
      </span>
    )
  }
  return (
    <span className="flex items-center gap-1 rounded-full bg-primary/10 px-2.5 py-0.5 text-[11px] font-semibold text-primary">
      <Loader2 className="size-3 animate-spin" /> {STATUS_LABELS[status]}
    </span>
  )
}

function DocumentCard({ doc }: { doc: DocumentItem }) {
  const inProgress = IN_PROGRESS_STATUSES.has(doc.status)
  return (
    <Link to={`/documents/${doc.id}`}>
      <Card className="flex h-full flex-col gap-3 p-4 transition-colors hover:bg-muted/40">
        <div className="flex items-start justify-between gap-2">
          <div className="flex size-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <FileText className="size-5" />
          </div>
          <StatusBadge status={doc.status} />
        </div>
        <div className="min-w-0">
          <p className="truncate font-semibold">{doc.filename}</p>
          <p className="text-xs text-muted-foreground">
            {formatSize(doc.file_size)} · {new Date(doc.created_at).toLocaleDateString()}
          </p>
        </div>
        {inProgress && (
          <div className="h-1 overflow-hidden rounded-full bg-muted">
            <div className="h-full w-2/3 animate-pulse rounded-full bg-primary" />
          </div>
        )}
        {doc.review && (
          <p className="line-clamp-2 border-l-2 border-primary/60 bg-muted/40 py-1.5 pl-2.5 text-xs italic text-muted-foreground">
            {doc.review.executive_summary}
          </p>
        )}
        {doc.status === 'failed' && doc.failure_reason && (
          <p className="line-clamp-2 text-xs text-destructive">{doc.failure_reason}</p>
        )}
      </Card>
    </Link>
  )
}

export default function Documents() {
  const queryClient = useQueryClient()
  const [pendingFile, setPendingFile] = useState<File | null>(null)
  const [instructions, setInstructions] = useState('')

  const { data: documents } = useQuery({
    queryKey: ['documents'],
    queryFn: listDocuments,
    refetchInterval: (query) => {
      const hasInProgress = query.state.data?.some((d) => IN_PROGRESS_STATUSES.has(d.status))
      return hasInProgress ? 3000 : false
    },
  })

  const uploadMutation = useMutation({
    mutationFn: () => uploadDocument(pendingFile!, instructions.trim() || undefined),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      setPendingFile(null)
      setInstructions('')
    },
  })

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      uploadMutation.reset()
      setPendingFile(file)
    }
    e.target.value = ''
  }

  const cancelPending = () => {
    setPendingFile(null)
    setInstructions('')
    uploadMutation.reset()
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Documents</h1>
          <p className="text-sm text-muted-foreground">
            Upload a contract, report, or memo for an AI review.
          </p>
        </div>
        <label className={cn(buttonVariants(), 'cursor-pointer')}>
          <Upload className="size-4" />
          Upload document
          <input
            type="file"
            className="hidden"
            accept=".pdf,.docx,.xlsx,.txt"
            onChange={handleFileChange}
          />
        </label>
      </div>

      {pendingFile && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{pendingFile.name}</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="instructions">
                Anything specific to focus on?{' '}
                <span className="text-muted-foreground">(optional)</span>
              </Label>
              <Textarea
                id="instructions"
                placeholder='e.g. "focus on payment terms" or "check this against our standard vendor policy"'
                value={instructions}
                onChange={(e) => setInstructions(e.target.value)}
                disabled={uploadMutation.isPending}
              />
            </div>
            <div className="flex gap-2">
              <Button disabled={uploadMutation.isPending} onClick={() => uploadMutation.mutate()}>
                {uploadMutation.isPending ? 'Uploading…' : 'Upload & review'}
              </Button>
              <Button variant="outline" disabled={uploadMutation.isPending} onClick={cancelPending}>
                Cancel
              </Button>
            </div>
            {uploadMutation.isError && (
              <p className="text-sm text-destructive">
                Upload failed. Only PDF, DOCX, XLSX, and plain text files are supported.
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {!documents || documents.length === 0 ? (
        <div className="flex flex-col items-center gap-3 rounded-xl border border-dashed p-12 text-center">
          <div className="flex size-12 items-center justify-center rounded-full bg-muted text-muted-foreground">
            <FileText className="size-6" />
          </div>
          <p className="max-w-md text-sm text-muted-foreground">
            No documents yet. Upload a contract, report, memo, or proposal to get an executive
            summary, risk flags, and a suggested rewrite.
          </p>
        </div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {documents.map((doc) => (
            <DocumentCard key={doc.id} doc={doc} />
          ))}
        </div>
      )}
    </div>
  )
}
