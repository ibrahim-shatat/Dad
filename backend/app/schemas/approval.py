import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.approval import ApprovalItemType, ApprovalStatus


class ApprovalQueueItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    item_type: ApprovalItemType
    reference_id: uuid.UUID
    preview_text: str
    requested_by_id: uuid.UUID
    status: ApprovalStatus
    reviewed_by_id: uuid.UUID | None
    reviewed_at: datetime | None
    created_at: datetime
