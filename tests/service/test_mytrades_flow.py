"""
Service tests for the complete /mytrades flow.

Tests cover end-to-end user interactions with the mytrades feature:
- Viewing trades list
- Viewing trade details
- Navigation between views
- Integration with trade management
"""

import os
import sys
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from telegram import CallbackQuery, Chat, Message, Update, User
from telegram.ext import ContextTypes


# Test fixtures
@pytest.fixture
def mock_user_update():
    """Create a mock Update object for a user"""
    update = AsyncMock(spec=Update)
    update.effective_user = AsyncMock(spec=User)
    update.effective_user.id = 12345
    update.effective_user.username = "testuser"
    update.message = AsyncMock(spec=Message)
    update.message.from_user = update.effective_user
    update.message.chat = AsyncMock(spec=Chat)
    update.message.chat.id = 12345
    update.message.reply_text = AsyncMock()
    update.callback_query = None
    return update


@pytest.fixture
def mock_callback_update():
    """Create a mock Update object for callback queries"""
    update = AsyncMock(spec=Update)
    update.effective_user = AsyncMock(spec=User)
    update.effective_user.id = 12345
    update.effective_user.username = "testuser"
    update.message = AsyncMock(spec=Message)
    update.message.from_user = update.effective_user
    update.callback_query = AsyncMock(spec=CallbackQuery)
    update.callback_query.from_user = update.effective_user
    update.callback_query.message = update.message
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    update.callback_query.data = ""
    return update


@pytest.fixture
def mock_context():
    """Create a mock context"""
    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {}
    context.bot = AsyncMock()
    return context


