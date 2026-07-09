from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email import EmailAccount

if TYPE_CHECKING:
    from app.models.email import EmailProvider


@dataclass
class EmailMessageData:
    provider_message_id: str
    thread_id: str | None
    sender: str
    subject: str
    snippet: str
    body: str
    received_at: datetime
    is_unread: bool


class EmailConnector(ABC):
    """Provider-specific email access. `send_message` is only ever called from the approval
    -execution path (services/email/approval.py) — never from a draft-editing endpoint — which
    structurally enforces that nothing is sent without explicit director approval.

    Every method takes `db` because a connector may need to refresh an expired access token and
    persist the new one back onto the account row; callers are responsible for committing.
    """

    @abstractmethod
    async def list_messages(
        self, db: AsyncSession, account: EmailAccount, since: datetime | None = None
    ) -> list[EmailMessageData]: ...

    @abstractmethod
    async def get_message(
        self, db: AsyncSession, account: EmailAccount, provider_message_id: str
    ) -> EmailMessageData: ...

    @abstractmethod
    async def send_message(
        self,
        db: AsyncSession,
        account: EmailAccount,
        *,
        to: list[str],
        cc: list[str],
        subject: str,
        body: str,
        thread_id: str | None = None,
    ) -> None: ...


def get_connector(provider: "EmailProvider") -> EmailConnector:
    # Deferred imports: gmail.py/outlook.py import EmailConnector from this module at load time,
    # so importing them back at module level here would be circular.
    from app.models.email import EmailProvider
    from app.services.email.gmail import GmailConnector
    from app.services.email.outlook import OutlookConnector

    if provider == EmailProvider.gmail:
        return GmailConnector()
    if provider == EmailProvider.outlook:
        return OutlookConnector()
    raise ValueError(f"Unknown email provider: {provider}")
