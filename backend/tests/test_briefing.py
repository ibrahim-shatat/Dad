"""Tests for the executive daily briefing: live assembly of what needs attention, the
Claude-written summary (mocked), and persistent 'handled' state per item."""

from datetime import date, timedelta

from app.models.approval import ApprovalItemType, ApprovalQueueItem
from app.models.meeting import ActionItem, ActionItemStatus, Meeting
from app.services.ai.schemas import ExecutiveBriefing


async def _make_meeting_with_due_action(db_session, user, due: date) -> ActionItem:
    meeting = Meeting(
        created_by_id=user.id,
        title="Q3 planning",
        meeting_date=date.today(),
        source_text="notes",
    )
    db_session.add(meeting)
    await db_session.flush()
    action = ActionItem(
        meeting_id=meeting.id,
        description="Send the budget to finance",
        owner="Alex",
        due_date=due,
        status=ActionItemStatus.open,
    )
    db_session.add(action)
    await db_session.commit()
    return action


async def test_today_briefing_assembles_live_items(client, auth_user, db_session):
    user, headers = auth_user
    await _make_meeting_with_due_action(db_session, user, date.today())
    db_session.add(
        ApprovalQueueItem(
            item_type=ApprovalItemType.email_draft,
            reference_id=user.id,
            preview_text="Reply to the vendor",
            requested_by_id=user.id,
        )
    )
    await db_session.commit()

    resp = await client.get("/api/v1/briefing/today", headers=headers)
    assert resp.status_code == 200
    body = resp.json()

    assert body["summary"] is None  # not generated yet
    # meeting today + its due action item + the pending approval
    assert body["total_items"] == 3
    populated = {s["id"] for s in body["sections"] if s["items"]}
    assert {"meetings_today", "action_items", "pending_approvals"} <= populated


async def test_generate_briefing_uses_claude_summary(client, auth_user, db_session, mock_claude):
    user, headers = auth_user
    await _make_meeting_with_due_action(db_session, user, date.today() - timedelta(days=1))
    mock_claude.return_value = ExecutiveBriefing(
        summary="One action item is overdue — send the budget to finance first.",
        top_priorities=["Send the budget to finance"],
    )

    resp = await client.post("/api/v1/briefing/generate", headers=headers)
    assert resp.status_code == 200
    body = resp.json()

    assert "overdue" in body["summary"]
    assert body["top_priorities"] == ["Send the budget to finance"]
    assert body["generated_at"] is not None
    mock_claude.assert_awaited_once()


async def test_toggle_item_persists_handled_state(client, auth_user, db_session):
    user, headers = auth_user
    action = await _make_meeting_with_due_action(db_session, user, date.today())
    key = f"action_item:{action.id}"

    resp = await client.post(
        "/api/v1/briefing/items/toggle", headers=headers, json={"key": key, "handled": True}
    )
    assert resp.status_code == 200
    assert resp.json()["handled_items"] == 1

    # Persisted across a fresh read.
    again = await client.get("/api/v1/briefing/today", headers=headers)
    handled_item = next(
        i
        for s in again.json()["sections"]
        for i in s["items"]
        if i["key"] == key
    )
    assert handled_item["handled"] is True

    # And can be turned back off.
    off = await client.post(
        "/api/v1/briefing/items/toggle", headers=headers, json={"key": key, "handled": False}
    )
    assert off.json()["handled_items"] == 0
