import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add project root to allow imports from the main project
# This might already be handled by conftest.py or pytest configuration (e.g., pyproject.toml)
if os.path.abspath(os.path.join(os.path.dirname(__file__), "..")) not in sys.path:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from telegram import (
    CallbackQuery,
    Chat,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    Update,
    User,
)
from telegram.ext import ContextTypes

# Import the flow and its states
from handlers.trade_flows.fiat import (
    AWAITING_AMOUNT,
    AWAITING_CURRENCY,
    AWAITING_DEPOSIT_CONFIRMATION,
    AWAITING_DESCRIPTION,
    CryptoFiatFlow,
)

# Import shared fixtures if they are not automatically discovered from conftest.py
# (pytest usually discovers them automatically)
# from ..conftest import mock_update, mock_context # If conftest is one level up


# Re-define or import mock_update and mock_context if not using a shared conftest
# For simplicity here, using the ones from test_handlers.py as a template
@pytest.fixture
def mock_update_fiat():
    update = AsyncMock(spec=Update)
    update.effective_user = AsyncMock(spec=User)
    update.effective_user.id = 123
    update.effective_user.username = "testuser"
    update.message = AsyncMock(spec=Message)
    update.message.from_user = update.effective_user
    update.message.chat = AsyncMock(spec=Chat)
    update.message.chat.id = 123
    update.callback_query = AsyncMock(spec=CallbackQuery)
    update.callback_query.from_user = update.effective_user
    update.callback_query.message = (
        update.message
    )  # Link query's message to update's message
    update.callback_query.data = ""
    update.message.text = ""  # Default to empty text
    return update


@pytest.fixture
def mock_context_fiat():
    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {}
    context.bot = AsyncMock()
    # context.application = AsyncMock() # Less likely needed directly by flow logic
    return context


@pytest.mark.asyncio
async def test_start_initial_setup(mock_update_fiat, mock_context_fiat):
    """Test the start_initial_setup method of CryptoFiatFlow."""
    query = mock_update_fiat.callback_query
    context = mock_context_fiat
    context.user_data["trade_creation"] = {}  # Initial state for trade creation

    await CryptoFiatFlow.start_initial_setup(query, context)

    # Assertions
    query.message.edit_text.assert_called_once()
    args, kwargs = query.message.edit_text.call_args
    assert f"Kicking off a <b>{CryptoFiatFlow.FLOW_NAME}</b> trade!" in args[0]
    assert "exact amount of cryptocurrency" in args[0]
    assert kwargs["parse_mode"] == "HTML"
    assert isinstance(kwargs["reply_markup"], InlineKeyboardMarkup)
    assert kwargs["reply_markup"].inline_keyboard[0][0].text == "❌ Cancel Setup"
    assert (
        kwargs["reply_markup"].inline_keyboard[0][0].callback_data == "cancel_creation"
    )

    assert context.user_data["trade_creation"]["current_flow_step"] == AWAITING_AMOUNT
    assert (
        context.user_data["trade_creation"]["active_flow_module"]
        == CryptoFiatFlow.FLOW_NAME
    )


@pytest.mark.asyncio
async def test_handle_amount_input_valid(mock_update_fiat, mock_context_fiat):
    """Test handle_amount_input with a valid amount."""
    update = mock_update_fiat
    context = mock_context_fiat

    # Setup context for this step
    context.user_data["trade_creation"] = {
        "current_flow_step": AWAITING_AMOUNT,
        "active_flow_module": CryptoFiatFlow.FLOW_NAME,
    }
    update.message.text = "0.5"

    with patch(
        "handlers.trade_flows.fiat.currency_menu",
        return_value=AsyncMock(spec=InlineKeyboardMarkup),
    ) as mock_currency_menu:
        await CryptoFiatFlow.handle_amount_input(update, context)

        # Assertions
        update.message.reply_text.assert_called_once()
        args, kwargs = update.message.reply_text.call_args
        assert "select the crypto currency" in args[0]
        mock_currency_menu.assert_called_once_with("crypto")
        assert kwargs["reply_markup"] == mock_currency_menu.return_value

        assert context.user_data["trade_creation"]["amount"] == 0.5
        assert (
            context.user_data["trade_creation"]["current_flow_step"]
            == AWAITING_CURRENCY
        )


@pytest.mark.asyncio
async def test_handle_amount_input_invalid_value(mock_update_fiat, mock_context_fiat):
    """Test handle_amount_input with an invalid (non-positive) amount."""
    update = mock_update_fiat
    context = mock_context_fiat
    context.user_data["trade_creation"] = {
        "current_flow_step": AWAITING_AMOUNT,
        "active_flow_module": CryptoFiatFlow.FLOW_NAME,
    }
    update.message.text = "-10"

    await CryptoFiatFlow.handle_amount_input(update, context)

    update.message.reply_text.assert_called_once()
    args, _ = update.message.reply_text.call_args
    assert "Invalid amount" in args[0]
    assert (
        context.user_data["trade_creation"].get("amount") is None
    )  # Amount should not be set
    assert (
        context.user_data["trade_creation"]["current_flow_step"] == AWAITING_AMOUNT
    )  # Should remain in amount step


@pytest.mark.asyncio
async def test_handle_amount_input_invalid_format(mock_update_fiat, mock_context_fiat):
    """Test handle_amount_input with an invalid format (not a number)."""
    update = mock_update_fiat
    context = mock_context_fiat
    context.user_data["trade_creation"] = {
        "current_flow_step": AWAITING_AMOUNT,
        "active_flow_module": CryptoFiatFlow.FLOW_NAME,
    }
    update.message.text = "abc"

    await CryptoFiatFlow.handle_amount_input(update, context)

    update.message.reply_text.assert_called_once()
    args, _ = update.message.reply_text.call_args
    assert "Invalid amount" in args[0]
    assert context.user_data["trade_creation"].get("amount") is None
    assert context.user_data["trade_creation"]["current_flow_step"] == AWAITING_AMOUNT


# Placeholder for more tests (currency selection, description, deposit check)

# ============= BROKER FLOW TESTS (SIMPLIFIED) =============


@pytest.mark.asyncio
async def test_broker_functionality_placeholder():
    """Placeholder test for broker functionality - to be enhanced later"""
    # For now, we'll add a simple test that verifies the broker classes exist
    # This ensures the broker functionality is properly integrated
    # Full broker integration tests will be added in a future iteration

    try:
        from functions.broker import BrokerClient
        from handlers.broker import register_broker_handlers

        assert True  # Basic import test passed
    except ImportError:
        assert False, "Broker modules not properly integrated"
