import { useState } from 'react'
import type { ChangeEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { FileText, Upload } from 'lucide-react'

import { Button, buttonVariants } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { cn } from '@/lib/utils'
import { listDocuments, uploadDocument } from '@/api/documents'
import type { DocumentStatus } from '@/types'

const STATUS_LABELS: Record<DocumentStatus, string> = {
  uploaded: 'Uploaded',
  extracting: 'Extracting…',
  extracted: 'Extracted',
  reviewing: 'Reviewing…',
  reviewed: 'Reviewed',
  failed: 'Failed',
}

const IN_PROGRESS_STATUSES = new Set<DocumentStatus>([
  'uploaded',
  'extracting',
  'extracted',
  'reviewing',
])

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
        <h1 className="text-2xl font-semibold">Documents</h1>
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
                Anything specific to focus on? <span className="text-muted-foreground">(optional)</span>
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
        <div className="flex flex-col items-center gap-3 rounded-lg border border-dashed p-12 text-center">
          <FileText className="size-8 text-muted-foreground" />
          <p className="max-w-md text-sm text-muted-foreground">
            Upload a contract, report, memo, or proposal to get an executive summary, risk flags,
            and a suggested rewrite.
          </p>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {documents.map((doc) => (
            <Link key={doc.id} to={`/documents/${doc.id}`}>
              <Card className="transition-colors hover:bg-muted/50">
                <CardHeader className="flex-row items-center justify-between gap-2 space-y-0">
                  <CardTitle className="text-base">{doc.filename}</CardTitle>
                  <Badge variant={doc.status === 'failed' ? 'destructive' : 'muted'}>
                    {STATUS_LABELS[doc.status]}
                  </Badge>
                </CardHeader>
                {doc.review && (
                  <CardContent>
                    <p className="line-clamp-2 text-sm text-muted-foreground">
                      {doc.review.executive_summary}
                    </p>
                  </CardContent>
                )}
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
