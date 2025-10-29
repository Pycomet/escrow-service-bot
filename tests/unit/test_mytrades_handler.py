"""
Unit tests for the /mytrades command handler.

Tests cover:
- /mytrades command with no active trades
- /mytrades command with one active trade
- /mytrades command with multiple active trades
- Callback handlers for mytrades views
- Trade age formatting
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class DummyUser:
    """Mock user object for testing"""

    id = 111
    first_name = "Alice"


class DummyChat:
    """Mock chat object for testing"""

    id = 111


class DummyMessage:
    """Mock message object for testing"""

    from_user = DummyUser()
    chat = DummyChat()

    async def reply_text(self, text, **kwargs):
        """Mock reply_text method"""
        return MagicMock(text=text)


class DummyUpdate:
    """Mock update object for testing"""

    effective_user = DummyUser()
    message = DummyMessage()

    callback_query = None


class DummyContext:
    """Mock context object for testing"""

    user_data = {}


def test_format_trade_age():
    """Test trade age formatting helper function"""
    from handlers.mytrades import format_trade_age

    now = datetime.now()

    # Just now
    assert format_trade_age(now) == "just now"

    # Minutes ago
    minutes_ago = now - timedelta(minutes=30)
    assert format_trade_age(minutes_ago) == "30m ago"

    # Hours ago
    hours_ago = now - timedelta(hours=5)
    assert format_trade_age(hours_ago) == "5h ago"

    # Days ago
    days_ago = now - timedelta(days=3)
    assert format_trade_age(days_ago) == "3d ago"


@pytest.mark.asyncio
@patch("handlers.mytrades.TradeClient")
async def test_mytrades_no_active_trades(mock_trade_client):
    """Test /mytrades command when user has no active trades"""
    from handlers.mytrades import mytrades_handler

    # Mock TradeClient to return empty list
    mock_trade_client.get_active_trades_for_user.return_value = []

    update = DummyUpdate()
    context = DummyContext()

    # Call handler
    await mytrades_handler(update, context)

    # Verify TradeClient was called correctly
    mock_trade_client.get_active_trades_for_user.assert_called_once_with("111")


@pytest.mark.asyncio
@patch("handlers.mytrades.TradeClient")
async def test_mytrades_single_active_trade(mock_trade_client):
    """Test /mytrades command with one active trade"""
    from handlers.mytrades import mytrades_handler

    # Create mock trade
    mock_trade = {
        "_id": "trade123456789",
        "seller_id": "111",
        "buyer_id": "",
        "price": 100.0,
        "currency": "USDT",
        "status": "active",
        "created_at": datetime.now() - timedelta(hours=2),
        "is_active": True,
    }

    # Mock TradeClient to return one trade
    mock_trade_client.get_active_trades_for_user.return_value = [mock_trade]

    update = DummyUpdate()
    context = DummyContext()

    # Call handler
    await mytrades_handler(update, context)

    # Verify TradeClient was called
    mock_trade_client.get_active_trades_for_user.assert_called_once_with("111")


@pytest.mark.asyncio
@patch("handlers.mytrades.TradeClient")
async def test_mytrades_multiple_active_trades(mock_trade_client):
    """Test /mytrades command with multiple active trades"""
    from handlers.mytrades import mytrades_handler

    # Create mock trades
    now = datetime.now()
    mock_trades = [
        {
            "_id": f"trade{i}",
            "seller_id": "111" if i % 2 == 0 else "222",
            "buyer_id": "222" if i % 2 == 0 else "111",
            "price": 100.0 * i,
            "currency": "USDT",
            "status": "active",
            "created_at": now - timedelta(hours=i),
            "is_active": True,
        }
        for i in range(1, 4)
    ]

    # Mock TradeClient to return multiple trades
    mock_trade_client.get_active_trades_for_user.return_value = mock_trades

    update = DummyUpdate()
    context = DummyContext()

    # Call handler
    await mytrades_handler(update, context)

    # Verify TradeClient was called
    mock_trade_client.get_active_trades_for_user.assert_called_once_with("111")


@pytest.mark.asyncio
@patch("handlers.mytrades.TradeClient")
async def test_mytrades_callback_handler_view_trades(mock_trade_client):
    """Test mytrades callback handler for viewing all trades"""
    from handlers.mytrades import mytrades_callback_handler

    # Create mock trade
    mock_trade = {
        "_id": "trade123",
        "seller_id": "111",
        "buyer_id": "",
        "price": 100.0,
        "currency": "USDT",
        "status": "active",
        "created_at": datetime.now(),
        "is_active": True,
    }

    # Mock TradeClient
    mock_trade_client.get_active_trades_for_user.return_value = [mock_trade]

    # Create mock callback query
    mock_query = AsyncMock()
    mock_query.data = "my_trades"
    mock_query.answer = AsyncMock()
    mock_query.edit_message_text = AsyncMock()

    # Create update with callback query
    update = DummyUpdate()
    update.callback_query = mock_query
    update.effective_user = DummyUser()

    context = DummyContext()

    # Call callback handler
    await mytrades_callback_handler(update, context)

    # Verify query was answered
    mock_query.answer.assert_called_once()


@pytest.mark.asyncio
@patch("handlers.mytrades.Messages")
@patch("handlers.mytrades.TradeClient")
async def test_mytrades_callback_handler_view_specific_trade(
    mock_trade_client, mock_messages
):
    """Test mytrades callback handler for viewing a specific trade"""
    from handlers.mytrades import mytrades_callback_handler

    # Create mock trade
    mock_trade = {
        "_id": "trade123",
        "seller_id": "111",
        "buyer_id": "222",
        "price": 100.0,
        "currency": "USDT",
        "status": "active",
        "created_at": datetime.now(),
        "is_active": True,
    }

    # Mock TradeClient
    mock_trade_client.get_trade.return_value = mock_trade

    # Mock Messages
    mock_messages.trade_details.return_value = "Trade details message"

    # Create mock callback query
    mock_query = AsyncMock()
    mock_query.data = "mytrade_view_trade123"
    mock_query.answer = AsyncMock()
    mock_query.edit_message_text = AsyncMock()

    # Create update with callback query
    update = DummyUpdate()
    update.callback_query = mock_query
    update.effective_user = DummyUser()

    context = DummyContext()

    # Call callback handler
    await mytrades_callback_handler(update, context)

    # Verify query was answered and trade was fetched
    mock_query.answer.assert_called_once()
    mock_trade_client.get_trade.assert_called_once_with("trade123")


@pytest.mark.asyncio
@patch("handlers.mytrades.Messages")
@patch("handlers.mytrades.TradeClient")
async def test_mytrades_callback_handler_trade_not_found(
    mock_trade_client, mock_messages
):
    """Test mytrades callback handler when trade is not found"""
    from handlers.mytrades import mytrades_callback_handler

    # Mock TradeClient to return None (trade not found)
    mock_trade_client.get_trade.return_value = None

    # Mock Messages
    mock_messages.trade_not_found.return_value = "Trade not found message"

    # Create mock callback query
    mock_query = AsyncMock()
    mock_query.data = "mytrade_view_nonexistent"
    mock_query.answer = AsyncMock()
    mock_query.edit_message_text = AsyncMock()

    # Create update with callback query
    update = DummyUpdate()
    update.callback_query = mock_query
    update.effective_user = DummyUser()

    context = DummyContext()

    # Call callback handler
    await mytrades_callback_handler(update, context)

    # Verify appropriate message was shown
    mock_query.answer.assert_called_once()
    mock_messages.trade_not_found.assert_called_once()


@pytest.mark.asyncio
@patch("handlers.mytrades.Messages")
@patch("handlers.mytrades.TradeClient")
async def test_mytrades_callback_handler_access_denied(
    mock_trade_client, mock_messages
):
    """Test mytrades callback handler when user doesn't have access to trade"""
    from handlers.mytrades import mytrades_callback_handler

    # Create mock trade owned by different users
    mock_trade = {
        "_id": "trade123",
        "seller_id": "999",  # Different user
        "buyer_id": "888",  # Different user
        "price": 100.0,
        "currency": "USDT",
        "status": "active",
        "created_at": datetime.now(),
        "is_active": True,
    }

    # Mock TradeClient
    mock_trade_client.get_trade.return_value = mock_trade

    # Mock Messages
    mock_messages.access_denied.return_value = "Access denied message"

    # Create mock callback query
    mock_query = AsyncMock()
    mock_query.data = "mytrade_view_trade123"
    mock_query.answer = AsyncMock()
    mock_query.edit_message_text = AsyncMock()

    # Create update with callback query (user ID 111)
    update = DummyUpdate()
    update.callback_query = mock_query
    update.effective_user = DummyUser()

    context = DummyContext()

    # Call callback handler
    await mytrades_callback_handler(update, context)

    # Verify access denied message was shown
    mock_query.answer.assert_called_once()
    mock_messages.access_denied.assert_called_once()
