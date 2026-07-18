import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel

from app.schemas.approval import ApprovalQueueItemRead


class AttentionItem(BaseModel):
    """One prioritized thing the director should look at now. The backend ranks and orders these
    across emails, approvals, deadlines, and meetings so the dashboard can render a single
    'here's what needs you' feed without the client re-deriving priority."""

    kind: Literal[
        "email", "approval", "deadline", "event", "task", "document", "presentation"
    ]
    title: str
    subtitle: str
    badge: str
    tone: Literal["urgent", "warning", "default"]
    link: str
    when: datetime | None = None


class UpcomingDeadlineRead(BaseModel):
    type: Literal["action_item", "decision"]
    id: uuid.UUID
    description: str
    owner: str
    due_date: date
    meeting_id: uuid.UUID
    meeting_title: str


class DashboardSummary(BaseModel):
    pending_approvals: list[ApprovalQueueItemRead]
    documents_awaiting_review: int = 0
    presentations_in_progress: int = 0
    open_action_items: int = 0
    upcoming_deadlines: list[UpcomingDeadlineRead] = []
    unread_urgent_emails: int = 0
    needs_attention: list[AttentionItem] = []
    needs_work: list[AttentionItem] = []
