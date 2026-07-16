import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { AlertTriangle, ShieldCheck, UserPlus } from 'lucide-react'

import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  createUser,
  fetchAuditLog,
  fetchSystemHealth,
  listUsers,
  updateUser,
} from '@/api/admin'
import { useAuthStore } from '@/store/authStore'
import type { User, UserRole } from '@/types'

const ROLES: UserRole[] = ['admin', 'director', 'assistant']
const TABS = ['Health', 'Users', 'Audit log'] as const
type Tab = (typeof TABS)[number]

export default function Admin() {
  const [tab, setTab] = useState<Tab>('Health')

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-start gap-3">
        <div className="mt-0.5 rounded-lg bg-primary/10 p-2 text-primary">
          <ShieldCheck className="size-5" />
        </div>
        <div>
          <h1 className="text-2xl font-semibold">Admin</h1>
          <p className="text-sm text-muted-foreground">
            Manage users, review the audit trail, and monitor system health.
          </p>
        </div>
      </div>

      <div className="flex gap-1 rounded-lg bg-muted p-1 self-start">
        {TABS.map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            className={cn(
              'rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
              tab === t
                ? 'bg-background text-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground'
            )}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === 'Health' && <HealthTab />}
      {tab === 'Users' && <UsersTab />}
      {tab === 'Audit log' && <AuditTab />}
    </div>
  )
}

