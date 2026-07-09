import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_role
from app.db.session import get_db
from app.models.approval import ApprovalQueueItem, ApprovalStatus
from app.models.user import User, UserRole
from app.schemas.approval import ApprovalQueueItemRead
from app.services.approvals import service as approvals_service

router = APIRouter()


@router.get("", response_model=list[ApprovalQueueItemRead])
async def list_approval_items(
    status_filter: ApprovalStatus | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[ApprovalQueueItem]:
    query = select(ApprovalQueueItem).order_by(ApprovalQueueItem.created_at.desc())
    if status_filter is not None:
        query = query.where(ApprovalQueueItem.status == status_filter)
    result = await db.execute(query)
    return list(result.scalars().all())


async def _get_pending_item(db: AsyncSession, item_id: uuid.UUID) -> ApprovalQueueItem:
    item = await db.get(ApprovalQueueItem, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval item not found")
    if item.status != ApprovalStatus.pending:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Item already {item.status.value}",
        )
    return item


@router.post(
    "/{item_id}/approve",
    response_model=ApprovalQueueItemRead,
    dependencies=[Depends(require_role(UserRole.director, UserRole.admin))],
)
async def approve(
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    reviewer: User = Depends(get_current_user),
) -> ApprovalQueueItem:
    item = await _get_pending_item(db, item_id)
    return await approvals_service.approve_item(db, item, reviewer)


@router.post(
    "/{item_id}/reject",
    response_model=ApprovalQueueItemRead,
    dependencies=[Depends(require_role(UserRole.director, UserRole.admin))],
)
async def reject(
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    reviewer: User = Depends(get_current_user),
) -> ApprovalQueueItem:
    item = await _get_pending_item(db, item_id)
    return await approvals_service.reject_item(db, item, reviewer)
