import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.models.document import DocumentStatus


class RiskFlagRead(BaseModel):
    category: str
    description: str
    severity: Literal["low", "medium", "high"]


class DocumentReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    executive_summary: str
    risk_flags: list[RiskFlagRead]
    suggested_rewrite: str
    disclaimer_ack: bool
    model_used: str
    created_at: datetime


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    mime_type: str
    file_size: int
    instructions: str | None
    status: DocumentStatus
    failure_reason: str | None
    created_at: datetime
    review: DocumentReviewRead | None = None
