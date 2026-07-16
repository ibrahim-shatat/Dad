import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_role
from app.db.session import get_db
from app.models.approval import ApprovalItemType, ApprovalQueueItem, ApprovalStatus
from app.models.user import User, UserRole
from app.schemas.approval import ApproveRequest, ApprovalQueueItemRead, RejectRequest
from app.services.approvals import service as approvals_service

router = APIRouter()


async def _serialize(db: AsyncSession, items: list[ApprovalQueueItem]) -> list[ApprovalQueueItemRead]:
    """Attach the requester / reviewer display names (one query for all the referenced users)."""
    user_ids = {i.requested_by_id for i in items} | {
        i.reviewed_by_id for i in items if i.reviewed_by_id
    }
    names: dict[uuid.UUID, str] = {}
    if user_ids:
        result = await db.execute(
            select(User.id, User.full_name).where(User.id.in_(user_ids))
        )
        names = {row[0]: row[1] for row in result.all()}

    out: list[ApprovalQueueItemRead] = []
    for item in items:
        read = ApprovalQueueItemRead.model_validate(item)
        read.requested_by_name = names.get(item.requested_by_id)
        read.reviewed_by_name = names.get(item.reviewed_by_id) if item.reviewed_by_id else None
        out.append(read)
    return out


@router.get("", response_model=list[ApprovalQueueItemRead])
async def list_approval_items(
    status_filter: ApprovalStatus | None = None,
    type_filter: ApprovalItemType | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[ApprovalQueueItemRead]:
    query = select(ApprovalQueueItem).order_by(ApprovalQueueItem.created_at.desc())
    if status_filter is not None:
        query = query.where(ApprovalQueueItem.status == status_filter)
    if type_filter is not None:
        query = query.where(ApprovalQueueItem.item_type == type_filter)
    result = await db.execute(query)
    return await _serialize(db, list(result.scalars().all()))


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
    payload: ApproveRequest | None = None,
    db: AsyncSession = Depends(get_db),
    reviewer: User = Depends(get_current_user),
) -> ApprovalQueueItemRead:
    item = await _get_pending_item(db, item_id)
    item = await approvals_service.approve_item(
        db, item, reviewer, note=payload.note if payload else None
    )
    return (await _serialize(db, [item]))[0]


@router.post(
    "/{item_id}/reject",
    response_model=ApprovalQueueItemRead,
    dependencies=[Depends(require_role(UserRole.director, UserRole.admin))],
)
async def reject(
    item_id: uuid.UUID,
    payload: RejectRequest,
    db: AsyncSession = Depends(get_db),
    reviewer: User = Depends(get_current_user),
) -> ApprovalQueueItemRead:
    item = await _get_pending_item(db, item_id)
    item = await approvals_service.reject_item(db, item, reviewer, reason=payload.reason)
    return (await _serialize(db, [item]))[0]
