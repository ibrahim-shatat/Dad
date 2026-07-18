from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.approval import ApprovalItemType, ApprovalQueueItem, ApprovalStatus
from app.models.calendar import CalendarEvent
from app.models.document import Document, DocumentStatus
from app.models.email import EmailAccount, EmailMessage, EmailProvider, EmailUrgency
from app.models.meeting import ActionItem, ActionItemStatus, Decision, DecisionStatus, Meeting
from app.models.presentation import Presentation, PresentationStatus
from app.models.user import User
from app.schemas.dashboard import AttentionItem, DashboardSummary, UpcomingDeadlineRead

router = APIRouter()

_DOCUMENTS_DONE_STATUSES = (DocumentStatus.reviewed, DocumentStatus.failed)
_PRESENTATIONS_IN_PROGRESS_STATUSES = (PresentationStatus.draft, PresentationStatus.generating)
_UPCOMING_DEADLINES_LIMIT = 5
_ATTENTION_LIMIT = 7
_NEEDS_WORK_LIMIT = 8
_PROVIDER_LABELS = {EmailProvider.gmail: "Gmail", EmailProvider.outlook: "Outlook"}


@router.get("", response_model=DashboardSummary)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DashboardSummary:
    pending_result = await db.execute(
        select(ApprovalQueueItem)
        .where(ApprovalQueueItem.status == ApprovalStatus.pending)
        .order_by(ApprovalQueueItem.created_at.desc())
    )
    pending = list(pending_result.scalars().all())

    documents_awaiting_review = await db.scalar(
        select(func.count())
        .select_from(Document)
        .where(Document.status.notin_(_DOCUMENTS_DONE_STATUSES))
    )

    presentations_in_progress = await db.scalar(
        select(func.count())
        .select_from(Presentation)
        .where(Presentation.status.in_(_PRESENTATIONS_IN_PROGRESS_STATUSES))
    )

    open_action_items = await db.scalar(
        select(func.count())
        .select_from(ActionItem)
        .where(ActionItem.status != ActionItemStatus.done)
    )

    action_item_rows = await db.execute(
        select(ActionItem, Meeting.title)
        .join(Meeting, ActionItem.meeting_id == Meeting.id)
        .where(ActionItem.status != ActionItemStatus.done, ActionItem.due_date.is_not(None))
    )
    decision_rows = await db.execute(
        select(Decision, Meeting.title)
        .join(Meeting, Decision.meeting_id == Meeting.id)
        .where(Decision.status == DecisionStatus.pending, Decision.deadline.is_not(None))
    )

    upcoming_deadlines = [
        UpcomingDeadlineRead(
            type="action_item",
            id=item.id,
            description=item.description,
            owner=item.owner,
            due_date=item.due_date,
            meeting_id=item.meeting_id,
            meeting_title=meeting_title,
        )
        for item, meeting_title in action_item_rows.all()
    ] + [
        UpcomingDeadlineRead(
            type="decision",
            id=decision.id,
            description=decision.description,
            owner=decision.decided_by,
            due_date=decision.deadline,
            meeting_id=decision.meeting_id,
            meeting_title=meeting_title,
        )
        for decision, meeting_title in decision_rows.all()
    ]
    upcoming_deadlines.sort(key=lambda d: d.due_date)
    upcoming_deadlines = upcoming_deadlines[:_UPCOMING_DEADLINES_LIMIT]

    urgent_email_rows = (
        await db.execute(
            select(EmailMessage, EmailAccount.provider)
            .join(EmailAccount, EmailMessage.account_id == EmailAccount.id)
            .where(
                EmailAccount.user_id == user.id,
                EmailMessage.is_unread.is_(True),
                EmailMessage.is_hidden.is_(False),
                EmailMessage.ai_urgency == EmailUrgency.high,
            )
            .order_by(EmailMessage.received_at.desc())
        )
    ).all()
    unread_urgent_emails = len(urgent_email_rows)

    now = datetime.now(timezone.utc)
    todays_event_rows = (
        await db.execute(
            select(CalendarEvent)
            .join(EmailAccount, CalendarEvent.account_id == EmailAccount.id)
            .where(
                EmailAccount.user_id == user.id,
                CalendarEvent.start_time >= now,
                CalendarEvent.start_time <= now + timedelta(hours=24),
            )
            .order_by(CalendarEvent.start_time.asc())
        )
    ).scalars().all()

    needs_attention = _build_needs_attention(
        pending=pending,
        urgent_emails=urgent_email_rows,
        deadlines=upcoming_deadlines,
        events=todays_event_rows,
        today=now.date(),
    )

    # "What needs work" — the director's own in-progress queue (distinct from the time-sensitive
    # attention feed): documents being reviewed, presentations being built, and open tasks that
    # aren't already surfaced as overdue/today deadlines.
    docs_in_progress = (
        await db.execute(
            select(Document)
            .where(Document.status.notin_(_DOCUMENTS_DONE_STATUSES))
            .order_by(Document.created_at.desc())
            .limit(_NEEDS_WORK_LIMIT)
        )
    ).scalars().all()
    pres_in_progress = (
        await db.execute(
            select(Presentation)
            .where(Presentation.status.in_(_PRESENTATIONS_IN_PROGRESS_STATUSES))
            .order_by(Presentation.created_at.desc())
            .limit(_NEEDS_WORK_LIMIT)
        )
    ).scalars().all()
    open_tasks = (
        await db.execute(
            select(ActionItem, Meeting.title)
            .join(Meeting, ActionItem.meeting_id == Meeting.id)
            .where(
                ActionItem.status != ActionItemStatus.done,
                or_(ActionItem.due_date.is_(None), ActionItem.due_date > now.date()),
            )
            .order_by(ActionItem.created_at.desc())
            .limit(_NEEDS_WORK_LIMIT)
        )
    ).all()

    needs_work = _build_needs_work(docs_in_progress, pres_in_progress, open_tasks)

    return DashboardSummary(
        pending_approvals=pending,
        documents_awaiting_review=documents_awaiting_review or 0,
        presentations_in_progress=presentations_in_progress or 0,
        open_action_items=open_action_items or 0,
        upcoming_deadlines=upcoming_deadlines,
        unread_urgent_emails=unread_urgent_emails,
        needs_attention=needs_attention,
        needs_work=needs_work,
    )


