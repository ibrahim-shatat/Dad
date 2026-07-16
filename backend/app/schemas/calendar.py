import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CalendarEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    title: str
    description: str | None
    location: str | None
    start_time: datetime
    end_time: datetime | None
    is_all_day: bool
    organizer: str | None
    attendees: list[str]
    prep_brief: str | None
    prep_generated_at: datetime | None
    created_at: datetime
