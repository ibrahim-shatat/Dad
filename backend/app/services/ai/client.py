from typing import TypeVar

from anthropic import AsyncAnthropic
from anthropic.types import Message
from pydantic import BaseModel, ValidationError

from app.core.config import settings

T = TypeVar("T", bound=BaseModel)

_TOOL_NAME = "extract"


def _extract_and_validate(
    response: Message, output_model: type[T]
) -> tuple[T | None, str | None, str | None]:
    """Returns (parsed, error, tool_use_id). tool_use_id is set whenever a tool_use block was
    found (even if validation failed) since the caller needs it to send a tool_result back."""
    for block in response.content:
        if block.type == "tool_use" and block.name == _TOOL_NAME:
            try:
                return output_model.model_validate(block.input), None, block.id
            except ValidationError as exc:
                return None, str(exc), block.id
    return None, "No tool_use block found in Claude's response.", None


class ClaudeClient:
    """Single wrapper around the Anthropic SDK for all Claude calls in the app."""

    def __init__(self) -> None:
        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def structured_call(
        self,
        *,
        system: str,
        user: str,
        output_model: type[T],
        model: str | None = None,
        max_tokens: int = 4096,
    ) -> T:
        """Call Claude and force a tool call whose input validates against `output_model`.

        Retries once, feeding the validation error back to the model, before giving up.
        """
        model_name = model or settings.claude_model_smart
        tool = {
            "name": _TOOL_NAME,
            "description": f"Extract structured output matching the {output_model.__name__} schema.",
            "input_schema": output_model.model_json_schema(),
        }
        tool_choice = {"type": "tool", "name": _TOOL_NAME}
        messages: list[dict] = [{"role": "user", "content": user}]

        response = await self._client.messages.create(
            model=model_name,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
            tools=[tool],
            tool_choice=tool_choice,
        )
        parsed, error, tool_use_id = _extract_and_validate(response, output_model)
        if parsed is not None:
            return parsed

        messages.append({"role": "assistant", "content": response.content})
        retry_note = (
            f"Your previous response did not match the required schema: {error}. "
            "Call the tool again with corrected arguments."
        )
        if tool_use_id is not None:
            # A dangling tool_use block must be followed by a tool_result in the very next
            # message, or the API rejects the request — a plain text reply isn't valid here.
            messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": retry_note,
                            "is_error": True,
                        }
                    ],
                }
            )
        else:
            messages.append({"role": "user", "content": retry_note})

        retry_response = await self._client.messages.create(
            model=model_name,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
            tools=[tool],
            tool_choice=tool_choice,
        )
        parsed, error, _ = _extract_and_validate(retry_response, output_model)
        if parsed is None:
            raise ValueError(
                f"Claude did not return a valid {output_model.__name__} after one retry: {error}"
            )
        return parsed


claude_client = ClaudeClient()
