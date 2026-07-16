"""Tests for ClaudeClient.structured_call's retry logic — this is bespoke, every feature
depends on it, and it has already needed one real bugfix (the tool_result-vs-plain-text retry
message shape). Mocks the Anthropic SDK client directly; never hits the real API.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from pydantic import BaseModel

from app.services.ai.client import ClaudeClient


class Widget(BaseModel):
    name: str
    count: int


def _tool_use_block(tool_input: dict, block_id: str = "tool_1", name: str = "extract"):
    return SimpleNamespace(type="tool_use", name=name, id=block_id, input=tool_input)


def _text_block(text: str = "hello"):
    return SimpleNamespace(type="text", text=text)


def _response(blocks: list):
    return SimpleNamespace(content=blocks)


@pytest.fixture
def client() -> ClaudeClient:
    c = ClaudeClient()
    c._client = AsyncMock()
    return c


async def test_first_call_success_returns_without_retry(client: ClaudeClient):
    client._client.messages.create.return_value = _response(
        [_tool_use_block({"name": "a", "count": 1})]
    )

    result = await client.structured_call(system="sys", user="usr", output_model=Widget)

    assert result == Widget(name="a", count=1)
    assert client._client.messages.create.call_count == 1


async def test_validation_failure_retries_with_tool_result_error(client: ClaudeClient):
    bad = _response([_tool_use_block({"name": "a"}, block_id="tool_abc")])  # missing "count"
    good = _response([_tool_use_block({"name": "a", "count": 2})])
    client._client.messages.create.side_effect = [bad, good]

    result = await client.structured_call(system="sys", user="usr", output_model=Widget)

    assert result == Widget(name="a", count=2)
    assert client._client.messages.create.call_count == 2
    retry_messages = client._client.messages.create.call_args_list[1].kwargs["messages"]
    last = retry_messages[-1]
    assert last["role"] == "user"
    assert isinstance(last["content"], list)
    assert last["content"][0]["type"] == "tool_result"
    assert last["content"][0]["tool_use_id"] == "tool_abc"
    assert last["content"][0]["is_error"] is True


async def test_no_tool_use_block_retries_with_plain_text_not_tool_result(client: ClaudeClient):
    no_tool = _response([_text_block("I'd rather not")])
    good = _response([_tool_use_block({"name": "a", "count": 3})])
    client._client.messages.create.side_effect = [no_tool, good]

    result = await client.structured_call(system="sys", user="usr", output_model=Widget)

    assert result == Widget(name="a", count=3)
    retry_messages = client._client.messages.create.call_args_list[1].kwargs["messages"]
    last = retry_messages[-1]
    assert last["role"] == "user"
    # No tool_use_id was available, so this must NOT be a tool_result block (the API rejects
    # a tool_result with no matching dangling tool_use) — plain string content instead.
    assert isinstance(last["content"], str)


async def test_second_failure_raises_with_model_name_and_error(client: ClaudeClient):
    bad1 = _response([_tool_use_block({"name": "a"}, block_id="t1")])
    bad2 = _response([_tool_use_block({"name": "b"}, block_id="t2")])
    client._client.messages.create.side_effect = [bad1, bad2]

    with pytest.raises(ValueError, match="Widget"):
        await client.structured_call(system="sys", user="usr", output_model=Widget)
