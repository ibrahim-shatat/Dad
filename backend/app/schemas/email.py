import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.email import EmailDraftStatus, EmailProvider, EmailUrgency


class EmailAccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    provider: EmailProvider
    email_address: str
    last_synced_at: datetime | None
    created_at: datetime


class EmailMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    provider_message_id: str
    thread_id: str | None
    sender: str
    subject: str
    snippet: str
    received_at: datetime
    is_unread: bool
    is_hidden: bool
    ai_urgency: EmailUrgency | None
    ai_summary: str | None


class EmailDraftUpdate(BaseModel):
    to_addresses: list[str] | None = None
    cc_addresses: list[str] | None = None
    subject: str | None = Field(default=None, max_length=255)
    body: str | None = None


class EmailDraftRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_meeting_id: uuid.UUID | None
    account_id: uuid.UUID | None
    source_message_id: uuid.UUID | None
    to_addresses: list[str]
    cc_addresses: list[str]
    subject: str
    body: str
    status: EmailDraftStatus
    sent_at: datetime | None
    created_at: datetime
