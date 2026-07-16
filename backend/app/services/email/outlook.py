"""Outlook connector via Microsoft Graph. msal's token calls are synchronous (blocking network
calls), so they're wrapped in asyncio.to_thread; the Graph API calls themselves use httpx's async
client directly.
"""

import asyncio
import re
from datetime import datetime, timedelta, timezone

import httpx
from msal import ConfidentialClientApplication
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.email import EmailAccount
from app.services.email.base import EmailConnector, EmailMessageData
from app.services.email.oauth import decrypt_token, encrypt_token

MS_AUTHORITY = "https://login.microsoftonline.com/common"
# msal treats offline_access (along with openid/profile) as a reserved scope it adds itself for
# confidential-client auth-code flow — passing it explicitly raises ValueError.
# Calendars.Read (M6): the same connected account also powers the calendar.
MS_SCOPES = ["Mail.Read", "Mail.Send", "User.Read", "Calendars.Read"]
GRAPH_BASE = "https://graph.microsoft.com/v1.0"


def outlook_redirect_uri() -> str:
    return f"{settings.api_base_url}/api/v1/email/outlook/callback"


def _msal_app() -> ConfidentialClientApplication:
    return ConfidentialClientApplication(
        client_id=settings.ms_client_id,
        client_credential=settings.ms_client_secret,
        authority=MS_AUTHORITY,
    )


def build_outlook_authorization_url(state: str) -> str:
    app = _msal_app()
    return app.get_authorization_request_url(
        MS_SCOPES, redirect_uri=outlook_redirect_uri(), state=state
    )


async def exchange_outlook_code(code: str) -> dict:
    app = _msal_app()
    return await asyncio.to_thread(
        app.acquire_token_by_authorization_code,
        code,
        scopes=MS_SCOPES,
        redirect_uri=outlook_redirect_uri(),
    )


async def fetch_outlook_profile_email(access_token: str) -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{GRAPH_BASE}/me", headers={"Authorization": f"Bearer {access_token}"}
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("mail") or data.get("userPrincipalName")


def _strip_html(html: str) -> str:
    return re.sub(r"<[^>]+>", " ", html)


def _message_to_data(msg: dict) -> EmailMessageData:
    from_field = (msg.get("from") or {}).get("emailAddress", {})
    sender = from_field.get("address") or from_field.get("name") or "unknown"
    body = msg.get("body", {})
    body_content = body.get("content", "")
    if body.get("contentType") == "html":
        body_content = _strip_html(body_content)
    return EmailMessageData(
        provider_message_id=msg["id"],
        thread_id=msg.get("conversationId"),
        sender=sender,
        subject=msg.get("subject") or "(no subject)",
        snippet=msg.get("bodyPreview", ""),
        body=body_content,
        received_at=datetime.fromisoformat(msg["receivedDateTime"].replace("Z", "+00:00")),
        is_unread=msg.get("isRead") is False,
    )


class OutlookConnector(EmailConnector):
    async def _ensure_fresh_token(self, db: AsyncSession, account: EmailAccount) -> str:
        if account.token_expires_at > datetime.now(timezone.utc):
            return decrypt_token(account.oauth_access_token)

        app = _msal_app()
        result = await asyncio.to_thread(
            app.acquire_token_by_refresh_token,
            decrypt_token(account.oauth_refresh_token),
            scopes=MS_SCOPES,
        )
        if "access_token" not in result:
            raise ValueError(
                f"Failed to refresh Outlook token: {result.get('error_description', result)}"
            )

        account.oauth_access_token = encrypt_token(result["access_token"])
        if "refresh_token" in result:
            account.oauth_refresh_token = encrypt_token(result["refresh_token"])
        account.token_expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=result.get("expires_in", 3600)
        )
        return result["access_token"]

    async def list_messages(
        self, db: AsyncSession, account: EmailAccount, since: datetime | None = None
    ) -> list[EmailMessageData]:
        access_token = await self._ensure_fresh_token(db, account)
        params = {"$top": "25", "$orderby": "receivedDateTime desc"}
        if since is not None:
            params["$filter"] = f"receivedDateTime ge {since.isoformat()}"

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{GRAPH_BASE}/me/mailFolders/inbox/messages",
                headers={"Authorization": f"Bearer {access_token}"},
                params=params,
            )
            resp.raise_for_status()
            return [_message_to_data(m) for m in resp.json().get("value", [])]

    async def get_message(
        self, db: AsyncSession, account: EmailAccount, provider_message_id: str
    ) -> EmailMessageData:
        access_token = await self._ensure_fresh_token(db, account)
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{GRAPH_BASE}/me/messages/{provider_message_id}",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            resp.raise_for_status()
            return _message_to_data(resp.json())

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
        access_token = await self._ensure_fresh_token(db, account)
        message = {
            "subject": subject,
            "body": {"contentType": "text", "content": body},
            "toRecipients": [{"emailAddress": {"address": addr}} for addr in to],
        }
        if cc:
            message["ccRecipients"] = [{"emailAddress": {"address": addr}} for addr in cc]

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{GRAPH_BASE}/me/sendMail",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"message": message, "saveToSentItems": True},
            )
            resp.raise_for_status()
