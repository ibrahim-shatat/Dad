import re
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from app.core.config import settings
from app.db.session import async_session_maker
from app.models.approval import ApprovalItemType
from app.models.document import Document, DocumentReview, DocumentStatus
from app.models.email import EmailAccount, EmailDraft, EmailMessage
from app.models.meeting import ActionItem, Decision, DecisionStatus, Meeting, MeetingStatus
from app.models.notification import NotificationType
from app.models.presentation import Presentation, PresentationStatus
from app.services.ai.client import claude_client
from app.services.ai.prompts import email as email_prompts
from app.services.ai.prompts import meeting as meeting_prompts
from app.services.ai.prompts import presentation as presentation_prompts
from app.services.ai.prompts.document_review import SYSTEM_PROMPT, build_user_prompt
from app.services.ai.schemas import (
    DocumentReviewResult,
    EmailReplyDraft,
    EmailSummary,
    MeetingExtraction,
    PresentationOutline,
)
from app.services.approvals.service import create_approval_item
from app.services.documents.extraction import extract_text
from app.services.documents.storage import get_storage_backend
from app.services.email.base import get_connector
from app.services.notifications.service import create_notification
from app.services.presentations.builder import build_presentation

_EMAIL_ADDRESS_RE = re.compile(r"[\w.\-+]+@[\w\-]+\.[\w.\-]+")


def _parse_email_address(sender: str) -> str | None:
    match = _EMAIL_ADDRESS_RE.search(sender)
    return match.group(0) if match else None


async def extract_document_text(ctx: dict[str, Any], document_id: str) -> None:
    doc_id = uuid.UUID(document_id)
    storage = get_storage_backend()

    async with async_session_maker() as db:
        document = await db.get(Document, doc_id)
        if document is None:
            return

        document.status = DocumentStatus.extracting
        await db.commit()

        try:
            data = await storage.read(document.storage_key)
            text = extract_text(data, document.mime_type, document.filename)
        except Exception as exc:
            document.status = DocumentStatus.failed
            document.failure_reason = f"Text extraction failed: {exc}"
            await db.commit()
            return

        document.extracted_text = text
        document.status = DocumentStatus.extracted
        await db.commit()

    await ctx["redis"].enqueue_job("review_document", document_id)


async def review_document(ctx: dict[str, Any], document_id: str) -> None:
    doc_id = uuid.UUID(document_id)

    async with async_session_maker() as db:
        document = await db.get(Document, doc_id)
        if document is None or not document.extracted_text:
            return

        document.status = DocumentStatus.reviewing
        await db.commit()

        try:
            result = await claude_client.structured_call(
                system=SYSTEM_PROMPT,
                user=build_user_prompt(document.extracted_text, document.instructions),
                output_model=DocumentReviewResult,
            )
        except Exception as exc:
            document.status = DocumentStatus.failed
            document.failure_reason = f"AI review failed: {exc}"
            await db.commit()
            return

        review = DocumentReview(
            document_id=document.id,
            executive_summary=result.executive_summary,
            risk_flags=[flag.model_dump() for flag in result.risk_flags],
            suggested_rewrite=result.suggested_rewrite,
            model_used=settings.claude_model_smart,
        )
        db.add(review)
        document.status = DocumentStatus.reviewed

        await create_notification(
            db,
            user_id=document.uploaded_by_id,
            type=NotificationType.document_reviewed,
            title=f"Document reviewed: {document.filename}",
            body=result.executive_summary[:200],
            link=f"/documents/{document.id}",
        )
        await db.commit()


async def generate_presentation(ctx: dict[str, Any], presentation_id: str) -> None:
    pres_id = uuid.UUID(presentation_id)

    async with async_session_maker() as db:
        presentation = await db.get(Presentation, pres_id)
        if presentation is None:
            return

        source_text = presentation.source_text
        if not source_text and presentation.source_document_id is not None:
            document = await db.get(Document, presentation.source_document_id)
            source_text = document.extracted_text if document else None

        if not source_text:
            presentation.status = PresentationStatus.failed
            presentation.failure_reason = "No source text available to generate a presentation from."
            await db.commit()
            return

        presentation.status = PresentationStatus.generating
        await db.commit()

        try:
            outline = await claude_client.structured_call(
                system=presentation_prompts.SYSTEM_PROMPT,
                user=presentation_prompts.build_user_prompt(source_text, presentation.instructions),
                output_model=PresentationOutline,
            )
        except Exception as exc:
            presentation.status = PresentationStatus.failed
            presentation.failure_reason = f"AI outline generation failed: {exc}"
            await db.commit()
            return

        presentation.title = presentation.title or outline.title
        presentation.structured_content = outline.model_dump()

        try:
            pptx_bytes = build_presentation(outline)
            storage = get_storage_backend()
            storage_key = await storage.save(pptx_bytes, f"{presentation.title}.pptx")
        except Exception as exc:
            presentation.status = PresentationStatus.failed
            presentation.failure_reason = f"Presentation file generation failed: {exc}"
            await db.commit()
            return

        presentation.storage_key = storage_key
        presentation.status = PresentationStatus.ready
        await db.commit()

        await create_approval_item(
            db,
            item_type=ApprovalItemType.presentation_export,
            reference_id=presentation.id,
            preview_text=f"Presentation ready for approval: {presentation.title}",
            requested_by_id=presentation.created_by_id,
        )
        await db.commit()


