"""Tests for M6 calendar: syncing events (mocked connector), prep-brief generation, and
post-meeting follow-up drafting — all without touching a real Google/Microsoft calendar or the
Anthropic API."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.models.approval import ApprovalItemType, ApprovalQueueItem
from app.models.calendar import CalendarEvent
from app.models.email import EmailAccount, EmailDraft, EmailProvider
from app.services.ai.schemas import FollowUpEmailDraft, MeetingPrepBrief
from app.services.calendar.base import CalendarEventData
from app.services.email.oauth import encrypt_token
from app.tasks import jobs


async def _make_account(db_session, user) -> EmailAccount:
    account = EmailAccount(
        user_id=user.id,
        provider=EmailProvider.gmail,
        email_address="director@example.com",
        oauth_access_token=encrypt_token("access"),
        oauth_refresh_token=encrypt_token("refresh"),
        token_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        scopes="mail calendar",
    )
    db_session.add(account)
    await db_session.commit()
    await db_session.refresh(account, attribute_names=["created_at"])
    return account


class _FakeCalendarConnector:
    def __init__(self, events: list[CalendarEventData]) -> None:
        self._events = events

    async def list_upcoming_events(self, db, account, *, time_min, time_max):
        return self._events


async def test_sync_calendar_account_upserts_events(db_session, make_user, fake_ctx, monkeypatch):
    user = await make_user()
    account = await _make_account(db_session, user)
    start = datetime.now(timezone.utc) + timedelta(days=1)
    events = [
        CalendarEventData(
            provider_event_id="evt-1",
            title="Board sync",
            description="Quarterly review",
            location="Room 4",
            start_time=start,
            end_time=start + timedelta(hours=1),
            is_all_day=False,
            organizer="chair@example.com",
            attendees=["chair@example.com", "director@example.com"],
        )
    ]
    monkeypatch.setattr(jobs, "get_calendar_connector", lambda provider: _FakeCalendarConnector(events))

    await jobs.sync_calendar_account(fake_ctx, str(account.id))

    result = await db_session.execute(select(CalendarEvent))
    stored = result.scalars().all()
    assert len(stored) == 1
    assert stored[0].title == "Board sync"

    # Re-syncing the same event updates in place rather than duplicating.
    events[0].title = "Board sync (updated)"
    await jobs.sync_calendar_account(fake_ctx, str(account.id))
    db_session.expire_all()  # drop identity-map cache so we read what the job's session wrote
    result = await db_session.execute(select(CalendarEvent))
    stored = result.scalars().all()
    assert len(stored) == 1
    assert stored[0].title == "Board sync (updated)"


async def test_generate_event_prep_writes_brief(db_session, make_user, fake_ctx, mock_claude):
    user = await make_user()
    account = await _make_account(db_session, user)
    event = CalendarEvent(
        account_id=account.id,
        provider_event_id="evt-2",
        title="Vendor negotiation",
        start_time=datetime.now(timezone.utc) + timedelta(days=1),
        attendees=["vendor@example.com"],
    )
    db_session.add(event)
    await db_session.commit()

    mock_claude.return_value = MeetingPrepBrief(
        context="Negotiating the renewal.",
        talking_points=["Hold firm on price"],
        questions_to_ask=["What's their floor?"],
        suggested_actions=["Bring last year's invoice"],
    )

    await jobs.generate_event_prep(fake_ctx, str(event.id))

    await db_session.refresh(event)
    assert event.prep_brief is not None
    assert "Negotiating the renewal." in event.prep_brief
    assert "Hold firm on price" in event.prep_brief
    assert event.prep_generated_at is not None


async def test_draft_follow_up_creates_draft_and_approval(
    db_session, make_user, fake_ctx, mock_claude
):
    user = await make_user()
    account = await _make_account(db_session, user)
    event = CalendarEvent(
        account_id=account.id,
        provider_event_id="evt-3",
        title="Kickoff",
        start_time=datetime.now(timezone.utc) - timedelta(days=1),
        attendees=["partner@example.com", "director@example.com"],
    )
    db_session.add(event)
    await db_session.commit()

    mock_claude.return_value = FollowUpEmailDraft(
        subject="Kickoff follow-up", body="Thanks all — next steps below."
    )

    await jobs.draft_event_follow_up(fake_ctx, str(event.id))

    drafts = (await db_session.execute(select(EmailDraft))).scalars().all()
    assert len(drafts) == 1
    # The organizer's own address is excluded from recipients.
    assert drafts[0].to_addresses == ["partner@example.com"]
    assert drafts[0].account_id == account.id

    approvals = (await db_session.execute(select(ApprovalQueueItem))).scalars().all()
    assert len(approvals) == 1
    assert approvals[0].item_type == ApprovalItemType.email_draft
