"""Unified keyword search across the workspace (documents, meetings, emails, presentations,
calendar events, approvals) and the context assembly that grounds the chat assistant. Uses simple
Postgres ILIKE matching — no vector store — which is plenty for a single director's workspace and
keeps the free/no-infra deploy story intact."""

from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.approval import ApprovalQueueItem, ApprovalStatus
from app.models.calendar import CalendarEvent
from app.models.document import Document, DocumentReview
from app.models.email import EmailAccount, EmailMessage, EmailUrgency
from app.models.meeting import ActionItem, ActionItemStatus, Meeting
from app.models.presentation import Presentation
from app.models.user import User

_PER_TYPE_LIMIT = 8


@dataclass
class SearchResult:
    type: str  # document | meeting | email | presentation | event | approval
    id: str
    title: str
    snippet: str | None
    link: str


@dataclass
class ContextItem:
    ref: str  # short stable label Claude cites, e.g. "approval#1"
    kind: str
    text: str
    link: str


@dataclass
class WorkspaceContext:
    items: list[ContextItem] = field(default_factory=list)


def _like(term: str) -> str:
    # Escape ILIKE wildcards in the user's term so they match literally.
    cleaned = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{cleaned}%"


async def search_workspace(
    db: AsyncSession, user: User, query: str, limit: int = _PER_TYPE_LIMIT
) -> list[SearchResult]:
    q = query.strip()
    if not q:
        return []
    pat = _like(q)
    results: list[SearchResult] = []

    # Documents (filename + review summary)
    doc_rows = await db.execute(
        select(Document, DocumentReview)
        .outerjoin(DocumentReview, DocumentReview.document_id == Document.id)
        .where(
            or_(
                Document.filename.ilike(pat),
                DocumentReview.executive_summary.ilike(pat),
            )
        )
        .order_by(Document.created_at.desc())
        .limit(limit)
    )
    for doc, review in doc_rows.all():
        results.append(
            SearchResult(
                type="document",
                id=str(doc.id),
                title=doc.filename,
                snippet=(review.executive_summary[:160] if review else None),
                link=f"/documents/{doc.id}",
            )
        )

    # Meetings (title + summary)
    meeting_rows = await db.execute(
        select(Meeting)
        .where(or_(Meeting.title.ilike(pat), Meeting.summary.ilike(pat)))
        .order_by(Meeting.created_at.desc())
        .limit(limit)
    )
    for m in meeting_rows.scalars().all():
        results.append(
            SearchResult(
                type="meeting",
                id=str(m.id),
                title=m.title,
                snippet=(m.summary[:160] if m.summary else None),
                link=f"/meetings/{m.id}",
            )
        )

    # Emails (subject + sender + summary), scoped to the user's accounts
    email_rows = await db.execute(
        select(EmailMessage)
        .join(EmailAccount, EmailMessage.account_id == EmailAccount.id)
        .where(
            EmailAccount.user_id == user.id,
            or_(
                EmailMessage.subject.ilike(pat),
                EmailMessage.sender.ilike(pat),
                EmailMessage.ai_summary.ilike(pat),
            ),
        )
        .order_by(EmailMessage.received_at.desc())
        .limit(limit)
    )
    for msg in email_rows.scalars().all():
        results.append(
            SearchResult(
                type="email",
                id=str(msg.id),
                title=msg.subject,
                snippet=f"From {msg.sender}",
                link="/email",
            )
        )

    # Presentations (title + instructions)
    pres_rows = await db.execute(
        select(Presentation)
        .where(or_(Presentation.title.ilike(pat), Presentation.instructions.ilike(pat)))
        .order_by(Presentation.created_at.desc())
        .limit(limit)
    )
    for p in pres_rows.scalars().all():
        results.append(
            SearchResult(
                type="presentation",
                id=str(p.id),
                title=p.title or "Untitled presentation",
                snippet=None,
                link=f"/presentations/{p.id}",
            )
        )

    # Calendar events (title + description), scoped to the user's accounts
    event_rows = await db.execute(
        select(CalendarEvent)
        .join(EmailAccount, CalendarEvent.account_id == EmailAccount.id)
        .where(
            EmailAccount.user_id == user.id,
            or_(CalendarEvent.title.ilike(pat), CalendarEvent.description.ilike(pat)),
        )
        .order_by(CalendarEvent.start_time.desc())
        .limit(limit)
    )
    for ev in event_rows.scalars().all():
        results.append(
            SearchResult(
                type="event",
                id=str(ev.id),
                title=ev.title,
                snippet=ev.start_time.strftime("%b %d, %H:%M"),
                link="/calendar",
            )
        )

    # Approvals (preview text)
    approval_rows = await db.execute(
        select(ApprovalQueueItem)
        .where(ApprovalQueueItem.preview_text.ilike(pat))
        .order_by(ApprovalQueueItem.created_at.desc())
        .limit(limit)
    )
    for a in approval_rows.scalars().all():
        results.append(
            SearchResult(
                type="approval",
                id=str(a.id),
                title=a.preview_text[:80],
                snippet=f"{a.item_type.value.replace('_', ' ')} · {a.status.value}",
                link="/approvals",
            )
        )

    return results


