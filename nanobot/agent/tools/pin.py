"""Pin tool for pinning/unpinning messages in supported channels."""

from typing import Any, Awaitable, Callable

from nanobot.agent.tools.base import Tool, tool_parameters
from nanobot.agent.tools.schema import StringSchema, tool_parameters_schema


@tool_parameters(
    tool_parameters_schema(
        message_id=StringSchema("The message ID to pin or unpin"),
        action=StringSchema(
            "Action to perform",
            enum=("pin", "unpin"),
        ),
        channel=StringSchema("Optional: target channel (default: current channel)"),
        chat_id=StringSchema("Optional: target chat ID (default: current chat)"),
        required=["message_id", "action"],
    )
)
class PinTool(Tool):
    """Tool to pin or unpin messages in supported channels (Feishu only)."""

    def __init__(
        self,
        pin_callback: Callable[[str, str, str, str], Awaitable[bool]] | None = None,
        default_channel: str = "",
        default_chat_id: str = "",
    ):
        self._pin_callback = pin_callback
        self._default_channel = default_channel
        self._default_chat_id = default_chat_id

    def set_context(self, channel: str, chat_id: str) -> None:
        self._default_channel = channel
        self._default_chat_id = chat_id

    def set_pin_callback(self, callback: Callable[[str, str, str, str], Awaitable[bool]]) -> None:
        self._pin_callback = callback

    @property
    def name(self) -> str:
        return "pin"

    @property
    def description(self) -> str:
        return (
            "Pin or unpin a message in the chat. "
            "Pinned messages appear at the top of the chat for all members. "
            "Use action='pin' to pin a message, action='unpin' to unpin it. "
            "Currently only supported for Feishu channel."
        )

    async def execute(
        self,
        message_id: str,
        action: str,
        channel: str | None = None,
        chat_id: str | None = None,
        **kwargs: Any,
    ) -> str:
        channel = channel or self._default_channel
        chat_id = chat_id or self._default_chat_id

        if not channel:
            return "Error: No target channel specified"

        if channel != "feishu":
            return f"Error: Pin is only supported for Feishu channel, got {channel}"

        if action not in ("pin", "unpin"):
            return f"Error: Invalid action '{action}', must be 'pin' or 'unpin'"

        if not self._pin_callback:
            return "Error: Pin callback not configured"

        try:
            success = await self._pin_callback(message_id, action, channel, chat_id)
            if success:
                return f"Message {message_id} {action}ned successfully in {channel}:{chat_id}"
            return f"Failed to {action} message {message_id}"
        except Exception as e:
            return f"Error {action}ning message: {str(e)}"
