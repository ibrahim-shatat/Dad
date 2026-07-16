import uuid
from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin


class Briefing(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """One executive daily briefing per (user, date). The summary/priorities are Claude-written
    snapshots generated on demand; the actionable item list is recomputed live each request, with
    per-item 'handled' state persisted here as a set of stable item keys."""

    __tablename__ = "briefings"
    __table_args__ = (UniqueConstraint("user_id", "briefing_date", name="uq_briefing_user_date"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    briefing_date: Mapped[date] = mapped_column(Date, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    top_priorities: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    handled_keys: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
