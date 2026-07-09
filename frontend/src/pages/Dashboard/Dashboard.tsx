import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import ApprovalQueueList from '@/components/ApprovalQueue/ApprovalQueueList'
import { fetchDashboard } from '@/api/dashboard'

const STAT_CARDS = [
  { key: 'documents_awaiting_review', label: 'Documents awaiting review' },
  { key: 'presentations_in_progress', label: 'Presentations in progress' },
  { key: 'open_action_items', label: 'Open action items' },
  { key: 'unread_urgent_emails', label: 'Unread urgent emails' },
] as const

export default function Dashboard() {
  const { data } = useQuery({ queryKey: ['dashboard'], queryFn: fetchDashboard })

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-semibold">Dashboard</h1>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {STAT_CARDS.map(({ key, label }) => (
          <Card key={key}>
            <CardHeader className="pb-2">
              <CardTitle className="text-3xl">{data?.[key] ?? '—'}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">{label}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div>
        <h2 className="mb-3 text-lg font-semibold">Pending approvals</h2>
        <ApprovalQueueList limit={5} />
      </div>

      <div>
        <h2 className="mb-3 text-lg font-semibold">Upcoming deadlines</h2>
        {!data || data.upcoming_deadlines.length === 0 ? (
          <p className="text-sm text-muted-foreground">Nothing due soon.</p>
        ) : (
          <div className="flex flex-col gap-3">
            {data.upcoming_deadlines.map((d) => (
              <Link key={d.id} to={`/meetings/${d.meeting_id}`}>
                <Card className="transition-colors hover:bg-muted/50">
                  <CardContent className="flex items-center justify-between gap-3 pt-6 text-sm">
                    <div>
                      <p>{d.description}</p>
                      <p className="text-xs text-muted-foreground">
                        {d.owner} · {d.meeting_title} · {d.type === 'decision' ? 'decision' : 'action item'}
                      </p>
                    </div>
                    <p className="text-xs font-medium text-muted-foreground">{d.due_date}</p>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
