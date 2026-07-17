"""Registers the approval handler for email drafts. Imported (for its side effect) from the
meetings endpoint module so registration happens at app startup.

This is the one place a real email actually goes out: approving a draft that has a connected
account_id calls the provider connector's send_message. Approving a draft with no account_id
(meeting-sourced, Phase 3, no inbox connected yet) just marks it approved so the UI unlocks
"copy to clipboard" instead.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.approval import ApprovalItemType
from app.models.email import EmailAccount, EmailDraft, EmailDraftStatus, EmailMessage
from app.services.approvals.service import register_handler
from app.services.email.base import get_connector


class EmailDraftApprovalHandler:
    async def on_approve(self, db: AsyncSession, reference_id: uuid.UUID) -> None:
        draft = await db.get(EmailDraft, reference_id)
        if draft is None:
            return

        if draft.account_id is None:
            draft.status = EmailDraftStatus.approved
            return

        account = await db.get(EmailAccount, draft.account_id)
        if account is None:
            raise ValueError("Email account not found for this draft")

        # Reply drafts carry the inbound message they answer — thread the send into that
        # conversation. Meeting-sourced drafts have no source message and go out as new mail.
        reply_to = (
            await db.get(EmailMessage, draft.source_message_id)
            if draft.source_message_id is not None
            else None
        )

        connector = get_connector(account.provider)
        await connector.send_message(
            db,
            account,
            to=draft.to_addresses,
            cc=draft.cc_addresses,
            subject=draft.subject,
            body=draft.body,
            reply_to=reply_to,
        )
        draft.status = EmailDraftStatus.sent
        draft.sent_at = datetime.now(timezone.utc)

    async def on_reject(self, db: AsyncSession, reference_id: uuid.UUID) -> None:
        draft = await db.get(EmailDraft, reference_id)
        if draft is not None:
            draft.status = EmailDraftStatus.rejected


register_handler(ApprovalItemType.email_draft, EmailDraftApprovalHandler())