class TestMyTradesServiceFlow:
    """Test the complete mytrades service flow"""

    @pytest.mark.asyncio
    async def test_mytrades_command_no_trades(self, mock_user_update, mock_context):
        """Test /mytrades command when user has no active trades"""
        from handlers.mytrades import mytrades_handler

        with patch(
            "handlers.mytrades.TradeClient.get_active_trades_for_user"
        ) as mock_get_trades:
            # Mock no active trades
            mock_get_trades.return_value = []

            # Execute handler
            await mytrades_handler(mock_user_update, mock_context)

            # Verify TradeClient was called with correct user_id
            mock_get_trades.assert_called_once_with("12345")

            # Verify message was sent to user
            mock_user_update.message.reply_text.assert_called_once()
            call_args = mock_user_update.message.reply_text.call_args
            message_text = call_args.args[0]

            # Verify message contains expected content
            assert "No Active Trades" in message_text

    @pytest.mark.asyncio
    async def test_mytrades_command_with_single_trade(
        self, mock_user_update, mock_context
    ):
        """Test /mytrades command with one active trade"""
        from handlers.mytrades import mytrades_handler

        # Create a mock trade
        mock_trade = {
            "_id": "trade123456789",
            "seller_id": "12345",
            "buyer_id": "67890",
            "price": 100.0,
            "currency": "USDT",
            "status": "active",
            "created_at": datetime.now() - timedelta(hours=5),
            "is_active": True,
        }

        with patch(
            "handlers.mytrades.TradeClient.get_active_trades_for_user"
        ) as mock_get_trades:
            # Mock one active trade
            mock_get_trades.return_value = [mock_trade]

            # Execute handler
            await mytrades_handler(mock_user_update, mock_context)

            # Verify message was sent
            mock_user_update.message.reply_text.assert_called_once()
            call_args = mock_user_update.message.reply_text.call_args
            message_text = call_args.args[0]

            # Verify message contains trade info
            assert "Your Active Trades" in message_text
            assert "1" in message_text  # Trade count
            assert "USDT" in message_text

    @pytest.mark.asyncio
    async def test_mytrades_callback_view_all_trades(
        self, mock_callback_update, mock_context
    ):
        """Test callback handler for viewing all trades"""
        from handlers.mytrades import mytrades_callback_handler

        # Set callback data
        mock_callback_update.callback_query.data = "my_trades"

        # Create mock trades
        mock_trades = [
            {
                "_id": f"trade{i}",
                "seller_id": "12345" if i % 2 == 0 else "67890",
                "buyer_id": "67890" if i % 2 == 0 else "12345",
                "price": 100.0 * i,
                "currency": "USDT",
                "status": "active",
                "created_at": datetime.now() - timedelta(hours=i),
                "is_active": True,
            }
            for i in range(1, 3)
        ]

        with patch(
            "handlers.mytrades.TradeClient.get_active_trades_for_user"
        ) as mock_get_trades:
            mock_get_trades.return_value = mock_trades

            # Execute callback handler
            await mytrades_callback_handler(mock_callback_update, mock_context)

            # Verify query was answered
            mock_callback_update.callback_query.answer.assert_called_once()

            # Verify message was edited
            mock_callback_update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_mytrades_callback_view_specific_trade(
        self, mock_callback_update, mock_context
    ):
        """Test viewing a specific trade detail"""
        from handlers.mytrades import mytrades_callback_handler

        # Set callback data to view specific trade
        mock_callback_update.callback_query.data = "mytrade_view_trade123"

        # Create mock trade
        mock_trade = {
            "_id": "trade123",
            "seller_id": "12345",
            "buyer_id": "67890",
            "price": 100.0,
            "currency": "USDT",
            "status": "active",
            "created_at": datetime.now(),
            "is_active": True,
            "trade_type": "CryptoToFiat",
        }

        with patch("handlers.mytrades.TradeClient.get_trade") as mock_get_trade, patch(
            "handlers.mytrades.Messages.trade_details"
        ) as mock_trade_details, patch(
            "utils.trade_status.get_trade_status"
        ) as mock_get_status, patch(
            "utils.trade_status.format_trade_status"
        ) as mock_format_status:

            # Mock trade retrieval
            mock_get_trade.return_value = mock_trade
            mock_trade_details.return_value = "Trade details"
            mock_get_status.return_value = ("active", "✅")
            mock_format_status.return_value = "Active"

            # Execute callback handler
            await mytrades_callback_handler(mock_callback_update, mock_context)

            # Verify trade was fetched
            mock_get_trade.assert_called_once_with("trade123")

            # Verify query was answered
            mock_callback_update.callback_query.answer.assert_called_once()

            # Verify message was edited with trade details
            mock_callback_update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_mytrades_flow_trade_not_found(
        self, mock_callback_update, mock_context
    ):
        """Test handling when trade is not found"""
        from handlers.mytrades import mytrades_callback_handler

        # Set callback data to view non-existent trade
        mock_callback_update.callback_query.data = "mytrade_view_nonexistent"

        with patch("handlers.mytrades.TradeClient.get_trade") as mock_get_trade, patch(
            "handlers.mytrades.Messages.trade_not_found"
        ) as mock_not_found:

            # Mock trade not found
            mock_get_trade.return_value = None
            mock_not_found.return_value = "Trade not found"

            # Execute callback handler
            await mytrades_callback_handler(mock_callback_update, mock_context)

            # Verify appropriate message was shown
            mock_not_found.assert_called_once()
            mock_callback_update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_mytrades_flow_access_denied(
        self, mock_callback_update, mock_context
    ):
        """Test handling when user tries to access trade they're not part of"""
        from handlers.mytrades import mytrades_callback_handler

        # Set callback data
        mock_callback_update.callback_query.data = "mytrade_view_trade999"

        # Create mock trade owned by different users
        mock_trade = {
            "_id": "trade999",
            "seller_id": "99999",  # Different user
            "buyer_id": "88888",  # Different user
            "price": 100.0,
            "currency": "USDT",
            "status": "active",
            "created_at": datetime.now(),
            "is_active": True,
        }

        with patch("handlers.mytrades.TradeClient.get_trade") as mock_get_trade, patch(
            "handlers.mytrades.Messages.access_denied"
        ) as mock_access_denied:

            # Mock trade retrieval
            mock_get_trade.return_value = mock_trade
            mock_access_denied.return_value = "Access denied"

            # Execute callback handler
            await mytrades_callback_handler(mock_callback_update, mock_context)

            # Verify access denied message was shown
            mock_access_denied.assert_called_once()
            mock_callback_update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_mytrades_multiple_trades_pagination(
        self, mock_user_update, mock_context
    ):
        """Test mytrades display with multiple trades"""
        from handlers.mytrades import mytrades_handler

        # Create 5 mock trades
        now = datetime.now()
        mock_trades = [
            {
                "_id": f"trade{i}",
                "seller_id": "12345" if i % 2 == 0 else "67890",
                "buyer_id": "67890" if i % 2 == 0 else "12345",
                "price": 100.0 * i,
                "currency": "USDT",
                "status": "active",
                "created_at": now - timedelta(hours=i),
                "is_active": True,
            }
            for i in range(1, 6)
        ]

        with patch(
            "handlers.mytrades.TradeClient.get_active_trades_for_user"
        ) as mock_get_trades:
            mock_get_trades.return_value = mock_trades

            # Execute handler
            await mytrades_handler(mock_user_update, mock_context)

            # Verify message was sent
            mock_user_update.message.reply_text.assert_called_once()
            call_args = mock_user_update.message.reply_text.call_args
            message_text = call_args.args[0]

            # Verify message contains count
            assert "5" in message_text
            assert "trade" in message_text.lower()

    @pytest.mark.asyncio
    async def test_mytrades_integration_with_status_command(
        self, mock_user_update, mock_context
    ):
        """Test that /mytrades integrates well with /status command"""
        from functions.user import UserClient
        from handlers.initiate_trade import status_handler

        # Create mock user
        mock_user = {
            "_id": "12345",
            "username": "testuser",
            "first_name": "Test",
        }

        # Create mock active trades
        mock_trades = [
            {
                "_id": "trade1",
                "seller_id": "12345",
                "buyer_id": "",
                "price": 100.0,
                "currency": "USDT",
                "status": "active",
                "created_at": datetime.now(),
                "is_active": True,
                "trade_type": "CryptoToFiat",
            }
        ]

        with patch(
            "handlers.initiate_trade.UserClient.get_user"
        ) as mock_get_user, patch(
            "handlers.initiate_trade.TradeClient.get_active_trades_for_user"
        ) as mock_get_trades:

            mock_get_user.return_value = mock_user
            mock_get_trades.return_value = mock_trades

            # Execute status handler
            await status_handler(mock_user_update, mock_context)

            # Verify message was sent
            mock_user_update.message.reply_text.assert_called_once()
            call_args = mock_user_update.message.reply_text.call_args
            message_text = call_args.args[0]

            # Verify status shows active trade
            assert "Active Trades" in message_text
            assert "1 trade" in message_text or "1" in message_text
