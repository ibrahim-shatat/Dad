import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.meeting import (
    ActionItem,
    ActionItemStatus,
    Decision,
    DecisionStatus,
    Meeting,
    MeetingStatus,
)
from app.models.user import User
from app.schemas.meeting import MeetingRead
from app.services.email import approval as _email_approval  # noqa: F401 — registers the email_draft handler
from app.tasks.queue import JobEnqueuer, get_job_queue

router = APIRouter()

_EAGER_OPTIONS = (
    selectinload(Meeting.action_items),
    selectinload(Meeting.decisions),
    selectinload(Meeting.email_drafts),
)


class MeetingCreate(BaseModel):
    title: str
    source_text: str
    meeting_date: date | None = None
    instructions: str | None = None


async def _get_meeting(db: AsyncSession, meeting_id: uuid.UUID) -> Meeting:
    result = await db.execute(
        select(Meeting).options(*_EAGER_OPTIONS).where(Meeting.id == meeting_id)
    )
    meeting = result.scalar_one_or_none()
    if meeting is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
    return meeting


@router.post("", response_model=MeetingRead, status_code=status.HTTP_201_CREATED)
async def create_meeting(
    payload: MeetingCreate,
    db: AsyncSession = Depends(get_db),
    queue: JobEnqueuer = Depends(get_job_queue),
    user: User = Depends(get_current_user),
) -> Meeting:
    meeting = Meeting(
        created_by_id=user.id,
        title=payload.title,
        meeting_date=payload.meeting_date or date.today(),
        source_text=payload.source_text,
        instructions=payload.instructions,
    )
    db.add(meeting)
    await db.commit()

    await queue.enqueue_job("process_meeting", str(meeting.id))
    return await _get_meeting(db, meeting.id)


@router.get("", response_model=list[MeetingRead])
async def list_meetings(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[Meeting]:
    result = await db.execute(
        select(Meeting)
        .options(*_EAGER_OPTIONS)
        .order_by(Meeting.meeting_date.desc(), Meeting.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/{meeting_id}", response_model=MeetingRead)
async def get_meeting(
    meeting_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Meeting:
    return await _get_meeting(db, meeting_id)


@router.post("/{meeting_id}/regenerate", response_model=MeetingRead)
async def regenerate_meeting(
    meeting_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    queue: JobEnqueuer = Depends(get_job_queue),
    _: User = Depends(get_current_user),
) -> Meeting:
    meeting = await _get_meeting(db, meeting_id)
    if meeting.status == MeetingStatus.processing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already processing")

    # Clear previously extracted items so regenerating doesn't duplicate them. Past approval
    # queue items / email drafts are left as historical record, same as presentation regenerate.
    await db.execute(delete(ActionItem).where(ActionItem.meeting_id == meeting_id))
    await db.execute(delete(Decision).where(Decision.meeting_id == meeting_id))

    meeting.status = MeetingStatus.processing
    meeting.summary = None
    meeting.failure_reason = None
    await db.commit()

    await queue.enqueue_job("process_meeting", str(meeting_id))
    return await _get_meeting(db, meeting_id)


class ActionItemStatusUpdate(BaseModel):
    status: ActionItemStatus


@router.patch("/{meeting_id}/action-items/{item_id}", response_model=MeetingRead)
async def update_action_item_status(
    meeting_id: uuid.UUID,
    item_id: uuid.UUID,
    payload: ActionItemStatusUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Meeting:
    item = await db.get(ActionItem, item_id)
    if item is None or item.meeting_id != meeting_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action item not found")

    item.status = payload.status
    await db.commit()
    return await _get_meeting(db, meeting_id)


class DecisionStatusUpdate(BaseModel):
    status: DecisionStatus


@router.patch("/{meeting_id}/decisions/{decision_id}", response_model=MeetingRead)
async def update_decision_status(
    meeting_id: uuid.UUID,
    decision_id: uuid.UUID,
    payload: DecisionStatusUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Meeting:
    decision = await db.get(Decision, decision_id)
    if decision is None or decision.meeting_id != meeting_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Decision not found")

    decision.status = payload.status
    await db.commit()
    return await _get_meeting(db, meeting_id)
