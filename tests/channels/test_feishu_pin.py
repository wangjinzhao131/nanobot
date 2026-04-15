"""Tests for Feishu pin/unpin message operations."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from nanobot.bus.queue import MessageBus
from nanobot.channels.feishu import FeishuChannel, FeishuConfig


def _make_channel() -> FeishuChannel:
    config = FeishuConfig(
        enabled=True,
        app_id="cli_test",
        app_secret="secret",
        allow_from=["*"],
    )
    ch = FeishuChannel(config, MessageBus())
    ch._client = MagicMock()
    ch._loop = None
    return ch


def _mock_pin_response(success: bool = True):
    resp = MagicMock()
    resp.success.return_value = success
    resp.code = 0 if success else 99999
    resp.msg = "ok" if success else "error"
    resp.data = SimpleNamespace() if success else None
    return resp


# ── _pin_message_sync ────────────────────────────────────────────────────────


class TestPinMessageSync:
    def test_returns_true_on_success(self):
        ch = _make_channel()
        ch._client.im.v1.pin.create.return_value = _mock_pin_response(success=True)
        result = ch._pin_message_sync("om_001")
        assert result is True

    def test_returns_false_when_response_fails(self):
        ch = _make_channel()
        ch._client.im.v1.pin.create.return_value = _mock_pin_response(success=False)
        result = ch._pin_message_sync("om_001")
        assert result is False

    def test_returns_false_on_exception(self):
        ch = _make_channel()
        ch._client.im.v1.pin.create.side_effect = RuntimeError("network error")
        result = ch._pin_message_sync("om_001")
        assert result is False

    def test_calls_correct_api_endpoint(self):
        ch = _make_channel()
        ch._client.im.v1.pin.create.return_value = _mock_pin_response(success=True)
        ch._pin_message_sync("om_001")
        ch._client.im.v1.pin.create.assert_called_once()


# ── _pin_message (async) ─────────────────────────────────────────────────────


class TestPinMessageAsync:
    @pytest.mark.asyncio
    async def test_returns_true_on_success(self):
        ch = _make_channel()
        ch._pin_message_sync = MagicMock(return_value=True)
        result = await ch._pin_message("om_001")
        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_when_sync_returns_false(self):
        ch = _make_channel()
        ch._pin_message_sync = MagicMock(return_value=False)
        result = await ch._pin_message("om_001")
        assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_when_no_client(self):
        ch = _make_channel()
        ch._client = None
        result = await ch._pin_message("om_001")
        assert result is False

    @pytest.mark.asyncio
    async def test_calls_sync_helper(self):
        ch = _make_channel()
        ch._pin_message_sync = MagicMock(return_value=True)
        await ch._pin_message("om_001")
        ch._pin_message_sync.assert_called_once_with("om_001")


# ── _unpin_message_sync ─────────────────────────────────────────────────────


class TestUnpinMessageSync:
    def test_returns_true_on_success(self):
        ch = _make_channel()
        ch._client.im.v1.pin.delete.return_value = _mock_pin_response(success=True)
        result = ch._unpin_message_sync("om_001")
        assert result is True

    def test_returns_false_when_response_fails(self):
        ch = _make_channel()
        ch._client.im.v1.pin.delete.return_value = _mock_pin_response(success=False)
        result = ch._unpin_message_sync("om_001")
        assert result is False

    def test_returns_false_on_exception(self):
        ch = _make_channel()
        ch._client.im.v1.pin.delete.side_effect = RuntimeError("network error")
        result = ch._unpin_message_sync("om_001")
        assert result is False

    def test_calls_correct_api_endpoint(self):
        ch = _make_channel()
        ch._client.im.v1.pin.delete.return_value = _mock_pin_response(success=True)
        ch._unpin_message_sync("om_001")
        ch._client.im.v1.pin.delete.assert_called_once()


# ── _unpin_message (async) ───────────────────────────────────────────────────


class TestUnpinMessageAsync:
    @pytest.mark.asyncio
    async def test_returns_true_on_success(self):
        ch = _make_channel()
        ch._unpin_message_sync = MagicMock(return_value=True)
        result = await ch._unpin_message("om_001")
        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_when_sync_returns_false(self):
        ch = _make_channel()
        ch._unpin_message_sync = MagicMock(return_value=False)
        result = await ch._unpin_message("om_001")
        assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_when_no_client(self):
        ch = _make_channel()
        ch._client = None
        result = await ch._unpin_message("om_001")
        assert result is False

    @pytest.mark.asyncio
    async def test_calls_sync_helper(self):
        ch = _make_channel()
        ch._unpin_message_sync = MagicMock(return_value=True)
        await ch._unpin_message("om_001")
        ch._unpin_message_sync.assert_called_once_with("om_001")


# ── PinTool tests ────────────────────────────────────────────────────────────


from nanobot.agent.tools.pin import PinTool


class TestPinTool:
    @pytest.mark.asyncio
    async def test_pin_action_success(self):
        pin_callback = AsyncMock(return_value=True)
        tool = PinTool(
            pin_callback=pin_callback, default_channel="feishu", default_chat_id="oc_123"
        )
        tool.set_context("feishu", "oc_123")

        result = await tool.execute(message_id="om_001", action="pin")

        pin_callback.assert_called_once_with("om_001", "pin", "feishu", "oc_123")
        assert "pinned successfully" in result

    @pytest.mark.asyncio
    async def test_unpin_action_success(self):
        pin_callback = AsyncMock(return_value=True)
        tool = PinTool(
            pin_callback=pin_callback, default_channel="feishu", default_chat_id="oc_123"
        )
        tool.set_context("feishu", "oc_123")

        result = await tool.execute(message_id="om_001", action="unpin")

        pin_callback.assert_called_once_with("om_001", "unpin", "feishu", "oc_123")
        assert "unpinned successfully" in result

    @pytest.mark.asyncio
    async def test_rejects_non_feishu_channel(self):
        pin_callback = AsyncMock(return_value=True)
        tool = PinTool(pin_callback=pin_callback, default_channel="slack", default_chat_id="ch_123")
        tool.set_context("slack", "ch_123")

        result = await tool.execute(message_id="om_001", action="pin")

        pin_callback.assert_not_called()
        assert "only supported for Feishu" in result

    @pytest.mark.asyncio
    async def test_rejects_invalid_action(self):
        pin_callback = AsyncMock(return_value=True)
        tool = PinTool(
            pin_callback=pin_callback, default_channel="feishu", default_chat_id="oc_123"
        )
        tool.set_context("feishu", "oc_123")

        result = await tool.execute(message_id="om_001", action="delete")

        pin_callback.assert_not_called()
        assert "Invalid action" in result

    @pytest.mark.asyncio
    async def test_returns_error_when_callback_not_configured(self):
        tool = PinTool(pin_callback=None, default_channel="feishu", default_chat_id="oc_123")
        tool.set_context("feishu", "oc_123")

        result = await tool.execute(message_id="om_001", action="pin")

        assert "not configured" in result

    @pytest.mark.asyncio
    async def test_pin_callback_failure(self):
        pin_callback = AsyncMock(return_value=False)
        tool = PinTool(
            pin_callback=pin_callback, default_channel="feishu", default_chat_id="oc_123"
        )
        tool.set_context("feishu", "oc_123")

        result = await tool.execute(message_id="om_001", action="pin")

        assert "Failed to pin" in result

    @pytest.mark.asyncio
    async def test_uses_explicit_channel_over_default(self):
        pin_callback = AsyncMock(return_value=True)
        tool = PinTool(
            pin_callback=pin_callback, default_channel="feishu", default_chat_id="oc_123"
        )
        tool.set_context("feishu", "oc_123")

        await tool.execute(message_id="om_001", action="pin", channel="feishu", chat_id="oc_456")

        pin_callback.assert_called_once_with("om_001", "pin", "feishu", "oc_456")

    def test_name_property(self):
        tool = PinTool(pin_callback=None)
        assert tool.name == "pin"

    def test_description_property(self):
        tool = PinTool(pin_callback=None)
        assert "pin" in tool.description.lower()
        assert "unpin" in tool.description.lower()
        assert "Feishu" in tool.description


# ── ChannelManager pin routing tests ────────────────────────────────────────


from nanobot.bus.events import OutboundMessage
from nanobot.channels.manager import ChannelManager


class TestChannelManagerPinRouting:
    @pytest.mark.asyncio
    async def test_send_once_pins_message(self):
        ch = _make_channel()
        ch._pin_message = AsyncMock(return_value=True)

        msg = OutboundMessage(
            channel="feishu",
            chat_id="oc_123",
            content="",
            metadata={
                "_pin": True,
                "pin_message_id": "om_001",
                "pin_action": "pin",
            },
        )

        await ChannelManager._send_once(ch, msg)

        ch._pin_message.assert_called_once_with("om_001")

    @pytest.mark.asyncio
    async def test_send_once_unpins_message(self):
        ch = _make_channel()
        ch._unpin_message = AsyncMock(return_value=True)

        msg = OutboundMessage(
            channel="feishu",
            chat_id="oc_123",
            content="",
            metadata={
                "_pin": True,
                "pin_message_id": "om_001",
                "pin_action": "unpin",
            },
        )

        await ChannelManager._send_once(ch, msg)

        ch._unpin_message.assert_called_once_with("om_001")

    @pytest.mark.asyncio
    async def test_send_once_logs_warning_on_missing_message_id(self):
        ch = _make_channel()
        ch._pin_message = AsyncMock()
        ch._unpin_message = AsyncMock()

        msg = OutboundMessage(
            channel="feishu",
            chat_id="oc_123",
            content="",
            metadata={
                "_pin": True,
                "pin_action": "pin",
            },
        )

        await ChannelManager._send_once(ch, msg)

        ch._pin_message.assert_not_called()
        ch._unpin_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_once_logs_warning_on_unknown_action(self):
        ch = _make_channel()
        ch._pin_message = AsyncMock()
        ch._unpin_message = AsyncMock()

        msg = OutboundMessage(
            channel="feishu",
            chat_id="oc_123",
            content="",
            metadata={
                "_pin": True,
                "pin_message_id": "om_001",
                "pin_action": "delete",
            },
        )

        await ChannelManager._send_once(ch, msg)

        ch._pin_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_once_logs_warning_on_failure(self):
        ch = _make_channel()
        ch._pin_message = AsyncMock(return_value=False)

        msg = OutboundMessage(
            channel="feishu",
            chat_id="oc_123",
            content="",
            metadata={
                "_pin": True,
                "pin_message_id": "om_001",
                "pin_action": "pin",
            },
        )

        await ChannelManager._send_once(ch, msg)

        ch._pin_message.assert_called_once_with("om_001")
