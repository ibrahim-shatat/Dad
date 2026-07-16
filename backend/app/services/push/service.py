"""Web Push (VAPID) delivery. Best-effort: push failures never break the caller. Sending is
gated on VAPID keys being configured — with no keys, in-app notifications still work, there's
just no phone push."""

import asyncio
import json
import logging
import uuid

from pywebpush import WebPushException, webpush
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.push import PushSubscription

logger = logging.getLogger(__name__)


def push_enabled() -> bool:
    return bool(settings.vapid_private_key and settings.vapid_public_key)


async def save_subscription(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    endpoint: str,
    p256dh: str,
    auth: str,
) -> None:
    existing = await db.execute(
        select(PushSubscription).where(PushSubscription.endpoint == endpoint)
    )
    sub = existing.scalar_one_or_none()
    if sub is not None:
        sub.user_id = user_id
        sub.p256dh = p256dh
        sub.auth = auth
    else:
        db.add(PushSubscription(user_id=user_id, endpoint=endpoint, p256dh=p256dh, auth=auth))
    await db.commit()


async def delete_subscription(db: AsyncSession, *, endpoint: str) -> None:
    await db.execute(delete(PushSubscription).where(PushSubscription.endpoint == endpoint))
    await db.commit()


def _send_one(subscription_info: dict, payload: str) -> None:
    webpush(
        subscription_info=subscription_info,
        data=payload,
        vapid_private_key=settings.vapid_private_key,
        vapid_claims={"sub": settings.vapid_subject},
        ttl=86400,
    )


async def send_push_to_user(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    title: str,
    body: str | None,
    url: str | None,
) -> None:
    """Fire a push to all of the user's subscribed devices. Called within the caller's
    transaction; stale-subscription cleanup rides the caller's commit (no commit here)."""
    if not push_enabled():
        return

    result = await db.execute(
        select(PushSubscription).where(PushSubscription.user_id == user_id)
    )
    subscriptions = list(result.scalars().all())
    if not subscriptions:
        return

    payload = json.dumps({"title": title, "body": body or "", "url": url or "/"})
    stale: list[str] = []
    for sub in subscriptions:
        info = {"endpoint": sub.endpoint, "keys": {"p256dh": sub.p256dh, "auth": sub.auth}}
        try:
            await asyncio.to_thread(_send_one, info, payload)
        except WebPushException as exc:
            status = getattr(exc.response, "status_code", None)
            if status in (404, 410):  # subscription expired/unsubscribed
                stale.append(sub.endpoint)
            else:
                logger.warning("web push failed (%s): %s", status, exc)
        except Exception as exc:  # noqa: BLE001 — never let push break the caller
            logger.warning("web push error: %s", exc)

    if stale:
        await db.execute(delete(PushSubscription).where(PushSubscription.endpoint.in_(stale)))
