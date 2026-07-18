"""Helpers for creating in-app notifications. Callers add notifications within their own
transaction (these flush but do not commit) so a notification is only persisted if the
triggering action commits too."""

import uuid
from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationType
from app.models.user import User, UserRole
from app.services.push.fcm import send_fcm_to_user
from app.services.push.service import send_push_to_user


async def create_notification(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    type: NotificationType,
    title: str,
    body: str | None = None,
    link: str | None = None,
) -> Notification:
    notification = Notification(
        user_id=user_id, type=type, title=title, body=body, link=link
    )
    db.add(notification)
    await db.flush()
    # Best-effort push — no-op if unconfigured or the user has no registered devices.
    await send_push_to_user(db, user_id, title=title, body=body, url=link)  # web push (VAPID)
    await send_fcm_to_user(db, user_id, title=title, body=body, link=link)  # native mobile (FCM)
    return notification


async def notify_users(
    db: AsyncSession,
    user_ids: Iterable[uuid.UUID],
    *,
    type: NotificationType,
    title: str,
    body: str | None = None,
    link: str | None = None,
) -> None:
    for user_id in set(user_ids):
        await create_notification(
            db, user_id=user_id, type=type, title=title, body=body, link=link
        )


async def notify_roles(
    db: AsyncSession,
    roles: Iterable[UserRole],
    *,
    type: NotificationType,
    title: str,
    body: str | None = None,
    link: str | None = None,
    exclude_user_id: uuid.UUID | None = None,
) -> None:
    """Notify every active user holding one of the given roles (e.g. the approvers)."""
    result = await db.execute(
        select(User.id).where(User.role.in_(list(roles)), User.is_active.is_(True))
    )
    user_ids = [row[0] for row in result.all() if row[0] != exclude_user_id]
    await notify_users(db, user_ids, type=type, title=title, body=body, link=link)