async def assemble_workspace_context(
    db: AsyncSession, user: User, query: str
) -> WorkspaceContext:
    """Gather a bounded snapshot of live workspace state plus keyword hits, each item tagged with
    a `ref` and `link` the chat assistant can cite."""
    ctx = WorkspaceContext()
    counter = {"n": 0}

    def add(kind: str, text: str, link: str) -> None:
        counter["n"] += 1
        ctx.items.append(ContextItem(ref=f"{kind}#{counter['n']}", kind=kind, text=text, link=link))

    # Pending approvals
    approvals = await db.execute(
        select(ApprovalQueueItem)
        .where(ApprovalQueueItem.status == ApprovalStatus.pending)
        .order_by(ApprovalQueueItem.created_at.desc())
        .limit(15)
    )
    for a in approvals.scalars().all():
        add(
            "approval",
            f"Pending approval ({a.item_type.value.replace('_', ' ')}): {a.preview_text}",
            "/approvals",
        )

    # Open action items with owners/due dates
    action_rows = await db.execute(
        select(ActionItem, Meeting.title)
        .join(Meeting, ActionItem.meeting_id == Meeting.id)
        .where(ActionItem.status != ActionItemStatus.done)
        .order_by(ActionItem.due_date.is_(None), ActionItem.due_date.asc())
        .limit(15)
    )
    for item, meeting_title in action_rows.all():
        due = f", due {item.due_date.isoformat()}" if item.due_date else ""
        add(
            "action_item",
            f"Open action item: {item.description} (owner {item.owner}{due}; from '{meeting_title}')",
            f"/meetings/{item.meeting_id}",
        )

    # Upcoming calendar events
    now = datetime.now(timezone.utc)
    events = await db.execute(
        select(CalendarEvent)
        .join(EmailAccount, CalendarEvent.account_id == EmailAccount.id)
        .where(EmailAccount.user_id == user.id, CalendarEvent.start_time >= now)
        .order_by(CalendarEvent.start_time.asc())
        .limit(10)
    )
    for ev in events.scalars().all():
        add(
            "event",
            f"Upcoming meeting '{ev.title}' at {ev.start_time.isoformat()}",
            "/calendar",
        )

    # Urgent unread emails
    emails = await db.execute(
        select(EmailMessage)
        .join(EmailAccount, EmailMessage.account_id == EmailAccount.id)
        .where(
            EmailAccount.user_id == user.id,
            EmailMessage.is_unread.is_(True),
            EmailMessage.ai_urgency == EmailUrgency.high,
        )
        .order_by(EmailMessage.received_at.desc())
        .limit(10)
    )
    for msg in emails.scalars().all():
        add(
            "email",
            f"Urgent unread email '{msg.subject}' from {msg.sender}: {msg.ai_summary or ''}",
            "/email",
        )

    # Recent meeting summaries
    meetings = await db.execute(
        select(Meeting)
        .where(Meeting.summary.is_not(None))
        .order_by(Meeting.created_at.desc())
        .limit(8)
    )
    for m in meetings.scalars().all():
        add("meeting", f"Meeting '{m.title}': {m.summary}", f"/meetings/{m.id}")

    # Documents with risk reviews
    doc_rows = await db.execute(
        select(Document, DocumentReview)
        .join(DocumentReview, DocumentReview.document_id == Document.id)
        .order_by(DocumentReview.created_at.desc())
        .limit(8)
    )
    for doc, review in doc_rows.all():
        risks = "; ".join(
            f.get("description", "") for f in (review.risk_flags or [])[:3]
        )
        add(
            "document",
            f"Document '{doc.filename}': {review.executive_summary}"
            + (f" Risks: {risks}" if risks else ""),
            f"/documents/{doc.id}",
        )

    # Keyword hits from the question itself, to surface things the snapshot above may not include.
    for result in await search_workspace(db, user, query, limit=5):
        add(
            result.type,
            f"Search hit — {result.title}: {result.snippet or ''}",
            result.link,
        )

    return ctx