async def process_meeting(ctx: dict[str, Any], meeting_id: str) -> None:
    m_id = uuid.UUID(meeting_id)

    async with async_session_maker() as db:
        meeting = await db.get(Meeting, m_id)
        if meeting is None:
            return

        try:
            extraction = await claude_client.structured_call(
                system=meeting_prompts.build_system_prompt(),
                user=meeting_prompts.build_user_prompt(meeting.source_text, meeting.instructions),
                output_model=MeetingExtraction,
            )
        except Exception as exc:
            meeting.status = MeetingStatus.failed
            meeting.failure_reason = f"AI extraction failed: {exc}"
            await db.commit()
            return

        meeting.summary = extraction.summary
        meeting.status = MeetingStatus.processed

        for item in extraction.action_items:
            db.add(
                ActionItem(
                    meeting_id=meeting.id,
                    description=item.description,
                    owner=item.owner,
                    due_date=item.due_date,
                )
            )

        for decision in extraction.decisions:
            db.add(
                Decision(
                    meeting_id=meeting.id,
                    description=decision.description,
                    decided_by=decision.decided_by,
                    status=DecisionStatus(decision.status),
                    deadline=decision.deadline,
                )
            )

        await create_notification(
            db,
            user_id=meeting.created_by_id,
            type=NotificationType.meeting_processed,
            title=f"Meeting processed: {meeting.title}",
            body=extraction.summary[:200],
            link=f"/meetings/{meeting.id}",
        )
        await db.commit()

        if extraction.follow_up_email is not None:
            draft = EmailDraft(
                created_by_id=meeting.created_by_id,
                source_meeting_id=meeting.id,
                subject=extraction.follow_up_email.subject,
                body=extraction.follow_up_email.body,
            )
            db.add(draft)
            await db.flush()

            await create_approval_item(
                db,
                item_type=ApprovalItemType.email_draft,
                reference_id=draft.id,
                preview_text=f"Follow-up email: {extraction.follow_up_email.subject}",
                requested_by_id=meeting.created_by_id,
            )
            await db.commit()


async def sync_email_account(ctx: dict[str, Any], account_id: str) -> None:
    acc_id = uuid.UUID(account_id)

    async with async_session_maker() as db:
        account = await db.get(EmailAccount, acc_id)
        if account is None:
            return

        connector = get_connector(account.provider)
        try:
            messages = await connector.list_messages(db, account, since=account.last_synced_at)
        except Exception:
            # Transient sync failure (expired grant, rate limit, network blip) — the next
            # scheduled sync will retry. Not surfaced anywhere yet; account.last_synced_at only
            # advances on success so nothing is silently skipped.
            return

        for msg_data in messages:
            existing = await db.execute(
                select(EmailMessage).where(
                    EmailMessage.account_id == account.id,
                    EmailMessage.provider_message_id == msg_data.provider_message_id,
                )
            )
            if existing.scalar_one_or_none() is not None:
                continue

            try:
                summary = await claude_client.structured_call(
                    system=email_prompts.SUMMARY_SYSTEM_PROMPT,
                    user=email_prompts.build_summary_prompt(
                        msg_data.sender, msg_data.subject, msg_data.body
                    ),
                    output_model=EmailSummary,
                    model=settings.claude_model_fast,
                )
                ai_summary, ai_urgency = summary.summary, summary.urgency
            except Exception:
                ai_summary, ai_urgency = None, None

            db.add(
                EmailMessage(
                    account_id=account.id,
                    provider_message_id=msg_data.provider_message_id,
                    thread_id=msg_data.thread_id,
                    sender=msg_data.sender,
                    subject=msg_data.subject,
                    snippet=msg_data.snippet,
                    received_at=msg_data.received_at,
                    is_unread=msg_data.is_unread,
                    ai_summary=ai_summary,
                    ai_urgency=ai_urgency,
                )
            )

            if ai_urgency == "high":
                await create_notification(
                    db,
                    user_id=account.user_id,
                    type=NotificationType.urgent_email,
                    title=f"Urgent email: {msg_data.subject}",
                    body=f"From {msg_data.sender}",
                    link="/email",
                )

        account.last_synced_at = datetime.now(timezone.utc)
        await db.commit()


async def draft_email_reply(
    ctx: dict[str, Any], message_id: str, instructions: str | None = None
) -> None:
    msg_id = uuid.UUID(message_id)

    async with async_session_maker() as db:
        message = await db.get(EmailMessage, msg_id)
        if message is None:
            return
        account = await db.get(EmailAccount, message.account_id)
        if account is None:
            return

        connector = get_connector(account.provider)
        try:
            # Fetch the full body live rather than persisting it — EmailMessage only stores a
            # snippet at rest to limit how much sensitive email content we retain.
            full_message = await connector.get_message(db, account, message.provider_message_id)
        except Exception:
            return

        try:
            reply = await claude_client.structured_call(
                system=email_prompts.REPLY_SYSTEM_PROMPT,
                user=email_prompts.build_reply_prompt(
                    full_message.sender, full_message.subject, full_message.body, instructions
                ),
                output_model=EmailReplyDraft,
            )
        except Exception:
            return

        to_address = _parse_email_address(full_message.sender)
        draft = EmailDraft(
            created_by_id=account.user_id,
            account_id=account.id,
            source_message_id=message.id,
            to_addresses=[to_address] if to_address else [],
            subject=reply.subject,
            body=reply.body,
        )
        db.add(draft)
        await db.flush()

        await create_approval_item(
            db,
            item_type=ApprovalItemType.email_draft,
            reference_id=draft.id,
            preview_text=f"Reply to {message.sender}: {reply.subject}",
            requested_by_id=account.user_id,
        )
        await db.commit()


async def sync_all_email_accounts(ctx: dict[str, Any]) -> None:
    """Cron entry point — arq's cron_jobs is a static list, so periodic per-account sync is done
    by fanning out from one scheduled job rather than registering a cron per account."""
    async with async_session_maker() as db:
        result = await db.execute(select(EmailAccount.id))
        account_ids = [row[0] for row in result.all()]

    for account_id in account_ids:
        await sync_email_account(ctx, str(account_id))
