"""Assembles the executive daily briefing: pulls what needs the director's attention today from
across the app (urgent emails, today's meetings, due action items, pending approvals, document
risks) and lets Claude write a short narrative over it. Item state ('handled') is persisted per
briefing; the item list itself is recomputed live so it always reflects current data."""

import json
from datetime import date, datetime, time, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.approval import ApprovalQueueItem, ApprovalStatus
from app.models.briefing import Briefing
from app.models.calendar import CalendarEvent
from app.models.document import Document, DocumentReview
from app.models.email import EmailAccount, EmailMessage, EmailUrgency
from app.models.meeting import ActionItem, ActionItemStatus, Meeting
from app.models.user import User
from app.services.ai.client import claude_client
from app.services.ai.schemas import ExecutiveBriefing

_ACTION_ITEMS_LIMIT = 8
_DOC_RISKS_LIMIT = 6


class Section:
    def __init__(self, section_id: str, label: str) -> None:
        self.id = section_id
        self.label = label
        self.items: list[dict] = []


async def assemble_sections(db: AsyncSession, user: User, today: date) -> list[Section]:
    """Build the live briefing sections (no handled state yet — the endpoint layers that on)."""
    sections: list[Section] = []

    # --- Urgent unread emails ---
    emails = Section("urgent_emails", "Urgent emails")
    email_rows = await db.execute(
        select(EmailMessage)
        .join(EmailAccount, EmailMessage.account_id == EmailAccount.id)
        .where(
            EmailAccount.user_id == user.id,
            EmailMessage.is_unread.is_(True),
            EmailMessage.ai_urgency == EmailUrgency.high,
        )
        .order_by(EmailMessage.received_at.desc())
    )
    for msg in email_rows.scalars().all():
        emails.items.append(
            {
                "key": f"email:{msg.id}",
                "title": msg.subject or "(no subject)",
                "subtitle": f"From {msg.sender}",
                "detail": msg.ai_summary or msg.snippet,
                "link": "/email",
                "severity": "high",
            }
        )
    sections.append(emails)

    # --- Meetings today: calendar events + processed meeting notes dated today ---
    meetings = Section("meetings_today", "Meetings today")
    day_start = datetime.combine(today, time.min, tzinfo=timezone.utc)
    day_end = datetime.combine(today, time.max, tzinfo=timezone.utc)
    calendar_rows = await db.execute(
        select(CalendarEvent)
        .join(EmailAccount, CalendarEvent.account_id == EmailAccount.id)
        .where(
            EmailAccount.user_id == user.id,
            CalendarEvent.start_time >= day_start,
            CalendarEvent.start_time <= day_end,
        )
        .order_by(CalendarEvent.start_time.asc())
    )
    for ev in calendar_rows.scalars().all():
        when = "All day" if ev.is_all_day else ev.start_time.strftime("%H:%M")
        meetings.items.append(
            {
                "key": f"calendar_event:{ev.id}",
                "title": ev.title,
                "subtitle": f"{when}" + (f" · {ev.location}" if ev.location else ""),
                "detail": ev.prep_brief.split("\n")[0] if ev.prep_brief else ev.description,
                "link": "/calendar",
            }
        )
    meeting_rows = await db.execute(
        select(Meeting)
        .where(Meeting.meeting_date == today)
        .order_by(Meeting.created_at.desc())
    )
    for m in meeting_rows.scalars().all():
        meetings.items.append(
            {
                "key": f"meeting:{m.id}",
                "title": m.title,
                "subtitle": "Meeting notes",
                "detail": m.summary,
                "link": f"/meetings/{m.id}",
            }
        )
    sections.append(meetings)

    # --- Open action items with a due date (overdue / soonest first) ---
    actions = Section("action_items", "Action items due")
    action_rows = await db.execute(
        select(ActionItem, Meeting.title)
        .join(Meeting, ActionItem.meeting_id == Meeting.id)
        .where(ActionItem.status != ActionItemStatus.done, ActionItem.due_date.is_not(None))
        .order_by(ActionItem.due_date.asc())
        .limit(_ACTION_ITEMS_LIMIT)
    )
    for item, meeting_title in action_rows.all():
        overdue = item.due_date < today
        actions.items.append(
            {
                "key": f"action_item:{item.id}",
                "title": item.description,
                "subtitle": f"{item.owner} · due {item.due_date.isoformat()}"
                + (" (overdue)" if overdue else ""),
                "detail": f"From: {meeting_title}",
                "link": f"/meetings/{item.meeting_id}",
                "severity": "high" if overdue else "medium",
            }
        )
    sections.append(actions)

    # --- Pending approvals ---
    approvals = Section("pending_approvals", "Waiting on your approval")
    approval_rows = await db.execute(
        select(ApprovalQueueItem)
        .where(ApprovalQueueItem.status == ApprovalStatus.pending)
        .order_by(ApprovalQueueItem.created_at.desc())
    )
    for a in approval_rows.scalars().all():
        approvals.items.append(
            {
                "key": f"approval:{a.id}",
                "title": a.preview_text,
                "subtitle": a.item_type.value.replace("_", " ").title(),
                "link": "/approvals",
            }
        )
    sections.append(approvals)

    # --- Document risks (high/medium flags on reviewed documents) ---
    risks = Section("document_risks", "Document risks")
    review_rows = await db.execute(
        select(DocumentReview, Document.filename)
        .join(Document, DocumentReview.document_id == Document.id)
        .order_by(DocumentReview.created_at.desc())
    )
    for review, filename in review_rows.all():
        if len(risks.items) >= _DOC_RISKS_LIMIT:
            break
        for idx, flag in enumerate(review.risk_flags or []):
            if len(risks.items) >= _DOC_RISKS_LIMIT:
                break
            severity = str(flag.get("severity", "")).lower()
            if severity not in ("high", "medium"):
                continue
            risks.items.append(
                {
                    "key": f"doc_risk:{review.id}:{idx}",
                    "title": flag.get("description", "Risk flag"),
                    "subtitle": f"{flag.get('category', 'Risk')} · {filename}",
                    "link": f"/documents/{review.document_id}",
                    "severity": severity,
                }
            )
    sections.append(risks)

    return sections


