import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Sparkles, X } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { getEmailDraft, updateEmailDraft } from '@/api/email'

const fieldLabel = 'text-xs font-medium uppercase tracking-wide text-muted-foreground'

interface Props {
  draftId: string
  onClose: () => void
}

/** Modal for reviewing / editing an email draft before it's approved and sent. */
export default function EmailDraftEditor({ draftId, onClose }: Props) {
  const queryClient = useQueryClient()
  const { data: draft, isLoading, isError } = useQuery({
    queryKey: ['draft', draftId],
    queryFn: () => getEmailDraft(draftId),
  })

  const [to, setTo] = useState('')
  const [cc, setCc] = useState('')
  const [subject, setSubject] = useState('')
  const [body, setBody] = useState('')
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    if (draft && !loaded) {
      setTo(draft.to_addresses.join(', '))
      setCc(draft.cc_addresses.join(', '))
      setSubject(draft.subject)
      setBody(draft.body)
      setLoaded(true)
    }
  }, [draft, loaded])

  const saveMutation = useMutation({
    mutationFn: () =>
      updateEmailDraft(draftId, {
        to_addresses: splitAddresses(to),
        cc_addresses: splitAddresses(cc),
        subject,
        body,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['draft', draftId] })
      queryClient.invalidateQueries({ queryKey: ['approvals'] })
      onClose()
    },
  })

  const editable = draft?.status === 'pending_approval'

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 p-0 sm:items-center sm:p-4"
      onMouseDown={onClose}
    >
      <div
        className="flex max-h-[90vh] w-full max-w-lg flex-col overflow-hidden rounded-t-2xl border bg-card shadow-xl sm:rounded-2xl"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b px-4 py-3">
          <h2 className="text-base font-semibold">Review email draft</h2>
          <button type="button" onClick={onClose} aria-label="Close" className="rounded-md p-1 hover:bg-muted">
            <X className="size-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-4 py-4">
          {isLoading && <p className="text-sm text-muted-foreground">Loading draft…</p>}
          {isError && <p className="text-sm text-destructive">Could not load this draft.</p>}
          {draft && (
            <div className="flex flex-col gap-3">
              {!editable && (
                <p className="rounded-md bg-muted px-3 py-2 text-xs text-muted-foreground">
                  This draft is {draft.status.replace('_', ' ')} and can no longer be edited.
                </p>
              )}
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="draft-to" className={fieldLabel}>
                  To
                </Label>
                <Input
                  id="draft-to"
                  className="bg-muted/40"
                  value={to}
                  onChange={(e) => setTo(e.target.value)}
                  disabled={!editable}
                  placeholder="comma-separated emails"
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="draft-cc" className={fieldLabel}>
                  Cc
                </Label>
                <Input
                  id="draft-cc"
                  className="bg-muted/40"
                  value={cc}
                  onChange={(e) => setCc(e.target.value)}
                  disabled={!editable}
                  placeholder="Add Cc recipients"
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="draft-subject" className={fieldLabel}>
                  Subject
                </Label>
                <Input
                  id="draft-subject"
                  className="bg-muted/40"
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  disabled={!editable}
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <div className="flex items-center justify-between">
                  <Label htmlFor="draft-body" className={fieldLabel}>
                    Body
                  </Label>
                  <span className="flex items-center gap-1 rounded-full bg-primary/10 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-primary">
                    <Sparkles className="size-3" /> AI assisted
                  </span>
                </div>
                <Textarea
                  id="draft-body"
                  className="min-h-48 bg-muted/40"
                  value={body}
                  onChange={(e) => setBody(e.target.value)}
                  disabled={!editable}
                />
              </div>
            </div>
          )}
        </div>

        <div className="flex justify-end gap-2 border-t px-4 py-3">
          <Button variant="outline" size="sm" onClick={onClose}>
            Close
          </Button>
          {editable && (
            <Button
              size="sm"
              disabled={saveMutation.isPending}
              onClick={() => saveMutation.mutate()}
            >
              {saveMutation.isPending ? 'Saving…' : 'Save changes'}
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}

function splitAddresses(value: string): string[] {
  return value
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
}
