"""Test doubles for external systems: Claude and email providers. Nothing here should ever
make a real network call.
"""

from datetime import datetime, timezone

from app.services.email.base import EmailConnector, EmailMessageData


class FakeEmailConnector(EmailConnector):
    def __init__(self) -> None:
        self.sent_messages: list[dict] = []
        self.messages_to_return: list[EmailMessageData] = []

    async def list_messages(self, db, account, since=None) -> list[EmailMessageData]:
        return self.messages_to_return

    async def get_message(self, db, account, provider_message_id: str) -> EmailMessageData:
        for message in self.messages_to_return:
            if message.provider_message_id == provider_message_id:
                return message
        raise ValueError(f"No fake message with id {provider_message_id}")

    async def send_message(
        self, db, account, *, to, cc, subject, body, reply_to=None
    ) -> None:
        self.sent_messages.append(
            {
                "to": to,
                "cc": cc,
                "subject": subject,
                "body": body,
                "reply_to": reply_to.provider_message_id if reply_to is not None else None,
            }
        )


def make_fake_message(
    provider_message_id: str = "msg-1",
    sender: str = "someone@example.com",
    subject: str = "Test subject",
    body: str = "Test body",
    thread_id: str | None = "thread-1",
) -> EmailMessageData:
    return EmailMessageData(
        provider_message_id=provider_message_id,
        thread_id=thread_id,
        sender=sender,
        subject=subject,
        snippet=body[:100],
        body=body,
        received_at=datetime.now(timezone.utc),
        is_unread=True,
    )
