"""Tests for the approval dispatch/send-gating logic — the core safety invariant of the whole
app ("nothing sends without director/admin approval"). Uses a fake email connector; never
touches a real Gmail/Outlook account.
"""

import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.models.approval import ApprovalItemType, ApprovalQueueItem
from app.models.email import EmailAccount, EmailDraft, EmailDraftStatus, EmailProvider
from app.services.approvals.service import approve_item, create_approval_item, reject_item
from app.services.email.oauth import encrypt_token
from tests.fakes import FakeEmailConnector


def test_send_message_is_only_ever_called_from_the_approval_handler():
    """Structural regression guard: send_message must only be invoked from the one code path
    that runs after director/admin approval — never from a draft-editing/creation endpoint.
    """
    app_dir = Path(__file__).resolve().parent.parent / "app"
    call_pattern = re.compile(r"\.send_message\(")

    calling_files = [
        # as_posix() so the comparison holds on Windows (backslashes) too.
        py_file.relative_to(app_dir).as_posix()
        for py_file in app_dir.rglob("*.py")
        if call_pattern.search(py_file.read_text(encoding="utf-8"))
    ]

    assert calling_files == ["services/email/approval.py"], (
        "send_message() must only be called from services/email/approval.py (the "
        f"approval-execution path). Found calls in: {calling_files}"
    )


@pytest.fixture
def fake_connector(monkeypatch) -> FakeEmailConnector:
    connector = FakeEmailConnector()
    monkeypatch.setattr("app.services.email.approval.get_connector", lambda provider: connector)
    return connector


async def _make_account(db_session, user) -> EmailAccount:
    account = EmailAccount(
        user_id=user.id,
        provider=EmailProvider.gmail,
        email_address="director@example.com",
        oauth_access_token=encrypt_token("access"),
        oauth_refresh_token=encrypt_token("refresh"),
        token_expires_at=datetime.now(timezone.utc),
        scopes="mail",
    )
    db_session.add(account)
    await db_session.commit()
    await db_session.refresh(account, attribute_names=["created_at"])
    return account


async def test_approving_email_draft_with_account_sends_via_connector(
    db_session, make_user, fake_connector
):
    user = await make_user()
    account = await _make_account(db_session, user)
    draft = EmailDraft(
        created_by_id=user.id,
        account_id=account.id,
        to_addresses=["someone@example.com"],
        subject="Hi",
        body="Body",
    )
    db_session.add(draft)
    await db_session.commit()
    await db_session.refresh(draft, attribute_names=["created_at"])

    item = await create_approval_item(
        db_session,
        item_type=ApprovalItemType.email_draft,
        reference_id=draft.id,
        preview_text="Hi",
        requested_by_id=user.id,
    )
    await db_session.commit()

    await approve_item(db_session, item, user)

    assert len(fake_connector.sent_messages) == 1
    assert fake_connector.sent_messages[0]["to"] == ["someone@example.com"]
    await db_session.refresh(draft)
    assert draft.status == EmailDraftStatus.sent
    assert draft.sent_at is not None


async def test_approving_email_draft_without_account_does_not_send(
    db_session, make_user, fake_connector
):
    user = await make_user()
    draft = EmailDraft(created_by_id=user.id, account_id=None, subject="Hi", body="Body")
    db_session.add(draft)
    await db_session.commit()
    await db_session.refresh(draft, attribute_names=["created_at"])

    item = await create_approval_item(
        db_session,
        item_type=ApprovalItemType.email_draft,
        reference_id=draft.id,
        preview_text="Hi",
        requested_by_id=user.id,
    )
    await db_session.commit()

    await approve_item(db_session, item, user)

    assert fake_connector.sent_messages == []
    await db_session.refresh(draft)
    assert draft.status == EmailDraftStatus.approved


async def test_rejecting_email_draft_never_sends(db_session, make_user, fake_connector):
    user = await make_user()
    account = await _make_account(db_session, user)
    draft = EmailDraft(
        created_by_id=user.id,
        account_id=account.id,
        to_addresses=["x@example.com"],
        subject="Hi",
        body="Body",
    )
    db_session.add(draft)
    await db_session.commit()
    await db_session.refresh(draft, attribute_names=["created_at"])

    item = await create_approval_item(
        db_session,
        item_type=ApprovalItemType.email_draft,
        reference_id=draft.id,
        preview_text="Hi",
        requested_by_id=user.id,
    )
    await db_session.commit()

    await reject_item(db_session, item, user)

    assert fake_connector.sent_messages == []
    await db_session.refresh(draft)
    assert draft.status == EmailDraftStatus.rejected


async def test_approving_item_with_no_registered_handler_raises(db_session, make_user, monkeypatch):
    from app.services.approvals import service as approvals_service

    # Temporarily unregister a real, otherwise-handled item type to exercise the "no handler"
    # branch without depending on a specific dead/unused enum value.
    monkeypatch.delitem(
        approvals_service._HANDLERS, ApprovalItemType.presentation_export, raising=False
    )

    user = await make_user()
    item = ApprovalQueueItem(
        item_type=ApprovalItemType.presentation_export,
        reference_id=uuid.uuid4(),
        preview_text="n/a",
        requested_by_id=user.id,
    )
    db_session.add(item)
    await db_session.commit()

    with pytest.raises(ValueError, match="No approval handler registered"):
        await approve_item(db_session, item, user)
