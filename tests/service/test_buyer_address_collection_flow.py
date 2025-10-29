import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from telegram import CallbackQuery, Chat, Message, Update, User
from telegram.ext import ContextTypes

import config
from handlers.join import handle_join_callback, handle_trade_id
from handlers.trade_flows.fiat import CryptoFiatFlow


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
    update.callback_query = AsyncMock(spec=CallbackQuery)
    update.callback_query.from_user = update.effective_user
    update.callback_query.message = update.message
    update.callback_query.data = ""
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
    """Create a mock context"""
    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {}
    context.bot = AsyncMock()
    return context


class TestBuyerAddressCollectionFlow:
    """Test the complete buyer address collection and payment monitoring flow"""

    @pytest.mark.asyncio
    async def test_complete_payment_to_address_flow(
        self, mock_seller_update, mock_buyer_update, mock_context
    ):
        """Test the complete flow from payment approval to address collection to crypto release"""

        test_trade_id = "complete_flow_test"
        usdt_address = "0x742d35cc6e3f4dc5bf5b123456789abcdef12345"

        # Mock trade object that evolves through the flow
        mock_trade = {
            "_id": test_trade_id,
            "seller_id": "111",
            "buyer_id": "222",
            "currency": "USDT",
            "price": 500.0,
            "trade_type": "CryptoToFiat",
            "is_active": True,
            "status": "payment_proof_submitted",
            "fiat_payment_approved": False,
            "terms": "Complete flow test",
        }

        with patch(
            "handlers.trade_flows.fiat.TradeClient.get_trade"
        ) as mock_get_trade, patch(
            "handlers.trade_flows.fiat.TradeClient.approve_fiat_payment"
        ) as mock_approve, patch(
            "handlers.trade_flows.fiat.TradeClient.request_buyer_address"
        ) as mock_request_address, patch(
            "handlers.join.db"
        ) as mock_db, patch(
            "handlers.join.TradeClient.set_buyer_address"
        ) as mock_set_address, patch(
            "handlers.join.TradeClient.initiate_crypto_release"
        ) as mock_release, patch(
            "handlers.join.TradeClient.complete_trade"
        ) as mock_complete:

            # Step 1: Seller approves payment
            mock_get_trade.return_value = mock_trade
            mock_approve.return_value = True
            mock_request_address.return_value = True
            mock_seller_update.callback_query.data = f"approve_payment_{test_trade_id}"

            # Execute payment approval
            await CryptoFiatFlow.handle_seller_payment_review(
                mock_seller_update, mock_context
            )

            # Verify seller got confirmation and buyer was notified
            mock_approve.assert_called_once_with(test_trade_id, "111")
            mock_request_address.assert_called_once_with(test_trade_id)
            mock_context.bot.send_message.assert_called()  # Buyer notification

            # Step 2: Buyer provides address
            # Update trade status for address collection
            mock_trade_awaiting_address = {
                **mock_trade,
                "status": "awaiting_buyer_address",
                "fiat_payment_approved": True,
            }
            mock_db.trades.find_one.return_value = mock_trade_awaiting_address
            mock_set_address.return_value = True
            mock_release.return_value = True
            mock_complete.return_value = True

            # Simulate buyer providing address
            mock_buyer_update.message.text = usdt_address

            # Execute address collection (this should be routed through handle_trade_id)
            await handle_trade_id(mock_buyer_update, mock_context)

            # Verify address was processed
            mock_set_address.assert_called_once_with(test_trade_id, usdt_address)
            mock_release.assert_called_once_with(test_trade_id)
            mock_complete.assert_called_once_with(test_trade_id)

            # Verify buyer got confirmation with payment status button
            mock_buyer_update.message.reply_text.assert_called()
            args, kwargs = mock_buyer_update.message.reply_text.call_args
            assert "Address Confirmed!" in args[0]
            assert usdt_address in args[0]

            # Check that payment status button is included
            reply_markup = kwargs.get("reply_markup")
            assert reply_markup is not None
            # The button should contain the payment status callback
            buttons_text = str(reply_markup.inline_keyboard)
            assert "payment_status" in buttons_text

    @pytest.mark.asyncio
    async def test_payment_status_monitoring_throughout_flow(
        self, mock_buyer_update, mock_context
    ):
        """Test payment status monitoring at different stages of the flow"""

        test_trade_id = "status_test"

        # Test status before address is provided
        mock_trade_before = {
            "_id": test_trade_id,
            "currency": "USDT",
            "price": 300.0,
            "buyer_address": "",  # No address yet
        }

        with patch("handlers.join.TradeClient.get_trade") as mock_get_trade:
            mock_get_trade.return_value = mock_trade_before
            mock_buyer_update.callback_query.data = f"payment_status_{test_trade_id}"

            # Import the function we need to test
            from handlers.join import handle_payment_status_callback

            # Execute status check before address
            await handle_payment_status_callback(
                mock_buyer_update.callback_query, mock_context, test_trade_id
            )

            # Verify "waiting for address" status
            mock_buyer_update.callback_query.message.edit_text.assert_called()
            args, _ = mock_buyer_update.callback_query.message.edit_text.call_args
            assert "Waiting for your USDT address" in args[0]
            assert "300.0" in args[0]

            # Test status after address is provided
            mock_trade_after = {
                "_id": test_trade_id,
                "currency": "USDT",
                "price": 300.0,
                "buyer_address": "0x742d35cc6e3f4dc5bf5b123456789abcdef12345",
            }

            mock_get_trade.return_value = mock_trade_after

            # Execute status check after address
            await handle_payment_status_callback(
                mock_buyer_update.callback_query, mock_context, test_trade_id
            )

            # Verify "payment sent" status
            args, _ = mock_buyer_update.callback_query.message.edit_text.call_args
            assert "Payment sent to your address" in args[0]
            assert "0x742d35cc6e3f4dc5bf5b123456789abcdef12345" in args[0]

    @pytest.mark.asyncio
    async def test_address_help_system(self, mock_buyer_update, mock_context):
        """Test the address help system for different cryptocurrencies"""

        test_trade_id = "help_test"

        # Test USDT help
        mock_usdt_trade = {"_id": test_trade_id, "currency": "USDT"}

        with patch("handlers.join.TradeClient.get_trade") as mock_get_trade:
            mock_get_trade.return_value = mock_usdt_trade

            from handlers.join import handle_address_help_callback

            # Execute USDT help
            await handle_address_help_callback(
                mock_buyer_update.callback_query, mock_context, test_trade_id
            )

            # Verify USDT-specific help content
            mock_buyer_update.callback_query.message.edit_text.assert_called()
            args, _ = mock_buyer_update.callback_query.message.edit_text.call_args
            assert "USDT Address Help" in args[0]
            assert "ERC-20 (Ethereum)" in args[0]
            assert "TRC-20 (Tron)" in args[0]
            assert "BSC (BEP-20)" in args[0]

            # Test ETH help
            mock_eth_trade = {"_id": test_trade_id, "currency": "ETH"}
            mock_get_trade.return_value = mock_eth_trade

            await handle_address_help_callback(
                mock_buyer_update.callback_query, mock_context, test_trade_id
            )

            args, _ = mock_buyer_update.callback_query.message.edit_text.call_args
            assert "ETH Address Help" in args[0]
            assert "Start with 0x" in args[0]
            assert "42 characters long" in args[0]

    @pytest.mark.asyncio
    async def test_error_handling_in_address_collection(
        self, mock_buyer_update, mock_context
    ):
        """Test error handling scenarios in address collection"""

        test_trade_id = "error_test"

        # Test invalid address handling
        mock_trade = {
            "_id": test_trade_id,
            "buyer_id": "222",
            "currency": "USDT",
            "status": "awaiting_buyer_address",
            "fiat_payment_approved": True,
        }

        with patch("handlers.join.db") as mock_db:
            mock_db.trades.find_one.return_value = mock_trade
            mock_buyer_update.message.text = "invalid_address"

            # Execute with invalid address - call handle_buyer_address_input directly
            from handlers.join import handle_buyer_address_input

            await handle_buyer_address_input(mock_buyer_update, mock_context)

            # Verify error message
            mock_buyer_update.message.reply_text.assert_called()
            args, _ = mock_buyer_update.message.reply_text.call_args
            assert (
                "Invalid address format" in args[0]
                or "Invalid USDT address format" in args[0]
            )

    @pytest.mark.asyncio
    async def test_database_error_fallback(self, mock_buyer_update, mock_context):
        """Test that database errors don't break normal trade ID processing"""

        # Setup normal trade ID scenario
        mock_context.user_data = {"state": "waiting_for_trade_id"}
        mock_buyer_update.message.text = "normal_trade_123"

        mock_trade = {
            "_id": "normal_trade_123",
            "seller_id": "111",
            "currency": "USDT",
            "price": 200.0,
            "is_active": True,
            "status": "pending",  # Changed to pending so it can be joined
            "trade_type": "CryptoToFiat",  # Added trade type
        }

        with patch("handlers.join.db") as mock_db, patch(
            "handlers.join.TradeClient.get_trade"
        ) as mock_get_trade, patch(
            "handlers.join.UserClient.get_user"
        ) as mock_get_user:

            # Simulate database error in buyer address check
            mock_db.trades.find_one.side_effect = Exception("Database connection error")

            # Setup normal trade ID flow
            mock_get_trade.return_value = mock_trade
            mock_get_user.return_value = {"_id": "222", "username": "buyer"}

            # Execute - should fall back to normal trade ID processing
            await handle_trade_id(mock_buyer_update, mock_context)

            # Verify normal trade ID processing occurred
            mock_get_trade.assert_called_once_with("normal_trade_123")
            mock_buyer_update.message.reply_text.assert_called()

            # Should show trade details, not error message
            args, _ = mock_buyer_update.message.reply_text.call_args
            assert (
                "Trade Details" in args[0]
                or "USDT" in args[0]
                or "normal_trade_123" in args[0]
            )  # Trade info shown
