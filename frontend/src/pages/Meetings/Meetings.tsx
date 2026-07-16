import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate, Link } from 'react-router-dom'
import { CalendarCheck } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { createMeeting, listMeetings } from '@/api/meetings'
import type { MeetingStatus } from '@/types'

const STATUS_LABELS: Record<MeetingStatus, string> = {
  processing: 'Processing…',
  processed: 'Processed',
  failed: 'Failed',
}

export default function Meetings() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [title, setTitle] = useState('')
  const [meetingDate, setMeetingDate] = useState('')
  const [sourceText, setSourceText] = useState('')
  const [instructions, setInstructions] = useState('')

  const { data: meetings } = useQuery({
    queryKey: ['meetings'],
    queryFn: listMeetings,
    refetchInterval: (query) => {
      const hasInProgress = query.state.data?.some((m) => m.status === 'processing')
      return hasInProgress ? 3000 : false
    },
  })

  const createMutation = useMutation({
    mutationFn: createMeeting,
    onSuccess: (meeting) => {
      queryClient.invalidateQueries({ queryKey: ['meetings'] })
      navigate(`/meetings/${meeting.id}`)
    },
  })

  const canSubmit = title.trim().length > 0 && sourceText.trim().length > 0

  const handleSubmit = () => {
    createMutation.mutate({
      title: title.trim(),
      source_text: sourceText.trim(),
      meeting_date: meetingDate || undefined,
      instructions: instructions.trim() || undefined,
    })
  }

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-semibold">Meetings</h1>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">New meeting</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <div className="flex flex-col gap-4 sm:flex-row">
            <div className="flex flex-1 flex-col gap-1.5">
              <Label htmlFor="meeting-title">Title</Label>
              <Input id="meeting-title" value={title} onChange={(e) => setTitle(e.target.value)} />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="meeting-date">Date</Label>
              <Input
                id="meeting-date"
                type="date"
                value={meetingDate}
                onChange={(e) => setMeetingDate(e.target.value)}
              />
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="meeting-notes">Notes or transcript</Label>
            <Textarea
              id="meeting-notes"
              className="min-h-40"
              placeholder="Paste meeting notes or a transcript here…"
              value={sourceText}
              onChange={(e) => setSourceText(e.target.value)}
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="meeting-instructions">
              Anything specific to focus on? <span className="text-muted-foreground">(optional)</span>
            </Label>
            <Textarea
              id="meeting-instructions"
              placeholder='e.g. "only extract action items for the engineering team" or "skip the follow-up email"'
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
            />
          </div>

          <div>
            <Button disabled={!canSubmit || createMutation.isPending} onClick={handleSubmit}>
              {createMutation.isPending ? 'Processing…' : 'Process meeting'}
            </Button>
          </div>
          {createMutation.isError && (
            <p className="text-sm text-destructive">Something went wrong processing the meeting.</p>
          )}
        </CardContent>
      </Card>

      {!meetings || meetings.length === 0 ? (
        <div className="flex flex-col items-center gap-3 rounded-lg border border-dashed p-12 text-center">
          <CalendarCheck className="size-8 text-muted-foreground" />
          <p className="max-w-md text-sm text-muted-foreground">
            Paste your first meeting notes or transcript above to get a summary, action items,
            and decisions.
          </p>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {meetings.map((m) => (
            <Link key={m.id} to={`/meetings/${m.id}`}>
              <Card className="transition-colors hover:bg-muted/50">
                <CardHeader className="flex-row items-center justify-between gap-2 space-y-0">
                  <div>
                    <CardTitle className="text-base">{m.title}</CardTitle>
                    <p className="text-xs text-muted-foreground">{m.meeting_date}</p>
                  </div>
                  <Badge variant={m.status === 'failed' ? 'destructive' : 'muted'}>
                    {STATUS_LABELS[m.status]}
                  </Badge>
                </CardHeader>
                {m.summary && (
                  <CardContent>
                    <p className="line-clamp-2 text-sm text-muted-foreground">{m.summary}</p>
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
