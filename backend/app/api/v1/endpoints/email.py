import asyncio
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.calendar import CalendarEvent
from app.models.email import EmailAccount, EmailDraft, EmailDraftStatus, EmailMessage, EmailProvider
from app.models.user import User, UserRole
from app.schemas.email import EmailAccountRead, EmailDraftRead, EmailDraftUpdate, EmailMessageRead
from app.services.email import approval as _email_approval  # noqa: F401 — registers the send-on-approve handler
from app.services.email.gmail import (
    GMAIL_SCOPES,
    build_gmail_flow,
    fetch_gmail_profile_email,
)
from app.services.email.oauth import create_oauth_state_token, decode_oauth_state_token, encrypt_token
from app.services.email.outlook import (
    MS_SCOPES,
    build_outlook_authorization_url,
    exchange_outlook_code,
    fetch_outlook_profile_email,
)
from app.tasks.queue import JobEnqueuer, get_job_queue

router = APIRouter()


# --- Connected accounts ---


@router.get("/accounts", response_model=list[EmailAccountRead])
async def list_accounts(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[EmailAccount]:
    result = await db.execute(
        select(EmailAccount)
        .where(EmailAccount.user_id == user.id)
        .order_by(EmailAccount.created_at.desc())
    )
    return list(result.scalars().all())


@router.delete("/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_account(
    account_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    """Disconnect an email/calendar account and remove its synced data. Draft emails are kept but
    detached (they become copy-to-clipboard drafts) so approval history isn't lost."""
    account = await db.get(EmailAccount, account_id)
    if account is None or account.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    message_ids = select(EmailMessage.id).where(EmailMessage.account_id == account_id)
    # Detach drafts that reference this account or its (about-to-be-deleted) messages.
    await db.execute(
        update(EmailDraft)
        .where(EmailDraft.account_id == account_id)
        .values(account_id=None, source_message_id=None)
    )
    await db.execute(
        update(EmailDraft)
        .where(EmailDraft.source_message_id.in_(message_ids))
        .values(source_message_id=None)
    )
    await db.execute(delete(CalendarEvent).where(CalendarEvent.account_id == account_id))
    await db.execute(delete(EmailMessage).where(EmailMessage.account_id == account_id))
    await db.delete(account)
    await db.commit()


# --- Gmail OAuth ---


@router.get("/gmail/connect")
async def gmail_connect(user: User = Depends(get_current_user)) -> dict:
    state = create_oauth_state_token(user.id, "gmail")
    flow = build_gmail_flow(state=state)
    auth_url, _ = flow.authorization_url(
        access_type="offline", prompt="consent", include_granted_scopes="true"
    )
    return {"authorization_url": auth_url}


@router.get("/gmail/callback")
async def gmail_callback(code: str, state: str, db: AsyncSession = Depends(get_db)) -> RedirectResponse:
    # Hit via browser redirect from Google, not an authenticated API call — the user's identity
    # comes from the signed state token minted in gmail_connect, not a Bearer token.
    user_id = decode_oauth_state_token(state, expected_provider="gmail")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OAuth state")

    flow = build_gmail_flow(state=state)
    try:
        await asyncio.to_thread(flow.fetch_token, code=code)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"OAuth exchange failed: {exc}")

    credentials = flow.credentials
    email_address = await asyncio.to_thread(fetch_gmail_profile_email, credentials)
    expires_at = (
        credentials.expiry.replace(tzinfo=timezone.utc)
        if credentials.expiry
        else datetime.now(timezone.utc) + timedelta(hours=1)
    )

    result = await db.execute(
        select(EmailAccount).where(
            EmailAccount.user_id == user_id,
            EmailAccount.provider == EmailProvider.gmail,
            EmailAccount.email_address == email_address,
        )
    )
    account = result.scalar_one_or_none()

    if account is None:
        db.add(
            EmailAccount(
                user_id=user_id,
                provider=EmailProvider.gmail,
                email_address=email_address,
                oauth_access_token=encrypt_token(credentials.token),
                oauth_refresh_token=encrypt_token(credentials.refresh_token or ""),
                token_expires_at=expires_at,
                scopes=" ".join(credentials.scopes or GMAIL_SCOPES),
            )
        )
    else:
        account.oauth_access_token = encrypt_token(credentials.token)
        if credentials.refresh_token:
            account.oauth_refresh_token = encrypt_token(credentials.refresh_token)
        account.token_expires_at = expires_at

    await db.commit()
    return RedirectResponse(url=f"{settings.frontend_url}/email?connected=gmail")


# --- Outlook OAuth ---


@router.get("/outlook/connect")
async def outlook_connect(user: User = Depends(get_current_user)) -> dict:
    state = create_oauth_state_token(user.id, "outlook")
    return {"authorization_url": build_outlook_authorization_url(state)}


@router.get("/outlook/callback")
async def outlook_callback(
    code: str, state: str, db: AsyncSession = Depends(get_db)
) -> RedirectResponse:
    user_id = decode_oauth_state_token(state, expected_provider="outlook")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OAuth state")

    token_result = await exchange_outlook_code(code)
    if "access_token" not in token_result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=token_result.get("error_description", "OAuth exchange failed"),
        )

    access_token = token_result["access_token"]
    refresh_token = token_result.get("refresh_token", "")
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=token_result.get("expires_in", 3600))
    email_address = await fetch_outlook_profile_email(access_token)

    result = await db.execute(
        select(EmailAccount).where(
            EmailAccount.user_id == user_id,
            EmailAccount.provider == EmailProvider.outlook,
            EmailAccount.email_address == email_address,
        )
    )
    account = result.scalar_one_or_none()

    if account is None:
        db.add(
            EmailAccount(
                user_id=user_id,
                provider=EmailProvider.outlook,
                email_address=email_address,
                oauth_access_token=encrypt_token(access_token),
                oauth_refresh_token=encrypt_token(refresh_token),
                token_expires_at=expires_at,
                scopes=" ".join(MS_SCOPES),
            )
        )
    else:
        account.oauth_access_token = encrypt_token(access_token)
        if refresh_token:
            account.oauth_refresh_token = encrypt_token(refresh_token)
        account.token_expires_at = expires_at

    await db.commit()
    return RedirectResponse(url=f"{settings.frontend_url}/email?connected=outlook")


