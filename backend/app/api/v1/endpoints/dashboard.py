from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.approval import ApprovalQueueItem, ApprovalStatus
from app.models.document import Document, DocumentStatus
from app.models.email import EmailAccount, EmailMessage, EmailUrgency
from app.models.meeting import ActionItem, ActionItemStatus, Decision, DecisionStatus, Meeting
from app.models.presentation import Presentation, PresentationStatus
from app.models.user import User
from app.schemas.dashboard import DashboardSummary, UpcomingDeadlineRead

router = APIRouter()

_DOCUMENTS_DONE_STATUSES = (DocumentStatus.reviewed, DocumentStatus.failed)
_PRESENTATIONS_IN_PROGRESS_STATUSES = (PresentationStatus.draft, PresentationStatus.generating)
_UPCOMING_DEADLINES_LIMIT = 5


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

    unread_urgent_emails = await db.scalar(
        select(func.count())
        .select_from(EmailMessage)
        .join(EmailAccount, EmailMessage.account_id == EmailAccount.id)
        .where(
            EmailAccount.user_id == user.id,
            EmailMessage.is_unread.is_(True),
            EmailMessage.ai_urgency == EmailUrgency.high,
        )
    )

    return DashboardSummary(
        pending_approvals=pending,
        documents_awaiting_review=documents_awaiting_review or 0,
        presentations_in_progress=presentations_in_progress or 0,
        open_action_items=open_action_items or 0,
        upcoming_deadlines=upcoming_deadlines,
        unread_urgent_emails=unread_urgent_emails or 0,
    )
