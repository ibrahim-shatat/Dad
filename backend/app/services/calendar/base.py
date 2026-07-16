from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email import EmailAccount

if TYPE_CHECKING:
    from app.models.email import EmailProvider


@dataclass
class CalendarEventData:
    provider_event_id: str
    title: str
    description: str | None
    location: str | None
    start_time: datetime
    end_time: datetime | None
    is_all_day: bool
    organizer: str | None
    attendees: list[str] = field(default_factory=list)


class CalendarConnector(ABC):
    """Provider-specific read access to a connected calendar. Read-only — the app never writes
    events. Takes `db` because refreshing an expired access token persists the new one back onto
    the account row; callers are responsible for committing."""

    @abstractmethod
    async def list_upcoming_events(
        self, db: AsyncSession, account: EmailAccount, *, time_min: datetime, time_max: datetime
    ) -> list[CalendarEventData]: ...


def get_calendar_connector(provider: "EmailProvider") -> CalendarConnector:
    from app.models.email import EmailProvider
    from app.services.calendar.gmail_calendar import GoogleCalendarConnector
    from app.services.calendar.outlook_calendar import OutlookCalendarConnector

    if provider == EmailProvider.gmail:
        return GoogleCalendarConnector()
    if provider == EmailProvider.outlook:
        return OutlookCalendarConnector()
    raise ValueError(f"Unknown calendar provider: {provider}")
