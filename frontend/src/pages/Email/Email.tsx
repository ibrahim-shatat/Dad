import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import { Mail, RefreshCw } from 'lucide-react'

import { Badge, type BadgeProps } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import {
  draftReply,
  getGmailAuthorizationUrl,
  getOutlookAuthorizationUrl,
  listEmailAccounts,
  listEmailMessages,
  syncAccount,
} from '@/api/email'
import type { EmailUrgency } from '@/types'

const URGENCY_VARIANT: Record<EmailUrgency, BadgeProps['variant']> = {
  high: 'destructive',
  medium: 'default',
  low: 'muted',
}

const PROVIDER_LABELS: Record<string, string> = {
  gmail: 'Gmail',
  outlook: 'Outlook',
}

export default function Email() {
  const [searchParams, setSearchParams] = useSearchParams()
  const connectedProvider = searchParams.get('connected')
  const queryClient = useQueryClient()
  const [replyingTo, setReplyingTo] = useState<string | null>(null)
  const [instructions, setInstructions] = useState('')
  const [queuedMessageIds, setQueuedMessageIds] = useState<Set<string>>(new Set())

  const { data: accounts } = useQuery({ queryKey: ['email-accounts'], queryFn: listEmailAccounts })
  const { data: messages } = useQuery({
    queryKey: ['email-messages'],
    queryFn: () => listEmailMessages(),
    refetchInterval: 20000,
  })

  const connectGmail = useMutation({
    mutationFn: getGmailAuthorizationUrl,
    onSuccess: (url) => {
      window.location.href = url
    },
  })
  const connectOutlook = useMutation({
    mutationFn: getOutlookAuthorizationUrl,
    onSuccess: (url) => {
      window.location.href = url
    },
  })
  const syncMutation = useMutation({
    mutationFn: syncAccount,
    onSuccess: () => {
      setTimeout(() => queryClient.invalidateQueries({ queryKey: ['email-messages'] }), 3000)
    },
  })
  const draftReplyMutation = useMutation({
    mutationFn: ({ messageId, text }: { messageId: string; text: string }) =>
      draftReply(messageId, text || undefined),
    onSuccess: (_data, variables) => {
      setQueuedMessageIds((prev) => new Set(prev).add(variables.messageId))
      setReplyingTo(null)
      setInstructions('')
    },
  })

  const dismissBanner = () => {
    searchParams.delete('connected')
    setSearchParams(searchParams, { replace: true })
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-2xl font-semibold">Email</h1>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" disabled={connectGmail.isPending} onClick={() => connectGmail.mutate()}>
            Connect Gmail
          </Button>
          <Button variant="outline" disabled={connectOutlook.isPending} onClick={() => connectOutlook.mutate()}>
            Connect Outlook
          </Button>
        </div>
      </div>

      {connectedProvider && (
        <Card className="border-emerald-500/50 bg-emerald-500/5">
          <CardContent className="flex items-center justify-between pt-6 text-sm">
            <p>{PROVIDER_LABELS[connectedProvider] ?? connectedProvider} connected successfully.</p>
            <Button size="sm" variant="ghost" onClick={dismissBanner}>
              Dismiss
            </Button>
          </CardContent>
        </Card>
      )}

      {!accounts || accounts.length === 0 ? (
        <div className="flex flex-col items-center gap-3 rounded-lg border border-dashed p-12 text-center">
          <Mail className="size-8 text-muted-foreground" />
          <p className="max-w-md text-sm text-muted-foreground">
            Connect Gmail or Outlook to get inbox summaries, urgency detection, and drafted
            replies — nothing sends without your approval.
          </p>
        </div>
      ) : (
        <>
          <div className="flex flex-col gap-3">
            {accounts.map((account) => (
              <Card key={account.id}>
                <CardHeader className="flex-row items-center justify-between gap-2 space-y-0">
                  <div>
                    <CardTitle className="text-base">{account.email_address}</CardTitle>
                    <p className="text-xs text-muted-foreground">
                      {PROVIDER_LABELS[account.provider]}
                      {account.last_synced_at
                        ? ` · last synced ${new Date(account.last_synced_at).toLocaleString()}`
                        : ' · not yet synced'}
                    </p>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={syncMutation.isPending}
                    onClick={() => syncMutation.mutate(account.id)}
                  >
                    <RefreshCw className="size-4" />
                    Sync now
                  </Button>
                </CardHeader>
              </Card>
            ))}
          </div>

          <div>
            <h2 className="mb-3 text-lg font-semibold">Inbox</h2>
            {!messages || messages.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No messages synced yet — try "Sync now" above.
              </p>
            ) : (
              <div className="flex flex-col gap-3">
                {messages.map((message) => (
                  <Card key={message.id}>
                    <CardHeader className="flex-row items-center justify-between gap-2 space-y-0">
                      <div>
                        <CardTitle className="text-base">
                          {message.is_unread && <span className="mr-1.5 text-primary">●</span>}
                          {message.subject}
                        </CardTitle>
                        <p className="text-xs text-muted-foreground">
                          {message.sender} · {new Date(message.received_at).toLocaleString()}
                        </p>
                      </div>
                      {message.ai_urgency && (
                        <Badge variant={URGENCY_VARIANT[message.ai_urgency]}>
                          {message.ai_urgency}
                        </Badge>
                      )}
                    </CardHeader>
                    <CardContent className="flex flex-col gap-3">
                      <p className="text-sm text-muted-foreground">
                        {message.ai_summary ?? message.snippet}
                      </p>

                      {replyingTo === message.id ? (
                        <div className="flex flex-col gap-2">
                          <Textarea
                            placeholder='Optional instructions, e.g. "decline politely" or "confirm Tuesday works"'
                            value={instructions}
                            onChange={(e) => setInstructions(e.target.value)}
                          />
                          <div className="flex gap-2">
                            <Button
                              size="sm"
                              disabled={draftReplyMutation.isPending}
                              onClick={() =>
                                draftReplyMutation.mutate({ messageId: message.id, text: instructions })
                              }
                            >
                              Generate draft
                            </Button>
                            <Button size="sm" variant="outline" onClick={() => setReplyingTo(null)}>
                              Cancel
                            </Button>
                          </div>
                        </div>
                      ) : queuedMessageIds.has(message.id) ? (
                        <p className="text-sm text-muted-foreground">
                          Draft requested — check the Approvals page shortly.
                        </p>
                      ) : (
                        <div>
                          <Button size="sm" variant="outline" onClick={() => setReplyingTo(message.id)}>
                            Draft reply
                          </Button>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}
