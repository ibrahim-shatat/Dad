import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.calendar import CalendarEvent
from app.models.email import EmailAccount
from app.models.user import User
from app.schemas.calendar import CalendarEventRead
from app.tasks.queue import JobEnqueuer, get_job_queue

router = APIRouter()


async def _user_owns_event(db: AsyncSession, user: User, event_id: uuid.UUID) -> CalendarEvent:
    result = await db.execute(
        select(CalendarEvent)
        .join(EmailAccount, CalendarEvent.account_id == EmailAccount.id)
        .where(CalendarEvent.id == event_id, EmailAccount.user_id == user.id)
    )
    event = result.scalar_one_or_none()
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event


@router.get("/events", response_model=list[CalendarEventRead])
async def list_events(
    include_past: bool = False,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[CalendarEvent]:
    query = (
        select(CalendarEvent)
        .join(EmailAccount, CalendarEvent.account_id == EmailAccount.id)
        .where(EmailAccount.user_id == user.id)
        .order_by(CalendarEvent.start_time.asc())
    )
    if not include_past:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
        query = query.where(CalendarEvent.start_time >= cutoff)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/events/{event_id}", response_model=CalendarEventRead)
async def get_event(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CalendarEvent:
    return await _user_owns_event(db, user, event_id)


@router.post("/sync", status_code=status.HTTP_202_ACCEPTED)
async def sync_calendars(
    queue: JobEnqueuer = Depends(get_job_queue),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    result = await db.execute(select(EmailAccount.id).where(EmailAccount.user_id == user.id))
    account_ids = [row[0] for row in result.all()]
    if not account_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No connected account. Connect Google or Outlook on the Email page first.",
        )
    for account_id in account_ids:
        await queue.enqueue_job("sync_calendar_account", str(account_id))
    return {"status": "queued", "accounts": len(account_ids)}


@router.post("/events/{event_id}/prep", status_code=status.HTTP_202_ACCEPTED)
async def generate_prep(
    event_id: uuid.UUID,
    queue: JobEnqueuer = Depends(get_job_queue),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    event = await _user_owns_event(db, user, event_id)
    await queue.enqueue_job("generate_event_prep", str(event.id))
    return {"status": "queued"}


@router.post("/events/{event_id}/follow-up", status_code=status.HTTP_202_ACCEPTED)
async def draft_follow_up(
    event_id: uuid.UUID,
    queue: JobEnqueuer = Depends(get_job_queue),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    event = await _user_owns_event(db, user, event_id)
    await queue.enqueue_job("draft_event_follow_up", str(event.id))
    return {"status": "queued"}
