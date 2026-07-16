import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    actor_email: str | None
    action: str
    target_type: str | None
    target_id: str | None
    detail: str | None
    ip: str | None


class ConnectedAccountHealth(BaseModel):
    email_address: str
    provider: str
    last_synced_at: datetime | None


class SystemHealth(BaseModel):
    total_users: int
    active_users: int
    failed_documents: int
    failed_meetings: int
    failed_presentations: int
    connected_accounts: list[ConnectedAccountHealth]
    recent_job_failures: list[AuditLogRead]
