import enum
import uuid
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin


class MeetingStatus(str, enum.Enum):
    processing = "processing"
    processed = "processed"
    failed = "failed"


class ActionItemStatus(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    done = "done"


class DecisionStatus(str, enum.Enum):
    pending = "pending"
    decided = "decided"
    deferred = "deferred"


class Meeting(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "meetings"

    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    meeting_date: Mapped[date] = mapped_column(Date, nullable=False)
    source_text: Mapped[str] = mapped_column(Text, nullable=False)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[MeetingStatus] = mapped_column(
        Enum(MeetingStatus, name="meeting_status"),
        nullable=False,
        default=MeetingStatus.processing,
    )
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    action_items: Mapped[list["ActionItem"]] = relationship(
        back_populates="meeting", order_by="ActionItem.created_at", cascade="all, delete-orphan"
    )
    decisions: Mapped[list["Decision"]] = relationship(
        back_populates="meeting", order_by="Decision.created_at", cascade="all, delete-orphan"
    )
    # Read-only: EmailDraft owns the FK (source_meeting_id) and is created directly by the
    # meeting-processing job, not through this relationship — viewonly avoids needing
    # back_populates bookkeeping across the meeting/email model modules.
    email_drafts: Mapped[list["EmailDraft"]] = relationship(
        "EmailDraft",
        primaryjoin="Meeting.id == foreign(EmailDraft.source_meeting_id)",
        viewonly=True,
        order_by="EmailDraft.created_at",
    )


class ActionItem(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "action_items"

    meeting_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("meetings.id"), nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    owner: Mapped[str] = mapped_column(String(255), nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[ActionItemStatus] = mapped_column(
        Enum(ActionItemStatus, name="action_item_status"),
        nullable=False,
        default=ActionItemStatus.open,
    )

    meeting: Mapped["Meeting"] = relationship(back_populates="action_items")


class Decision(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "decisions"

    meeting_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("meetings.id"), nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    decided_by: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[DecisionStatus] = mapped_column(
        Enum(DecisionStatus, name="decision_status"),
        nullable=False,
        default=DecisionStatus.decided,
    )
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)

    meeting: Mapped["Meeting"] = relationship(back_populates="decisions")
