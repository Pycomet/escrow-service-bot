import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from telegram import CallbackQuery, Chat, Message, Update, User
from telegram.ext import ContextTypes

import config
from handlers.initiate_trade import handle_trade_type_selection, initiate_trade_handler
from handlers.trade_flows.fiat import CryptoFiatFlow

# ---------------------------------------------------------------------------
# Full PTB integration test for seller creating trade
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def event_loop():
    import asyncio

    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_update():
    """Create a mock Update object"""
    update = AsyncMock(spec=Update)
    update.effective_user = AsyncMock(spec=User)
    update.effective_user.id = 111  # seller_id
    update.effective_user.username = "seller"
    update.message = AsyncMock(spec=Message)
    update.message.from_user = update.effective_user
    update.message.chat = AsyncMock(spec=Chat)
    update.message.chat.id = 111
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
async def test_seller_creates_trade_flow(mock_update, mock_context):
    """Test seller creating a complete CryptoToFiat trade"""

    # Mock the database operations comprehensively
    with patch("config.db") as mock_db, patch(
        "functions.trade.db"
    ) as mock_trade_db, patch("functions.user.db") as mock_user_db, patch(
        "handlers.trade_flows.fiat.db"
    ) as mock_fiat_db:

        # Setup all database mocks
        for db_mock in [mock_db, mock_trade_db, mock_user_db, mock_fiat_db]:
            db_mock.trades.insert_one.return_value = MagicMock()
            db_mock.trades.find_one.return_value = {
                "_id": "test_trade_123",
                "seller_id": "111",
                "currency": "USDT",
                "price": 150,
                "trade_type": "CryptoToFiat",
                "status": "created",
            }
            db_mock.trades.update_one.return_value = MagicMock(modified_count=1)
            db_mock.users.find_one.return_value = {"_id": "111", "username": "seller"}

        # Mock other dependencies
        with patch(
            "handlers.initiate_trade.UserClient.get_user"
        ) as mock_get_user, patch(
            "handlers.initiate_trade.TradeClient.get_most_recent_trade"
        ) as mock_get_recent_trade, patch(
            "handlers.trade_flows.fiat.TradeClient.open_new_trade"
        ) as mock_open_trade, patch(
            "handlers.trade_flows.fiat.TradeClient.get_invoice_url"
        ) as mock_get_invoice_url, patch(
            "handlers.trade_flows.fiat.TradeClient.get_trade"
        ) as mock_get_trade, patch(
            "handlers.trade_flows.fiat.TradeClient.add_terms"
        ) as mock_add_terms, patch(
            "handlers.trade_flows.fiat.currency_menu"
        ) as mock_currency_menu, patch(
            "utils.keyboard.trade_type_menu"
        ) as mock_trade_type_menu:

            # Setup mocks
            mock_get_user.return_value = {"_id": "111", "username": "seller"}
            mock_get_recent_trade.return_value = None
            mock_trade_type_menu.return_value = MagicMock()
            mock_currency_menu.return_value = MagicMock()
            mock_get_invoice_url.return_value = "https://test.invoice.url"
            mock_get_trade.return_value = {
                "_id": "test_trade_123",
                "seller_id": "111",
                "currency": "USDT",
                "price": 150,
                "is_wallet_trade": True,
            }
            mock_add_terms.return_value = True
            mock_open_trade.return_value = {
                "_id": "test_trade_123",
                "seller_id": "111",
                "currency": "USDT",
                "price": 150,
                "is_wallet_trade": True,
            }

            # Step 1: Start trade creation
            await initiate_trade_handler(mock_update, mock_context)

            # Verify trade creation started
            assert "trade_creation" in mock_context.user_data
            assert (
                mock_context.user_data["trade_creation"]["step"] == "select_trade_type"
            )

            # Step 2: Select trade type
            mock_update.callback_query.data = "trade_type_CryptoToFiat"
            mock_context.user_data["trade_creation"]["step"] = "select_trade_type"

            await handle_trade_type_selection(mock_update, mock_context)

            # Verify trade type was selected
            assert (
                mock_context.user_data["trade_creation"]["trade_type"] == "CryptoToFiat"
            )

            # Step 3: Enter amount
            mock_update.message.text = "150"
            mock_context.user_data["trade_creation"][
                "current_flow_step"
            ] = "AWAITING_AMOUNT"
            mock_context.user_data["trade_creation"][
                "active_flow_module"
            ] = "CryptoToFiat"

            await CryptoFiatFlow.handle_amount_input(mock_update, mock_context)

            # Verify amount was set
            assert mock_context.user_data["trade_creation"]["amount"] == 150.0

            # Step 4: Select currency
            mock_update.callback_query.data = "currency_USDT"
            mock_context.user_data["trade_creation"][
                "current_flow_step"
            ] = "AWAITING_CURRENCY"

            await CryptoFiatFlow.handle_currency_selection(
                mock_update.callback_query, mock_context
            )

            # Verify currency was set
            assert mock_context.user_data["trade_creation"]["currency"] == "USDT"

            # Step 5: Enter description/terms
            mock_update.message.text = "Selling 150 USDT, pay 150 EUR via SEPA."
            mock_context.user_data["trade_creation"][
                "current_flow_step"
            ] = "AWAITING_DESCRIPTION"

            await CryptoFiatFlow.handle_description_input(mock_update, mock_context)

            # Verify trade was created
            mock_open_trade.assert_called_once()

            # Verify terms were added
            mock_add_terms.assert_called_once()

            # Verify trade was stored in database (via the mock)
            assert mock_open_trade.called
