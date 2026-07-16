import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.approval import ApprovalItemType, ApprovalStatus


class ApprovalQueueItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    item_type: ApprovalItemType
    reference_id: uuid.UUID
    preview_text: str
    requested_by_id: uuid.UUID
    requested_by_name: str | None = None
    status: ApprovalStatus
    reviewed_by_id: uuid.UUID | None
    reviewed_by_name: str | None = None
    reviewed_at: datetime | None
    review_note: str | None = None
    created_at: datetime


class RejectRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=1000)


class ApproveRequest(BaseModel):
    note: str | None = Field(default=None, max_length=1000)
