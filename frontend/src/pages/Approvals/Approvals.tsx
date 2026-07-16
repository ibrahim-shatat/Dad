import ApprovalQueueList from '@/components/ApprovalQueue/ApprovalQueueList'

export default function Approvals() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold">Approval queue</h1>
        <p className="text-sm text-muted-foreground">
          Nothing here is sent or finalized until you approve it. Edit email drafts before
          approving, and browse the full approval history below.
        </p>
      </div>
      <ApprovalQueueList />
    </div>
  )
}
