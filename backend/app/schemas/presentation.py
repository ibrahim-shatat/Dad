import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.models.presentation import PresentationStatus


class SlideChartRead(BaseModel):
    categories: list[str]
    values: list[float]
    series_name: str


class SlideContentRead(BaseModel):
    layout: Literal["section_header", "bullets", "two_column", "chart"]
    title: str
    bullets: list[str]
    left_column: list[str]
    right_column: list[str]
    chart: SlideChartRead | None
    speaker_notes: str


class PresentationOutlineRead(BaseModel):
    title: str
    slides: list[SlideContentRead]


class PresentationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_document_id: uuid.UUID | None
    title: str | None
    instructions: str | None
    structured_content: PresentationOutlineRead | None
    status: PresentationStatus
    failure_reason: str | None
    created_at: datetime