def _prompt_payload(sections: list[Section]) -> str:
    return json.dumps(
        {
            s.label: [
                {k: v for k, v in item.items() if k in ("title", "subtitle", "detail", "severity")}
                for item in s.items
            ]
            for s in sections
        },
        default=str,
    )


async def generate_summary(sections: list[Section], today: date) -> ExecutiveBriefing:
    total = sum(len(s.items) for s in sections)
    if total == 0:
        return ExecutiveBriefing(
            summary="You're all clear — nothing urgent is waiting for you today. No pending "
            "approvals, no due action items, and no urgent emails flagged.",
            top_priorities=[],
        )
    system = (
        "You are Dad, an AI executive assistant. Write a brief, calm start-of-day briefing for a "
        "director based only on the structured data provided. Be specific, prioritize ruthlessly, "
        "and never invent items that aren't in the data."
    )
    user = (
        f"Today is {today.isoformat()}. Here is everything currently needing attention, grouped "
        f"by category:\n\n{_prompt_payload(sections)}\n\nWrite the executive briefing."
    )
    return await claude_client.structured_call(
        system=system,
        user=user,
        output_model=ExecutiveBriefing,
        model=settings.claude_model_fast,
        max_tokens=1024,
    )


async def get_or_create_briefing(db: AsyncSession, user: User, today: date) -> Briefing:
    result = await db.execute(
        select(Briefing).where(Briefing.user_id == user.id, Briefing.briefing_date == today)
    )
    briefing = result.scalar_one_or_none()
    if briefing is None:
        briefing = Briefing(user_id=user.id, briefing_date=today)
        db.add(briefing)
        await db.flush()
    return briefing


async def regenerate(db: AsyncSession, user: User, today: date) -> Briefing:
    sections = await assemble_sections(db, user, today)
    result = await generate_summary(sections, today)
    briefing = await get_or_create_briefing(db, user, today)
    briefing.summary = result.summary
    briefing.top_priorities = result.top_priorities
    briefing.generated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(briefing)
    return briefing
