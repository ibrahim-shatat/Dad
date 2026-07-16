import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin


class EmailProvider(str, enum.Enum):
    gmail = "gmail"
    outlook = "outlook"


class EmailUrgency(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class EmailDraftStatus(str, enum.Enum):
    pending_approval = "pending_approval"
    approved = "approved"
    rejected = "rejected"
    sent = "sent"


class EmailAccount(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "email_accounts"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    provider: Mapped[EmailProvider] = mapped_column(
        Enum(EmailProvider, name="email_provider"), nullable=False
    )
    email_address: Mapped[str] = mapped_column(String(255), nullable=False)
    # Encrypted at rest (see services/email/oauth.py) — never store raw tokens.
    oauth_access_token: Mapped[str] = mapped_column(Text, nullable=False)
    oauth_refresh_token: Mapped[str] = mapped_column(Text, nullable=False)
    token_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    scopes: Mapped[str] = mapped_column(Text, nullable=False)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class EmailMessage(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "email_messages"

    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("email_accounts.id"), nullable=False
    )
    provider_message_id: Mapped[str] = mapped_column(String(255), nullable=False)
    thread_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sender: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(998), nullable=False)
    snippet: Mapped[str] = mapped_column(Text, nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_unread: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # User dismissed this message from the inbox feed (hidden until unhidden).
    is_hidden: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ai_urgency: Mapped[EmailUrgency | None] = mapped_column(
        Enum(EmailUrgency, name="email_urgency"), nullable=True
    )
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)


class EmailDraft(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "email_drafts"

    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    source_meeting_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("meetings.id"), nullable=True
    )
    # account_id/source_message_id are null for meeting-sourced drafts (Phase 3), which have no
    # connected inbox to send from or reply to — approving those just unlocks "copy to clipboard".
    account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("email_accounts.id"), nullable=True
    )
    source_message_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("email_messages.id"), nullable=True
    )
    to_addresses: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    cc_addresses: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[EmailDraftStatus] = mapped_column(
        Enum(EmailDraftStatus, name="email_draft_status"),
        nullable=False,
        default=EmailDraftStatus.pending_approval,
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
