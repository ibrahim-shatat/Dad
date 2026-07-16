"""Google Calendar read access. Reuses the same OAuth account as Gmail (calendar.readonly scope
is included in GMAIL_SCOPES). google-api-python-client is synchronous, so calls run in a worker
thread; token refresh happens first in the async method so the refreshed token can be persisted."""

import asyncio
from datetime import datetime, timezone

from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.email import EmailAccount
from app.services.calendar.base import CalendarConnector, CalendarEventData
from app.services.email.gmail import GMAIL_SCOPES, _TOKEN_URI
from app.services.email.oauth import decrypt_token, encrypt_token


def _parse_dt(node: dict) -> tuple[datetime, bool]:
    """Google returns either {'dateTime': ...} for timed events or {'date': ...} for all-day."""
    if node.get("dateTime"):
        return datetime.fromisoformat(node["dateTime"].replace("Z", "+00:00")), False
    # All-day event: date only.
    return datetime.fromisoformat(node["date"]).replace(tzinfo=timezone.utc), True


def _event_to_data(event: dict) -> CalendarEventData | None:
    start = event.get("start") or {}
    end = event.get("end") or {}
    if not (start.get("dateTime") or start.get("date")):
        return None  # Skip events with no usable start (e.g. cancelled).
    start_time, all_day = _parse_dt(start)
    end_time = _parse_dt(end)[0] if (end.get("dateTime") or end.get("date")) else None
    organizer = (event.get("organizer") or {}).get("email")
    attendees = [
        a.get("email") for a in (event.get("attendees") or []) if a.get("email")
    ]
    return CalendarEventData(
        provider_event_id=event["id"],
        title=event.get("summary") or "(no title)",
        description=event.get("description"),
        location=event.get("location"),
        start_time=start_time,
        end_time=end_time,
        is_all_day=all_day,
        organizer=organizer,
        attendees=attendees,
    )


class GoogleCalendarConnector(CalendarConnector):
    async def _fresh_credentials(self, db: AsyncSession, account: EmailAccount) -> Credentials:
        creds = Credentials(
            token=decrypt_token(account.oauth_access_token),
            refresh_token=decrypt_token(account.oauth_refresh_token),
            token_uri=_TOKEN_URI,
            client_id=settings.gmail_client_id,
            client_secret=settings.gmail_client_secret,
            scopes=GMAIL_SCOPES,
            expiry=account.token_expires_at.replace(tzinfo=None),
        )
        if creds.expired:
            await asyncio.to_thread(creds.refresh, GoogleAuthRequest())
            account.oauth_access_token = encrypt_token(creds.token)
            account.token_expires_at = creds.expiry.replace(tzinfo=timezone.utc)
        return creds

    async def list_upcoming_events(
        self, db: AsyncSession, account: EmailAccount, *, time_min: datetime, time_max: datetime
    ) -> list[CalendarEventData]:
        creds = await self._fresh_credentials(db, account)
        return await asyncio.to_thread(self._list_sync, creds, time_min, time_max)

    def _list_sync(
        self, creds: Credentials, time_min: datetime, time_max: datetime
    ) -> list[CalendarEventData]:
        service = build("calendar", "v3", credentials=creds, cache_discovery=False)
        result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=time_min.astimezone(timezone.utc).isoformat(),
                timeMax=time_max.astimezone(timezone.utc).isoformat(),
                singleEvents=True,
                orderBy="startTime",
                maxResults=50,
            )
            .execute()
        )
        events = []
        for raw in result.get("items", []):
            data = _event_to_data(raw)
            if data is not None:
                events.append(data)
        return events
