"""Outlook Calendar read access via Microsoft Graph, reusing the same OAuth account as email
(Calendars.Read is in MS_SCOPES). Uses Graph's calendarView so recurring events are expanded."""

from datetime import datetime, timezone

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email import EmailAccount
from app.services.calendar.base import CalendarConnector, CalendarEventData
from app.services.email.outlook import GRAPH_BASE, OutlookConnector


def _parse_graph_dt(node: dict) -> datetime:
    # Graph returns naive ISO strings with a separate timeZone field (usually UTC for calendarView).
    raw = node["dateTime"]
    dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _event_to_data(event: dict) -> CalendarEventData | None:
    start = event.get("start")
    if not start or not start.get("dateTime"):
        return None
    end = event.get("end")
    organizer = ((event.get("organizer") or {}).get("emailAddress") or {}).get("address")
    attendees = [
        (a.get("emailAddress") or {}).get("address")
        for a in (event.get("attendees") or [])
        if (a.get("emailAddress") or {}).get("address")
    ]
    body = event.get("body") or {}
    return CalendarEventData(
        provider_event_id=event["id"],
        title=event.get("subject") or "(no title)",
        description=body.get("content") if body.get("contentType") == "text" else event.get("bodyPreview"),
        location=(event.get("location") or {}).get("displayName") or None,
        start_time=_parse_graph_dt(start),
        end_time=_parse_graph_dt(end) if end and end.get("dateTime") else None,
        is_all_day=bool(event.get("isAllDay")),
        organizer=organizer,
        attendees=attendees,
    )


class OutlookCalendarConnector(CalendarConnector):
    async def list_upcoming_events(
        self, db: AsyncSession, account: EmailAccount, *, time_min: datetime, time_max: datetime
    ) -> list[CalendarEventData]:
        # Reuse the email connector's token-refresh logic (same account, same token).
        access_token = await OutlookConnector()._ensure_fresh_token(db, account)
        params = {
            "startDateTime": time_min.astimezone(timezone.utc).isoformat(),
            "endDateTime": time_max.astimezone(timezone.utc).isoformat(),
            "$orderby": "start/dateTime",
            "$top": "50",
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{GRAPH_BASE}/me/calendarView",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Prefer": 'outlook.timezone="UTC"',
                },
                params=params,
            )
            resp.raise_for_status()
            events = []
            for raw in resp.json().get("value", []):
                data = _event_to_data(raw)
                if data is not None:
                    events.append(data)
            return events
