"""Tests for M7 workspace search and the chat assistant (Claude mocked)."""

from datetime import date

from app.models.approval import ApprovalItemType, ApprovalQueueItem
from app.models.meeting import Meeting
from app.services.ai.schemas import ChatAnswer, ChatSource


async def _make_meeting(db_session, user, title: str, summary: str) -> Meeting:
    meeting = Meeting(
        created_by_id=user.id,
        title=title,
        meeting_date=date.today(),
        source_text="notes",
        summary=summary,
    )
    db_session.add(meeting)
    await db_session.commit()
    return meeting


async def test_search_finds_meeting_by_title_and_summary(client, auth_user, db_session):
    user, headers = auth_user
    await _make_meeting(db_session, user, "Vendor negotiation", "Discussed pricing for renewal")

    resp = await client.get("/api/v1/search", params={"q": "vendor"}, headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert any(r["type"] == "meeting" and "Vendor" in r["title"] for r in body)

    # Matches on summary text too.
    resp2 = await client.get("/api/v1/search", params={"q": "renewal"}, headers=headers)
    assert any(r["type"] == "meeting" for r in resp2.json())


async def test_search_empty_query_returns_empty(client, auth_user):
    _, headers = auth_user
    resp = await client.get("/api/v1/search", params={"q": "   "}, headers=headers)
    assert resp.status_code == 200
    assert resp.json() == []


async def test_chat_answers_with_sources(client, auth_user, db_session, mock_claude):
    user, headers = auth_user
    db_session.add(
        ApprovalQueueItem(
            item_type=ApprovalItemType.email_draft,
            reference_id=user.id,
            preview_text="Reply to the vendor about pricing",
            requested_by_id=user.id,
        )
    )
    await db_session.commit()

    mock_claude.return_value = ChatAnswer(
        answer="You have 1 item awaiting approval: a reply to the vendor.",
        sources=[ChatSource(label="Reply to the vendor about pricing", link="/approvals")],
    )

    resp = await client.post(
        "/api/v1/search/chat",
        headers=headers,
        json={"question": "What needs my approval today?"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "approval" in body["answer"].lower()
    assert body["sources"][0]["link"] == "/approvals"

    # The assistant was given the pending approval in its context.
    prompt = mock_claude.await_args.kwargs["user"]
    assert "Reply to the vendor about pricing" in prompt
