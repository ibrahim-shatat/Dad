import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin


class DeviceToken(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """A Firebase Cloud Messaging registration token for one mobile device belonging to a user.
    Used to deliver native push notifications to the Flutter app."""

    __tablename__ = "device_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    # The FCM registration token uniquely identifies a device install.
    token: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    platform: Mapped[str] = mapped_column(String(32), nullable=False, default="android")
