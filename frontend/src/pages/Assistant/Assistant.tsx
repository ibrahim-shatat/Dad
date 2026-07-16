import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'
import {
  CalendarClock,
  ClipboardCheck,
  FileText,
  Mail,
  Search as SearchIcon,
  Send,
  Sparkles,
  Presentation as PresentationIcon,
  CalendarCheck,
} from 'lucide-react'

import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { askAssistant, searchWorkspace } from '@/api/search'
import type { ChatSource, SearchResult, SearchResultType } from '@/types'

const TYPE_META: Record<SearchResultType, { label: string; icon: typeof FileText }> = {
  document: { label: 'Document', icon: FileText },
  meeting: { label: 'Meeting', icon: CalendarCheck },
  email: { label: 'Email', icon: Mail },
  presentation: { label: 'Presentation', icon: PresentationIcon },
  event: { label: 'Event', icon: CalendarClock },
  approval: { label: 'Approval', icon: ClipboardCheck },
}

const SUGGESTIONS = [
  'What needs my approval today?',
  'Summarize my open action items',
  "What's on my calendar this week?",
  'Any urgent emails I should know about?',
]

interface ChatMessage {
  role: 'user' | 'assistant'
  text: string
  sources?: ChatSource[]
}

export default function Assistant() {
  const navigate = useNavigate()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const scrollRef = useRef<HTMLDivElement>(null)

  const chatMutation = useMutation({
    mutationFn: askAssistant,
    onSuccess: (res) =>
      setMessages((m) => [...m, { role: 'assistant', text: res.answer, sources: res.sources }]),
    onError: () =>
      setMessages((m) => [
        ...m,
        { role: 'assistant', text: 'Sorry — I could not answer that right now. Please try again.' },
      ]),
  })

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, chatMutation.isPending])

  const send = (question: string) => {
    const q = question.trim()
    if (!q || chatMutation.isPending) return
    setMessages((m) => [...m, { role: 'user', text: q }])
    setInput('')
    chatMutation.mutate(q)
  }

  // --- Search (debounced) ---
  const [rawQuery, setRawQuery] = useState('')
  const [query, setQuery] = useState('')
  useEffect(() => {
    const t = setTimeout(() => setQuery(rawQuery), 300)
    return () => clearTimeout(t)
  }, [rawQuery])

  const { data: results, isFetching } = useQuery({
    queryKey: ['search', query],
    queryFn: () => searchWorkspace(query),
    enabled: query.trim().length >= 2,
  })

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold">Assistant</h1>
        <p className="text-sm text-muted-foreground">
          Ask about your workspace, or search across everything.
        </p>
      </div>

      {/* Chat */}
      <Card>
        <CardContent className="flex flex-col gap-3 py-4">
          <div ref={scrollRef} className="flex max-h-[24rem] flex-col gap-3 overflow-y-auto">
            {messages.length === 0 ? (
              <div className="flex flex-col gap-3 py-4">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Sparkles className="size-4 text-primary" />
                  Ask me anything about your work. Try:
                </div>
                <div className="flex flex-wrap gap-2">
                  {SUGGESTIONS.map((s) => (
                    <button
                      key={s}
                      type="button"
                      onClick={() => send(s)}
                      className="rounded-full border px-3 py-1.5 text-xs font-medium text-foreground transition-colors hover:bg-muted"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((m, i) => (
                <div
                  key={i}
                  className={cn('flex', m.role === 'user' ? 'justify-end' : 'justify-start')}
                >
                  <div
                    className={cn(
                      'max-w-[85%] rounded-2xl px-3.5 py-2.5 text-sm',
                      m.role === 'user'
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted text-foreground'
                    )}
                  >
                    <p className="whitespace-pre-wrap leading-relaxed">{m.text}</p>
                    {m.sources && m.sources.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1.5">
                        {m.sources.map((s, j) => (
                          <button
                            key={j}
                            type="button"
                            onClick={() => navigate(s.link)}
                            className="rounded-full bg-background/70 px-2 py-0.5 text-[11px] font-medium text-foreground hover:underline"
                          >
                            {s.label}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
            {chatMutation.isPending && (
              <div className="flex justify-start">
                <div className="rounded-2xl bg-muted px-3.5 py-2.5 text-sm text-muted-foreground">
                  Thinking…
                </div>
              </div>
            )}
          </div>

          <form
            onSubmit={(e) => {
              e.preventDefault()
              send(input)
            }}
            className="flex gap-2"
          >
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about approvals, tasks, meetings…"
              disabled={chatMutation.isPending}
            />
            <Button type="submit" size="sm" disabled={chatMutation.isPending || !input.trim()}>
              <Send className="size-4" />
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Search */}
      <div className="flex flex-col gap-3">
        <div className="relative">
          <SearchIcon className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={rawQuery}
            onChange={(e) => setRawQuery(e.target.value)}
            placeholder="Search documents, meetings, emails, presentations…"
            className="pl-9"
          />
        </div>

        {query.trim().length >= 2 && (
          <div className="flex flex-col gap-2">
            {isFetching && !results ? (
              <p className="text-sm text-muted-foreground">Searching…</p>
            ) : !results || results.length === 0 ? (
              <p className="text-sm text-muted-foreground">No matches for “{query}”.</p>
            ) : (
              results.map((r) => <SearchRow key={`${r.type}-${r.id}`} result={r} />)
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function SearchRow({ result }: { result: SearchResult }) {
  const navigate = useNavigate()
  const meta = TYPE_META[result.type]
  const Icon = meta.icon
  return (
    <button
      type="button"
      onClick={() => navigate(result.link)}
      className="flex items-start gap-3 rounded-lg border bg-card px-3 py-3 text-left transition-colors hover:bg-muted/50"
    >
      <div className="mt-0.5 rounded-md bg-muted p-1.5 text-muted-foreground">
        <Icon className="size-4" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
            {meta.label}
          </span>
        </div>
        <p className="truncate text-sm font-medium">{result.title}</p>
        {result.snippet && (
          <p className="truncate text-xs text-muted-foreground">{result.snippet}</p>
        )}
      </div>
    </button>
  )
}
