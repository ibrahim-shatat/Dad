import uuid
from datetime import datetime, timezone
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.approval import ApprovalItemType, ApprovalQueueItem, ApprovalStatus
from app.models.user import User


class ApprovalHandler(Protocol):
    async def on_approve(self, db: AsyncSession, reference_id: uuid.UUID) -> None: ...
    async def on_reject(self, db: AsyncSession, reference_id: uuid.UUID) -> None: ...


class DummyApprovalHandler:
    """Phase 0 proof-of-flow handler — no real side effect. Remove once a real item type exists."""

    async def on_approve(self, db: AsyncSession, reference_id: uuid.UUID) -> None:
        return None

    async def on_reject(self, db: AsyncSession, reference_id: uuid.UUID) -> None:
        return None


_HANDLERS: dict[ApprovalItemType, ApprovalHandler] = {
    ApprovalItemType.dummy: DummyApprovalHandler(),
}


def register_handler(item_type: ApprovalItemType, handler: ApprovalHandler) -> None:
    """Feature modules call this at import time to plug in their approve/reject side effect."""
    _HANDLERS[item_type] = handler


async def create_approval_item(
    db: AsyncSession,
    *,
    item_type: ApprovalItemType,
    reference_id: uuid.UUID,
    preview_text: str,
    requested_by_id: uuid.UUID,
) -> ApprovalQueueItem:
    item = ApprovalQueueItem(
        item_type=item_type,
        reference_id=reference_id,
        preview_text=preview_text,
        requested_by_id=requested_by_id,
    )
    db.add(item)
    await db.flush()
    return item


async def approve_item(db: AsyncSession, item: ApprovalQueueItem, reviewer: User) -> ApprovalQueueItem:
    handler = _HANDLERS.get(item.item_type)
    if handler is None:
        raise ValueError(f"No approval handler registered for item_type={item.item_type}")

    await handler.on_approve(db, item.reference_id)

    item.status = ApprovalStatus.approved
    item.reviewed_by_id = reviewer.id
    item.reviewed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(item)
    return item


async def reject_item(db: AsyncSession, item: ApprovalQueueItem, reviewer: User) -> ApprovalQueueItem:
    handler = _HANDLERS.get(item.item_type)
    if handler is not None:
        await handler.on_reject(db, item.reference_id)

    item.status = ApprovalStatus.rejected
    item.reviewed_by_id = reviewer.id
    item.reviewed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(item)
    return item
