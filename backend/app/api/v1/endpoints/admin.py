from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_role
from app.db.session import get_db
from app.models.audit import AuditLog
from app.models.document import Document, DocumentStatus
from app.models.email import EmailAccount
from app.models.meeting import Meeting, MeetingStatus
from app.models.presentation import Presentation, PresentationStatus
from app.models.user import User, UserRole
from app.schemas.admin import (
    AuditLogRead,
    ConnectedAccountHealth,
    SystemHealth,
)

router = APIRouter(dependencies=[Depends(require_role(UserRole.admin))])


@router.get("/audit", response_model=list[AuditLogRead])
async def list_audit_log(
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
) -> list[AuditLog]:
    result = await db.execute(
        select(AuditLog).order_by(AuditLog.created_at.desc()).limit(min(limit, 500))
    )
    return list(result.scalars().all())


async def _count(db: AsyncSession, model, condition) -> int:
    return (await db.scalar(select(func.count()).select_from(model).where(condition))) or 0


@router.get("/health", response_model=SystemHealth)
async def system_health(db: AsyncSession = Depends(get_db)) -> SystemHealth:
    total_users = (await db.scalar(select(func.count()).select_from(User))) or 0
    active_users = await _count(db, User, User.is_active.is_(True))
    failed_documents = await _count(db, Document, Document.status == DocumentStatus.failed)
    failed_meetings = await _count(db, Meeting, Meeting.status == MeetingStatus.failed)
    failed_presentations = await _count(
        db, Presentation, Presentation.status == PresentationStatus.failed
    )

    account_rows = await db.execute(
        select(EmailAccount).order_by(EmailAccount.created_at.desc())
    )
    connected_accounts = [
        ConnectedAccountHealth(
            email_address=a.email_address,
            provider=a.provider.value,
            last_synced_at=a.last_synced_at,
        )
        for a in account_rows.scalars().all()
    ]

    failure_rows = await db.execute(
        select(AuditLog)
        .where(AuditLog.action == "job.failed")
        .order_by(AuditLog.created_at.desc())
        .limit(20)
    )
    recent_job_failures = list(failure_rows.scalars().all())

    return SystemHealth(
        total_users=total_users,
        active_users=active_users,
        failed_documents=failed_documents,
        failed_meetings=failed_meetings,
        failed_presentations=failed_presentations,
        connected_accounts=connected_accounts,
        recent_job_failures=recent_job_failures,
    )