# --- Sync ---


@router.post("/accounts/{account_id}/sync", status_code=status.HTTP_202_ACCEPTED)
async def trigger_sync(
    account_id: uuid.UUID,
    queue: JobEnqueuer = Depends(get_job_queue),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    account = await db.get(EmailAccount, account_id)
    if account is None or account.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    await queue.enqueue_job("sync_email_account", str(account_id))
    return {"status": "queued"}


# --- Messages ---


@router.get("/messages", response_model=list[EmailMessageRead])
async def list_messages(
    account_id: uuid.UUID | None = None,
    include_hidden: bool = False,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[EmailMessage]:
    query = (
        select(EmailMessage)
        .join(EmailAccount, EmailMessage.account_id == EmailAccount.id)
        .where(EmailAccount.user_id == user.id)
        .order_by(EmailMessage.received_at.desc())
    )
    if account_id is not None:
        query = query.where(EmailMessage.account_id == account_id)
    if not include_hidden:
        query = query.where(EmailMessage.is_hidden.is_(False))

    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("/messages/{message_id}/hide", status_code=status.HTTP_204_NO_CONTENT)
async def hide_message(
    message_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    message = await _get_owned_message(db, user, message_id)
    message.is_hidden = True
    await db.commit()


@router.post("/messages/{message_id}/unhide", status_code=status.HTTP_204_NO_CONTENT)
async def unhide_message(
    message_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    message = await _get_owned_message(db, user, message_id)
    message.is_hidden = False
    await db.commit()


async def _get_owned_message(db: AsyncSession, user: User, message_id: uuid.UUID) -> EmailMessage:
    result = await db.execute(
        select(EmailMessage)
        .join(EmailAccount, EmailMessage.account_id == EmailAccount.id)
        .where(EmailMessage.id == message_id, EmailAccount.user_id == user.id)
    )
    message = result.scalar_one_or_none()
    if message is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    return message


@router.get("/messages/{message_id}", response_model=EmailMessageRead)
async def get_message(
    message_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> EmailMessage:
    return await _get_owned_message(db, user, message_id)


# --- Drafts (viewed / edited from the approval queue before approval) ---


@router.get("/drafts/{draft_id}", response_model=EmailDraftRead)
async def get_draft(
    draft_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> EmailDraft:
    draft = await db.get(EmailDraft, draft_id)
    if draft is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
    return draft


@router.patch("/drafts/{draft_id}", response_model=EmailDraftRead)
async def update_draft(
    draft_id: uuid.UUID,
    payload: EmailDraftUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> EmailDraft:
    draft = await db.get(EmailDraft, draft_id)
    if draft is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
    # Only the author or an approver (director/admin) can edit, and only before it's actioned.
    if draft.created_by_id != user.id and user.role not in (UserRole.director, UserRole.admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to edit this draft")
    if draft.status != EmailDraftStatus.pending_approval:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Draft is {draft.status.value} and can no longer be edited",
        )

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(draft, field, value)
    await db.commit()
    await db.refresh(draft)
    return draft


class DraftReplyRequest(BaseModel):
    instructions: str | None = None


@router.post("/messages/{message_id}/draft-reply", status_code=status.HTTP_202_ACCEPTED)
async def trigger_draft_reply(
    message_id: uuid.UUID,
    payload: DraftReplyRequest,
    queue: JobEnqueuer = Depends(get_job_queue),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    await _get_owned_message(db, user, message_id)
    await queue.enqueue_job("draft_email_reply", str(message_id), payload.instructions)
    return {"status": "queued"}
