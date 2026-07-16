import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin


class ApprovalItemType(str, enum.Enum):
    email_draft = "email_draft"
    presentation_export = "presentation_export"
    document_share = "document_share"
    dummy = "dummy"  # Phase 0 proof-of-flow only; remove once a real item type exists.


class ApprovalStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class ApprovalQueueItem(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "approval_queue_items"

    item_type: Mapped[ApprovalItemType] = mapped_column(
        Enum(ApprovalItemType, name="approval_item_type"), nullable=False
    )
    reference_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    preview_text: Mapped[str] = mapped_column(Text, nullable=False)
    requested_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    status: Mapped[ApprovalStatus] = mapped_column(
        Enum(ApprovalStatus, name="approval_status"),
        nullable=False,
        default=ApprovalStatus.pending,
    )
    reviewed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Reviewer's note — required on reject (the reason), optional on approve.
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
