"""Append-only audit logging. `record` adds + flushes within the caller's transaction (so the
entry only persists if the action commits too); `record_and_commit` is for standalone events
like a login attempt that has no other transaction to ride along with."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog
from app.models.user import User


async def record(
    db: AsyncSession,
    *,
    action: str,
    actor: User | None = None,
    actor_email: str | None = None,
    target_type: str | None = None,
    target_id: str | uuid.UUID | None = None,
    detail: str | None = None,
    ip: str | None = None,
) -> AuditLog:
    entry = AuditLog(
        action=action,
        actor_id=actor.id if actor else None,
        actor_email=actor_email or (actor.email if actor else None),
        target_type=target_type,
        target_id=str(target_id) if target_id is not None else None,
        detail=detail,
        ip=ip,
    )
    db.add(entry)
    await db.flush()
    return entry


async def record_and_commit(db: AsyncSession, **kwargs) -> AuditLog:
    entry = await record(db, **kwargs)
    await db.commit()
    return entry
