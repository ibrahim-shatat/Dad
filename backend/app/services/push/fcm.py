"""Firebase Cloud Messaging (native mobile push) via the HTTP v1 API. Best-effort: send
failures never break the caller. Gated on FCM credentials being configured — with none, in-app
notifications and web push still work, there's just no mobile push.
"""

import asyncio
import json
import logging
import uuid

import httpx
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.device_token import DeviceToken

logger = logging.getLogger(__name__)

_SCOPE = "https://www.googleapis.com/auth/firebase.messaging"


def fcm_enabled() -> bool:
    return bool(settings.fcm_credentials_json and settings.fcm_project_id)


def _fetch_access_token() -> str | None:
    """Synchronous: mint a short-lived OAuth token from the service-account JSON. Run in a
    thread so it doesn't block the event loop."""
    from google.auth.transport.requests import Request
    from google.oauth2 import service_account

    info = json.loads(settings.fcm_credentials_json)
    creds = service_account.Credentials.from_service_account_info(info, scopes=[_SCOPE])
    creds.refresh(Request())
    return creds.token


async def register_device(
    db: AsyncSession, *, user_id: uuid.UUID, token: str, platform: str
) -> None:
    existing = await db.execute(select(DeviceToken).where(DeviceToken.token == token))
    device = existing.scalar_one_or_none()
    if device is not None:
        device.user_id = user_id
        device.platform = platform
    else:
        db.add(DeviceToken(user_id=user_id, token=token, platform=platform))
    await db.commit()


async def unregister_device(db: AsyncSession, *, user_id: uuid.UUID, token: str) -> None:
    await db.execute(
        delete(DeviceToken).where(
            DeviceToken.token == token, DeviceToken.user_id == user_id
        )
    )
    await db.commit()


async def send_fcm_to_user(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    title: str,
    body: str | None = None,
    link: str | None = None,
) -> None:
    """Push a notification to all of a user's registered mobile devices. No-op if FCM isn't
    configured or the user has no devices. Prunes tokens the server reports as unregistered."""
    if not fcm_enabled():
        return

    result = await db.execute(
        select(DeviceToken.token).where(DeviceToken.user_id == user_id)
    )
    tokens = [row[0] for row in result.all()]
    if not tokens:
        return

    try:
        access_token = await asyncio.to_thread(_fetch_access_token)
    except Exception:
        logger.warning("FCM: could not obtain access token", exc_info=True)
        return
    if not access_token:
        return

    url = f"https://fcm.googleapis.com/v1/projects/{settings.fcm_project_id}/messages:send"
    headers = {"Authorization": f"Bearer {access_token}"}
    stale: list[str] = []

    async with httpx.AsyncClient(timeout=10) as client:
        for token in tokens:
            message: dict = {
                "message": {
                    "token": token,
                    "notification": {"title": title, "body": body or ""},
                }
            }
            if link:
                # data values must be strings; the app reads `link` to deep-link on tap.
                message["message"]["data"] = {"link": link}
            try:
                resp = await client.post(url, headers=headers, json=message)
            except Exception:
                logger.warning("FCM: send failed for a device", exc_info=True)
                continue
            # 404 (NOT_FOUND) / 400 with UNREGISTERED means the token is dead — drop it.
            if resp.status_code in (400, 404):
                stale.append(token)

    if stale:
        await db.execute(delete(DeviceToken).where(DeviceToken.token.in_(stale)))
