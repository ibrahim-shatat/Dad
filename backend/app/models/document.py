import enum
import uuid

from sqlalchemy import JSON, BigInteger, Boolean, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin


class DocumentStatus(str, enum.Enum):
    uploaded = "uploaded"
    extracting = "extracting"
    extracted = "extracted"
    reviewing = "reviewing"
    reviewed = "reviewed"
    failed = "failed"


class Document(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "documents"

    uploaded_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(127), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, name="document_status"),
        nullable=False,
        default=DocumentStatus.uploaded,
    )
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    review: Mapped["DocumentReview | None"] = relationship(
        back_populates="document", uselist=False, cascade="all, delete-orphan"
    )


class DocumentReview(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "document_reviews"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, unique=True
    )
    executive_summary: Mapped[str] = mapped_column(Text, nullable=False)
    risk_flags: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    suggested_rewrite: Mapped[str] = mapped_column(Text, nullable=False)
    disclaimer_ack: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    model_used: Mapped[str] = mapped_column(String(127), nullable=False)

    document: Mapped["Document"] = relationship(back_populates="review")
