import uuid
from datetime import date
from typing import Literal

from pydantic import BaseModel

from app.schemas.approval import ApprovalQueueItemRead


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
