"""Gmail connector. google-api-python-client is fully synchronous, so the actual API calls run
in a worker thread via asyncio.to_thread; token refresh happens first, in the async method, so it
can safely persist the refreshed token through the (async) db session.
"""

import asyncio
import base64
import re
from datetime import datetime, timezone
from email.mime.text import MIMEText

from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.email import EmailAccount
from app.services.email.base import EmailConnector, EmailMessageData
from app.services.email.oauth import decrypt_token, encrypt_token

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/userinfo.email",
    # Calendar read (Phase 4 / M6): a connected Google account also powers the calendar.
    "https://www.googleapis.com/auth/calendar.readonly",
]

_TOKEN_URI = "https://oauth2.googleapis.com/token"
_AUTH_URI = "https://accounts.google.com/o/oauth2/auth"


def gmail_redirect_uri() -> str:
    return f"{settings.api_base_url}/api/v1/email/gmail/callback"


def build_gmail_flow(state: str | None = None):
    from google_auth_oauthlib.flow import Flow

    client_config = {
        "web": {
            "client_id": settings.gmail_client_id,
            "client_secret": settings.gmail_client_secret,
            "auth_uri": _AUTH_URI,
            "token_uri": _TOKEN_URI,
            "redirect_uris": [gmail_redirect_uri()],
        }
    }
    return Flow.from_client_config(
        client_config, scopes=GMAIL_SCOPES, redirect_uri=gmail_redirect_uri(), state=state
    )


def _decode_base64url(data: str) -> bytes:
    padded = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded)


def _strip_html(html: str) -> str:
    return re.sub(r"<[^>]+>", " ", html)


def _extract_body(payload: dict) -> str:
    mime_type = payload.get("mimeType", "")
    if mime_type == "text/plain" and payload.get("body", {}).get("data"):
        return _decode_base64url(payload["body"]["data"]).decode("utf-8", errors="replace")

    html_fallback: str | None = None
    for part in payload.get("parts", []) or []:
        part_mime = part.get("mimeType", "")
        if part_mime == "text/plain" and part.get("body", {}).get("data"):
            return _decode_base64url(part["body"]["data"]).decode("utf-8", errors="replace")
        if part_mime == "text/html" and part.get("body", {}).get("data") and html_fallback is None:
            html_fallback = _decode_base64url(part["body"]["data"]).decode("utf-8", errors="replace")
        if part_mime.startswith("multipart/"):
            nested = _extract_body(part)
            if nested:
                return nested

    if html_fallback is not None:
        return _strip_html(html_fallback)
    if payload.get("body", {}).get("data"):
        return _decode_base64url(payload["body"]["data"]).decode("utf-8", errors="replace")
    return ""


def _message_to_data(msg: dict) -> EmailMessageData:
    headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
    return EmailMessageData(
        provider_message_id=msg["id"],
        thread_id=msg.get("threadId"),
        sender=headers.get("From", "unknown"),
        subject=headers.get("Subject", "(no subject)"),
        snippet=msg.get("snippet", ""),
        body=_extract_body(msg.get("payload", {})),
        received_at=datetime.fromtimestamp(int(msg["internalDate"]) / 1000, tz=timezone.utc),
        is_unread="UNREAD" in msg.get("labelIds", []),
    )


class GmailConnector(EmailConnector):
    async def _ensure_fresh_credentials(self, db: AsyncSession, account: EmailAccount) -> Credentials:
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

    async def list_messages(
        self, db: AsyncSession, account: EmailAccount, since: datetime | None = None
    ) -> list[EmailMessageData]:
        creds = await self._ensure_fresh_credentials(db, account)
        return await asyncio.to_thread(self._list_messages_sync, creds, since)

    def _list_messages_sync(self, creds: Credentials, since: datetime | None) -> list[EmailMessageData]:
        service = build("gmail", "v1", credentials=creds, cache_discovery=False)
        query = "in:inbox"
        if since is not None:
            query += f" after:{int(since.timestamp())}"

        results = (
            service.users().messages().list(userId="me", q=query, maxResults=25).execute()
        )
        messages = []
        for ref in results.get("messages", []):
            full = service.users().messages().get(userId="me", id=ref["id"], format="full").execute()
            messages.append(_message_to_data(full))
        return messages

    async def get_message(
        self, db: AsyncSession, account: EmailAccount, provider_message_id: str
    ) -> EmailMessageData:
        creds = await self._ensure_fresh_credentials(db, account)
        return await asyncio.to_thread(self._get_message_sync, creds, provider_message_id)

    def _get_message_sync(self, creds: Credentials, provider_message_id: str) -> EmailMessageData:
        service = build("gmail", "v1", credentials=creds, cache_discovery=False)
        full = (
            service.users()
            .messages()
            .get(userId="me", id=provider_message_id, format="full")
            .execute()
        )
        return _message_to_data(full)

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
    ) -> None:
        creds = await self._ensure_fresh_credentials(db, account)
        await asyncio.to_thread(self._send_message_sync, creds, to, cc, subject, body, thread_id)

    def _send_message_sync(
        self,
        creds: Credentials,
        to: list[str],
        cc: list[str],
        subject: str,
        body: str,
        thread_id: str | None,
    ) -> None:
        service = build("gmail", "v1", credentials=creds, cache_discovery=False)
        message = MIMEText(body)
        message["to"] = ", ".join(to)
        if cc:
            message["cc"] = ", ".join(cc)
        message["subject"] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        payload: dict = {"raw": raw}
        if thread_id:
            payload["threadId"] = thread_id
        service.users().messages().send(userId="me", body=payload).execute()


def fetch_gmail_profile_email(creds: Credentials) -> str:
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)
    profile = service.users().getProfile(userId="me").execute()
    return profile["emailAddress"]
