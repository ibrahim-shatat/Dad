import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import { Mail, RefreshCw } from 'lucide-react'

import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import {
  draftReply,
  getGmailAuthorizationUrl,
  getOutlookAuthorizationUrl,
  listEmailAccounts,
  listEmailMessages,
  syncAccount,
} from '@/api/email'
import type { EmailMessageItem, EmailUrgency } from '@/types'

const PROVIDER_LABELS: Record<string, string> = { gmail: 'Gmail', outlook: 'Outlook' }

const URGENCY_STYLE: Record<EmailUrgency, string> = {
  high: 'bg-red-500 text-white',
  medium: 'bg-amber-500 text-white',
  low: 'bg-muted text-muted-foreground',
}

function UrgencyPill({ urgency }: { urgency: EmailUrgency }) {
  return (
    <span
      className={cn(
        'rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide',
        URGENCY_STYLE[urgency]
      )}
    >
      {urgency} urgency
    </span>
  )
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

  const unreadCount = messages?.filter((m) => m.is_unread).length ?? 0

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Email</h1>
          <p className="text-sm text-muted-foreground">
            AI summaries and urgency flags. Replies wait for your approval.
          </p>
        </div>
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
        <Card className="border-green-500/40 bg-green-500/5">
          <CardContent className="flex items-center justify-between pt-6 text-sm">
            <p>{PROVIDER_LABELS[connectedProvider] ?? connectedProvider} connected successfully.</p>
            <Button size="sm" variant="ghost" onClick={dismissBanner}>
              Dismiss
            </Button>
          </CardContent>
        </Card>
      )}

      {!accounts || accounts.length === 0 ? (
        <div className="flex flex-col items-center gap-3 rounded-xl border border-dashed p-12 text-center">
          <div className="flex size-12 items-center justify-center rounded-full bg-muted text-muted-foreground">
            <Mail className="size-6" />
          </div>
          <p className="max-w-md text-sm text-muted-foreground">
            Connect Gmail or Outlook to get inbox summaries, urgency detection, and drafted replies
            — nothing sends without your approval.
          </p>
        </div>
      ) : (
        <>
          <div className="flex flex-col gap-3">
            {accounts.map((account) => (
              <Card key={account.id} className="flex items-center justify-between gap-3 p-4">
                <div className="flex min-w-0 items-center gap-3">
                  <div className="flex size-10 flex-none items-center justify-center rounded-lg bg-primary/10 text-primary">
                    <Mail className="size-5" />
                  </div>
                  <div className="min-w-0">
                    <p className="truncate font-semibold">{account.email_address}</p>
                    <p className="text-xs text-muted-foreground">
                      {PROVIDER_LABELS[account.provider]}
                      {account.last_synced_at
                        ? ` · synced ${new Date(account.last_synced_at).toLocaleString()}`
                        : ' · not yet synced'}
                    </p>
                  </div>
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  disabled={syncMutation.isPending}
                  onClick={() => syncMutation.mutate(account.id)}
                >
                  <RefreshCw className={cn('size-4', syncMutation.isPending && 'animate-spin')} />
                  Sync
                </Button>
              </Card>
            ))}
          </div>

          <div className="flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-semibold uppercase tracking-wide text-muted-foreground">
                Inbox feed
              </h2>
              {unreadCount > 0 && (
                <span className="text-xs font-medium text-primary">{unreadCount} unread</span>
              )}
            </div>
            {!messages || messages.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No messages synced yet — try "Sync" above.
              </p>
            ) : (
              <div className="flex flex-col gap-3">
                {messages.map((message) => (
                  <MessageCard
                    key={message.id}
                    message={message}
                    isReplying={replyingTo === message.id}
                    isQueued={queuedMessageIds.has(message.id)}
                    instructions={instructions}
                    setInstructions={setInstructions}
                    isPending={draftReplyMutation.isPending}
                    onStartReply={() => setReplyingTo(message.id)}
                    onCancelReply={() => setReplyingTo(null)}
                    onGenerate={() =>
                      draftReplyMutation.mutate({ messageId: message.id, text: instructions })
                    }
                  />
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}

interface MessageCardProps {
  message: EmailMessageItem
  isReplying: boolean
  isQueued: boolean
  instructions: string
  setInstructions: (v: string) => void
  isPending: boolean
  onStartReply: () => void
  onCancelReply: () => void
  onGenerate: () => void
}

function MessageCard({
  message,
  isReplying,
  isQueued,
  instructions,
  setInstructions,
  isPending,
  onStartReply,
  onCancelReply,
  onGenerate,
}: MessageCardProps) {
  const high = message.ai_urgency === 'high'
  return (
    <Card className={cn('p-4', high && 'border-red-500/30 bg-red-500/5')}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          {message.ai_urgency && <UrgencyPill urgency={message.ai_urgency} />}
          {message.is_unread && <span className="size-2 rounded-full bg-primary" />}
        </div>
        <span className="flex-none text-xs text-muted-foreground">
          {new Date(message.received_at).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </span>
      </div>
      <p className="mt-2 font-semibold leading-tight">{message.sender}</p>
      <p className="font-medium">{message.subject}</p>
      <p className="mt-1 text-sm text-muted-foreground">{message.ai_summary ?? message.snippet}</p>

      <div className="mt-3">
        {isReplying ? (
          <div className="flex flex-col gap-2">
            <Textarea
              placeholder='Optional instructions, e.g. "decline politely" or "confirm Tuesday works"'
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
            />
            <div className="flex gap-2">
              <Button size="sm" disabled={isPending} onClick={onGenerate}>
                Generate draft
              </Button>
              <Button size="sm" variant="outline" onClick={onCancelReply}>
                Cancel
              </Button>
            </div>
          </div>
        ) : isQueued ? (
          <p className="text-sm text-muted-foreground">
            Draft requested — check the Approvals page shortly.
          </p>
        ) : (
          <Button size="sm" variant="outline" onClick={onStartReply}>
            Draft reply
          </Button>
        )}
      </div>
    </Card>
  )
}
