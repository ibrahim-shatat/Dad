import enum
import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, String, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin


class NotificationType(str, enum.Enum):
    document_reviewed = "document_reviewed"
    meeting_processed = "meeting_processed"
    approval_pending = "approval_pending"
    approval_approved = "approval_approved"
    approval_rejected = "approval_rejected"
    urgent_email = "urgent_email"


class Notification(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "notifications"

    # Recipient.
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, name="notification_type"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Frontend route to open when the notification is clicked, e.g. "/meetings/<id>".
    link: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (Index("ix_notifications_user_unread", "user_id", "is_read"),)