function HealthTab() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['admin', 'health'],
    queryFn: fetchSystemHealth,
    refetchInterval: 30000,
  })

  if (isLoading) return <p className="text-sm text-muted-foreground">Loading system health…</p>
  if (isError || !data)
    return <p className="text-sm text-destructive">Could not load system health.</p>

  const failedTotal = data.failed_documents + data.failed_meetings + data.failed_presentations

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Stat label="Users" value={`${data.active_users}/${data.total_users}`} hint="active/total" />
        <Stat label="Failed docs" value={data.failed_documents} danger={data.failed_documents > 0} />
        <Stat
          label="Failed meetings"
          value={data.failed_meetings}
          danger={data.failed_meetings > 0}
        />
        <Stat
          label="Failed slides"
          value={data.failed_presentations}
          danger={data.failed_presentations > 0}
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Connected accounts</CardTitle>
        </CardHeader>
        <CardContent>
          {data.connected_accounts.length === 0 ? (
            <p className="text-sm text-muted-foreground">No email/calendar accounts connected.</p>
          ) : (
            <ul className="flex flex-col gap-2">
              {data.connected_accounts.map((a) => (
                <li key={a.email_address} className="flex items-center justify-between text-sm">
                  <span>
                    {a.email_address}{' '}
                    <span className="text-xs uppercase text-muted-foreground">{a.provider}</span>
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {a.last_synced_at
                      ? `synced ${new Date(a.last_synced_at).toLocaleString()}`
                      : 'never synced'}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <AlertTriangle
              className={cn('size-4', failedTotal > 0 ? 'text-amber-500' : 'text-muted-foreground')}
            />
            Recent job failures
          </CardTitle>
        </CardHeader>
        <CardContent>
          {data.recent_job_failures.length === 0 ? (
            <p className="text-sm text-muted-foreground">No background job failures logged. 🎉</p>
          ) : (
            <ul className="flex flex-col gap-2">
              {data.recent_job_failures.map((f) => (
                <li key={f.id} className="text-sm">
                  <span className="font-medium">{f.target_type}</span>{' '}
                  <span className="text-muted-foreground">— {f.detail}</span>
                  <span className="block text-[11px] text-muted-foreground">
                    {new Date(f.created_at).toLocaleString()}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

function Stat({
  label,
  value,
  hint,
  danger,
}: {
  label: string
  value: string | number
  hint?: string
  danger?: boolean
}) {
  return (
    <Card>
      <CardContent className="py-4">
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className={cn('text-2xl font-semibold', danger && 'text-destructive')}>{value}</p>
        {hint && <p className="text-[11px] text-muted-foreground">{hint}</p>}
      </CardContent>
    </Card>
  )
}

function UsersTab() {
  const queryClient = useQueryClient()
  const currentUser = useAuthStore((s) => s.user)
  const { data: users, isLoading } = useQuery({ queryKey: ['admin', 'users'], queryFn: listUsers })

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['admin', 'users'] })
  const updateMutation = useMutation({ mutationFn: ({ id, ...p }: { id: string } & Parameters<typeof updateUser>[1]) => updateUser(id, p), onSuccess: invalidate })

  const [form, setForm] = useState({ email: '', full_name: '', password: '', role: 'assistant' as UserRole })
  const [formError, setFormError] = useState<string | null>(null)
  const createMutation = useMutation({
    mutationFn: createUser,
    onSuccess: () => {
      setForm({ email: '', full_name: '', password: '', role: 'assistant' })
      setFormError(null)
      invalidate()
    },
    onError: (e: unknown) => {
      const detail =
        (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        'Could not create user.'
      setFormError(detail)
    },
  })

  if (isLoading) return <p className="text-sm text-muted-foreground">Loading users…</p>

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-2">
        {users?.map((u) => (
          <UserRow
            key={u.id}
            user={u}
            isSelf={u.id === currentUser?.id}
            disabled={updateMutation.isPending}
            onRole={(role) => updateMutation.mutate({ id: u.id, role })}
            onToggleActive={() => updateMutation.mutate({ id: u.id, is_active: !u.is_active })}
          />
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <UserPlus className="size-4" />
            Add a user
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form
            className="flex flex-col gap-3"
            onSubmit={(e) => {
              e.preventDefault()
              createMutation.mutate(form)
            }}
          >
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="nu-name">Full name</Label>
                <Input
                  id="nu-name"
                  value={form.full_name}
                  onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))}
                  required
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="nu-email">Email</Label>
                <Input
                  id="nu-email"
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                  required
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="nu-pass">Temporary password</Label>
                <Input
                  id="nu-pass"
                  type="text"
                  value={form.password}
                  onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
                  minLength={8}
                  required
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="nu-role">Role</Label>
                <select
                  id="nu-role"
                  value={form.role}
                  onChange={(e) => setForm((f) => ({ ...f, role: e.target.value as UserRole }))}
                  className="h-9 rounded-md border border-input bg-background px-3 text-sm"
                >
                  {ROLES.map((r) => (
                    <option key={r} value={r}>
                      {r}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            {formError && <p className="text-xs text-destructive">{formError}</p>}
            <Button type="submit" size="sm" disabled={createMutation.isPending} className="self-start">
              {createMutation.isPending ? 'Creating…' : 'Create user'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}

function UserRow({
  user,
  isSelf,
  disabled,
  onRole,
  onToggleActive,
}: {
  user: User
  isSelf: boolean
  disabled: boolean
  onRole: (role: UserRole) => void
  onToggleActive: () => void
}) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border bg-card px-3 py-3">
      <div className="min-w-0">
        <p className="truncate text-sm font-medium">
          {user.full_name} {isSelf && <span className="text-xs text-muted-foreground">(you)</span>}
        </p>
        <p className="truncate text-xs text-muted-foreground">{user.email}</p>
      </div>
      <div className="flex items-center gap-2">
        <select
          value={user.role}
          disabled={disabled || isSelf}
          onChange={(e) => onRole(e.target.value as UserRole)}
          className="h-8 rounded-md border border-input bg-background px-2 text-xs disabled:opacity-60"
        >
          {ROLES.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>
        <Button
          size="sm"
          variant={user.is_active ? 'outline' : 'default'}
          disabled={disabled || isSelf}
          onClick={onToggleActive}
        >
          {user.is_active ? 'Deactivate' : 'Activate'}
        </Button>
      </div>
    </div>
  )
}

function AuditTab() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['admin', 'audit'],
    queryFn: () => fetchAuditLog(150),
  })

  if (isLoading) return <p className="text-sm text-muted-foreground">Loading audit log…</p>
  if (isError || !data)
    return <p className="text-sm text-destructive">Could not load the audit log.</p>
  if (data.length === 0)
    return <p className="text-sm text-muted-foreground">No audit entries yet.</p>

  return (
    <div className="flex flex-col divide-y rounded-lg border bg-card">
      {data.map((e) => (
        <div key={e.id} className="flex flex-col gap-0.5 px-3 py-2.5 text-sm">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded bg-muted px-1.5 py-0.5 font-mono text-[11px]">{e.action}</span>
            <span className="text-xs text-muted-foreground">{e.actor_email ?? 'system'}</span>
            <span className="ml-auto text-[11px] text-muted-foreground">
              {new Date(e.created_at).toLocaleString()}
            </span>
          </div>
          {e.detail && <p className="text-xs text-muted-foreground">{e.detail}</p>}
        </div>
      ))}
    </div>
  )
}
