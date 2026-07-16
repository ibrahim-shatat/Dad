from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.briefing import Briefing
from app.models.user import User
from app.schemas.briefing import (
    BriefingItemRead,
    BriefingRead,
    BriefingSectionRead,
    ToggleItemRequest,
)
from app.services.briefing import service as briefing_service

router = APIRouter()


def _today() -> date:
    return date.today()


async def _build_read(
    db: AsyncSession, user: User, briefing: Briefing, today: date
) -> BriefingRead:
    sections = await briefing_service.assemble_sections(db, user, today)
    handled = set(briefing.handled_keys or [])

    section_reads: list[BriefingSectionRead] = []
    total = 0
    handled_count = 0
    for section in sections:
        items = [
            BriefingItemRead(
                key=item["key"],
                title=item["title"],
                subtitle=item.get("subtitle"),
                detail=item.get("detail"),
                link=item.get("link"),
                severity=item.get("severity"),
                handled=item["key"] in handled,
            )
            for item in section.items
        ]
        total += len(items)
        handled_count += sum(1 for i in items if i.handled)
        section_reads.append(
            BriefingSectionRead(id=section.id, label=section.label, items=items)
        )

    return BriefingRead(
        briefing_date=today,
        summary=briefing.summary,
        top_priorities=briefing.top_priorities or [],
        generated_at=briefing.generated_at,
        sections=section_reads,
        total_items=total,
        handled_items=handled_count,
    )


@router.get("/today", response_model=BriefingRead)
async def get_today_briefing(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BriefingRead:
    today = _today()
    briefing = await briefing_service.get_or_create_briefing(db, user, today)
    await db.commit()
    return await _build_read(db, user, briefing, today)


@router.post("/generate", response_model=BriefingRead)
async def generate_briefing(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BriefingRead:
    today = _today()
    briefing = await briefing_service.regenerate(db, user, today)
    return await _build_read(db, user, briefing, today)


@router.post("/items/toggle", response_model=BriefingRead)
async def toggle_item(
    payload: ToggleItemRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BriefingRead:
    today = _today()
    briefing = await briefing_service.get_or_create_briefing(db, user, today)

    keys = set(briefing.handled_keys or [])
    if payload.handled:
        keys.add(payload.key)
    else:
        keys.discard(payload.key)
    # Reassign a new list so SQLAlchemy detects the change on the JSON column.
    briefing.handled_keys = sorted(keys)
    await db.commit()
    await db.refresh(briefing)
    return await _build_read(db, user, briefing, today)
