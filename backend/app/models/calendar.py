import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin


class CalendarEvent(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """An upcoming (or recent) event pulled from a connected calendar. Synced from the same
    OAuth account used for email; prep_brief is a Claude-written meeting-prep note generated on
    demand."""

    __tablename__ = "calendar_events"
    __table_args__ = (
        UniqueConstraint("account_id", "provider_event_id", name="uq_calendar_event_provider"),
    )

    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("email_accounts.id"), nullable=False, index=True
    )
    provider_event_id: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(512), nullable=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_all_day: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    organizer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    attendees: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    prep_brief: Mapped[str | None] = mapped_column(Text, nullable=True)
    prep_generated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
