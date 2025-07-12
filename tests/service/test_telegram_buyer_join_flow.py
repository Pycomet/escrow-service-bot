import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from telegram import CallbackQuery, Chat, Message, Update, User
from telegram.ext import ContextTypes

import config
from handlers.join import handle_join_callback, handle_trade_id, join_handler


# Test fixtures
@pytest.fixture
def mock_seller_update():
    """Create a mock Update object for seller"""
    update = AsyncMock(spec=Update)
    update.effective_user = AsyncMock(spec=User)
    update.effective_user.id = 111  # seller_id
    update.effective_user.username = "seller"
    update.message = AsyncMock(spec=Message)
    update.message.from_user = update.effective_user
    update.message.chat = AsyncMock(spec=Chat)
    update.message.chat.id = 111
    return update


@pytest.fixture
def mock_buyer_update():
    """Create a mock Update object for buyer"""
    update = AsyncMock(spec=Update)
    update.effective_user = AsyncMock(spec=User)
    update.effective_user.id = 222  # buyer_id
    update.effective_user.username = "buyer"
    update.message = AsyncMock(spec=Message)
    update.message.from_user = update.effective_user
    update.message.chat = AsyncMock(spec=Chat)
    update.message.chat.id = 222
    update.message.text = ""
    update.callback_query = AsyncMock(spec=CallbackQuery)
    update.callback_query.from_user = update.effective_user
    update.callback_query.message = update.message
    update.callback_query.data = ""
    return update


@pytest.fixture
def mock_context():
    """Create a mock Context object"""
    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {}
    context.bot = AsyncMock()
    return context


@pytest.mark.asyncio
async def test_buyer_joins_flow(mock_buyer_update, mock_context):
    """Test buyer joining an existing trade"""

    # Mock trade data
    test_trade_id = "test_trade_123"
    mock_trade = {
        "_id": test_trade_id,
        "seller_id": "111",
        "buyer_id": "",  # Empty string means no buyer
        "currency": "USDT",
        "price": 150,
        "trade_type": "CryptoToFiat",
        "is_active": True,
        "status": "deposited",
        "terms": "Test trade terms",
    }

    # Mock the database and other dependencies
    with patch("handlers.join.TradeClient.get_trade") as mock_get_trade, patch(
        "handlers.join.TradeClient.join_trade"
    ) as mock_join_trade, patch("handlers.join.UserClient.get_user") as mock_get_user:

        # Setup mocks
        mock_get_trade.return_value = mock_trade
        mock_join_trade.return_value = True
        mock_get_user.return_value = {"_id": "222", "username": "buyer"}

        # Step 1: Start join process
        await join_handler(mock_buyer_update, mock_context)

        # Verify join process started - check state was set
        assert mock_context.user_data.get("state") == "waiting_for_trade_id"

        # Step 2: Enter trade ID
        mock_buyer_update.message.text = test_trade_id
        mock_context.user_data["state"] = "waiting_for_trade_id"

        await handle_trade_id(mock_buyer_update, mock_context)

        # Verify trade details were shown
        mock_buyer_update.message.reply_text.assert_called()
        args, _ = mock_buyer_update.message.reply_text.call_args
        assert "Trade Details" in args[0]
        assert "150 USDT" in args[0]

        # Step 3: Confirm join
        mock_buyer_update.callback_query.data = f"confirm_join_{test_trade_id}"

        await handle_join_callback(mock_buyer_update, mock_context)

        # Verify join was attempted
        mock_join_trade.assert_called_once_with(test_trade_id, 222)

        # Verify success message
        mock_buyer_update.callback_query.message.edit_text.assert_called()
        args, _ = mock_buyer_update.callback_query.message.edit_text.call_args
        assert "Successfully Joined Trade" in args[0]
