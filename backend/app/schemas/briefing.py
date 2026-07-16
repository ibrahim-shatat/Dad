import uuid
from datetime import date, datetime

from pydantic import BaseModel


class BriefingItemRead(BaseModel):
    key: str
    title: str
    subtitle: str | None = None
    detail: str | None = None
    link: str | None = None
    severity: str | None = None  # low | medium | high, where meaningful
    handled: bool = False


class BriefingSectionRead(BaseModel):
    id: str  # e.g. "urgent_emails"
    label: str
    items: list[BriefingItemRead]


class BriefingRead(BaseModel):
    briefing_date: date
    summary: str | None
    top_priorities: list[str]
    generated_at: datetime | None
    sections: list[BriefingSectionRead]
    total_items: int
    handled_items: int


class ToggleItemRequest(BaseModel):
    key: str
    handled: bool