def _build_needs_work(documents, presentations, tasks) -> list[AttentionItem]:
    items: list[AttentionItem] = []
    for item, meeting_title in tasks:
        subtitle = f"{item.owner} · {meeting_title}" if item.owner else meeting_title
        items.append(
            AttentionItem(
                kind="task",
                title=item.description,
                subtitle=subtitle,
                badge="To do",
                tone="default",
                link=f"/meetings/{item.meeting_id}",
                when=None,
            )
        )
    for doc in documents:
        items.append(
            AttentionItem(
                kind="document",
                title=doc.filename,
                subtitle="AI review in progress",
                badge="Reviewing",
                tone="default",
                link="/documents",
                when=None,
            )
        )
    for pres in presentations:
        items.append(
            AttentionItem(
                kind="presentation",
                title=pres.title,
                subtitle="Being generated",
                badge="In progress",
                tone="default",
                link="/presentations",
                when=None,
            )
        )
    return items[:_NEEDS_WORK_LIMIT]


def _truncate(text: str, limit: int = 90) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _build_needs_attention(
    *,
    pending: list[ApprovalQueueItem],
    urgent_emails: list,
    deadlines: list[UpcomingDeadlineRead],
    events: list[CalendarEvent],
    today: date,
) -> list[AttentionItem]:
    """Merge the pressing items across surfaces into one priority-ranked feed. Priority (higher =
    more urgent): overdue deadline > urgent email > pending approval > deadline due today >
    meeting in the next 24h."""
    scored: list[tuple[int, AttentionItem]] = []

    for message, provider in urgent_emails:
        scored.append(
            (
                90,
                AttentionItem(
                    kind="email",
                    title=message.sender,
                    subtitle=_truncate(message.subject),
                    badge=f"Urgent · {_PROVIDER_LABELS.get(provider, 'Email')}",
                    tone="urgent",
                    link="/email",
                    when=message.received_at,
                ),
            )
        )

    for item in pending:
        label = "Email to send" if item.item_type == ApprovalItemType.email_draft else "To approve"
        by = f" · {item.requested_by_name}" if item.requested_by_name else ""
        scored.append(
            (
                80,
                AttentionItem(
                    kind="approval",
                    title=_truncate(item.preview_text),
                    subtitle=f"Waiting on your approval{by}",
                    badge=label,
                    tone="warning",
                    link="/approvals",
                    when=item.created_at,
                ),
            )
        )

    for d in deadlines:
        if d.due_date < today:
            priority, badge, tone = 100, "Overdue", "urgent"
        elif d.due_date == today:
            priority, badge, tone = 75, "Due today", "warning"
        else:
            continue
        scored.append(
            (
                priority,
                AttentionItem(
                    kind="deadline",
                    title=d.description,
                    subtitle=f"{d.owner} · {d.meeting_title}",
                    badge=badge,
                    tone=tone,
                    link=f"/meetings/{d.meeting_id}",
                    when=None,
                ),
            )
        )

    for event in events:
        detail = event.location or event.organizer or (
            f"{len(event.attendees)} attendees" if event.attendees else "On your calendar"
        )
        scored.append(
            (
                60,
                AttentionItem(
                    kind="event",
                    title=event.title,
                    subtitle=detail,
                    badge="Upcoming",
                    tone="default",
                    link="/calendar",
                    when=event.start_time,
                ),
            )
        )

    # Highest priority first; within a tier keep the query order (recent / soonest already sorted).
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [item for _, item in scored[:_ATTENTION_LIMIT]]
