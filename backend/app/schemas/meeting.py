import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.meeting import ActionItemStatus, DecisionStatus, MeetingStatus
from app.schemas.email import EmailDraftRead


class ActionItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    description: str
    owner: str
    due_date: date | None
    status: ActionItemStatus
    created_at: datetime


class DecisionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    description: str
    decided_by: str
    status: DecisionStatus
    deadline: date | None
    created_at: datetime


class MeetingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    meeting_date: date
    instructions: str | None
    summary: str | None
    status: MeetingStatus
    failure_reason: str | None
    action_items: list[ActionItemRead]
    decisions: list[DecisionRead]
    email_drafts: list[EmailDraftRead]
    created_at: datetime
