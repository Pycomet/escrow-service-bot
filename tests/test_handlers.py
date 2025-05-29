import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock, ANY
import sys
import os

# Add project root to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram import Update, User, Message, Chat, CallbackQuery, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Updated imports: removed handle_trade_amount, handle_trade_currency, handle_trade_description
from handlers.initiate_trade import (
    initiate_trade_handler, 
    handle_trade_type_selection, # Assuming this is the correct handler for type selection logic testing
    cancel_handler,
    dispatch_to_flow, # For testing the dispatcher if needed, though flow tests might cover it
    handle_check_deposit_callback # For testing deposit check routing
)
# Import TradeFlowHandler if we need to mock its methods called by initiate_trade handlers
from handlers.trade_flows import TradeFlowHandler
from utils.enums import TradeTypeEnums # For setting up trade_type in tests
from utils.keyboard import trade_type_menu # Import trade_type_menu


@pytest.fixture
def mock_update():
    """Create a mock Update object for testing"""
    update = AsyncMock(spec=Update)
    update.effective_user = AsyncMock(spec=User)
    update.effective_user.id = 123456
    update.effective_user.username = "testuser"
    
    update.message = AsyncMock(spec=Message)
    update.message.from_user = update.effective_user
    update.message.chat = AsyncMock(spec=Chat)
    update.message.chat.id = 123456
    update.message.text = "initial_message_text"
    # Ensure reply_text is an AsyncMock if it's awaited or needs assertions like assert_called_once
    update.message.reply_text = AsyncMock()

    update.callback_query = AsyncMock(spec=CallbackQuery)
    update.callback_query.from_user = update.effective_user
    update.callback_query.message = update.message 
    update.callback_query.data = "initial_callback_data"
    # Ensure answer and edit_message_text are AsyncMocks
    update.callback_query.answer = AsyncMock()
    update.callback_query.message.edit_text = AsyncMock() # cq.message can be different from update.message
    
    return update


@pytest.fixture
def mock_context():
    """Create a mock Context object for testing"""
    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {}
    context.bot = AsyncMock()
    # context.application = AsyncMock() # Usually not needed for handler logic testing directly
    return context


@pytest.mark.asyncio
async def test_initiate_trade_handler(mock_update, mock_context):
    """Test the /trade command handler successfully initiates trade type selection."""
    # Nested with statements for clarity and linter compatibility
    with patch('handlers.initiate_trade.UserClient.get_user', return_value={"_id": mock_update.effective_user.id}) as mock_get_user:
        with patch('handlers.initiate_trade.TradeClient.get_most_recent_trade', return_value=None) as mock_get_recent_trade:
            with patch('handlers.initiate_trade.trade_type_menu', new_callable=AsyncMock) as mock_trade_type_menu_call:
                
                mock_trade_type_menu_call.return_value = MagicMock(spec=InlineKeyboardMarkup) # Mock keyboard object

                await initiate_trade_handler(mock_update, mock_context)
                
                assert "trade_creation" in mock_context.user_data
                assert mock_context.user_data["trade_creation"]["step"] == "select_trade_type"
                
                mock_get_user.assert_called_once_with(mock_update.message)
                mock_get_recent_trade.assert_called_once_with(mock_get_user.return_value)
                mock_trade_type_menu_call.assert_called_once() 
                mock_update.message.reply_text.assert_called_once()
                args, _ = mock_update.message.reply_text.call_args
                assert "Please select the type of trade" in args[0]

@pytest.mark.asyncio
async def test_initiate_trade_handler_with_active_trade(mock_update, mock_context):
    """Test /trade command handler when user already has an active trade."""
    # Nested with statements
    with patch('handlers.initiate_trade.UserClient.get_user', return_value={"_id": mock_update.effective_user.id}) as mock_get_user:
        with patch('handlers.initiate_trade.TradeClient.get_most_recent_trade', return_value={"_id": "existing_trade_123", "is_active": True}) as mock_get_recent_trade:

            await initiate_trade_handler(mock_update, mock_context)
            
            assert "trade_creation" not in mock_context.user_data
            mock_get_user.assert_called_once_with(mock_update.message)
            mock_get_recent_trade.assert_called_once_with(mock_get_user.return_value)
            mock_update.message.reply_text.assert_called_once()
            args, _ = mock_update.message.reply_text.call_args
            assert "You already have an active trade" in args[0]

# Removed test_handle_trade_amount
# Removed test_handle_trade_amount_invalid
# Removed test_handle_trade_currency
# Removed test_handle_trade_description

@pytest.mark.asyncio
async def test_handle_trade_type_selection_valid(mock_update, mock_context):
    """Test handling a valid trade type selection."""
    mock_context.user_data["trade_creation"] = {"step": "select_trade_type"}
    mock_update.callback_query.data = f"trade_type_{TradeTypeEnums.CRYPTO_FIAT.value}"

    with patch.object(TradeFlowHandler, 'initiate_flow_setup', new_callable=AsyncMock) as mock_initiate_flow:
        mock_initiate_flow.return_value = True

        await handle_trade_type_selection(mock_update, mock_context)

        mock_update.callback_query.answer.assert_called_once()
        mock_initiate_flow.assert_called_once_with(mock_update, mock_context, TradeTypeEnums.CRYPTO_FIAT.value)
        
        assert mock_context.user_data["trade_creation"]["trade_type"] == TradeTypeEnums.CRYPTO_FIAT.value
        assert mock_context.user_data["trade_creation"]["step"] == "flow_initiated"

@pytest.mark.asyncio
async def test_handle_trade_type_selection_disabled(mock_update, mock_context):
    """Test handling a disabled trade type selection."""
    mock_context.user_data["trade_creation"] = {"step": "select_trade_type"}
    mock_update.callback_query.data = "trade_type_Disabled"

    await handle_trade_type_selection(mock_update, mock_context)

    mock_update.callback_query.answer.assert_called_once()
    mock_update.callback_query.message.edit_text.assert_called_once()
    args, _ = mock_update.callback_query.message.edit_text.call_args
    assert "This feature is currently not available" in args[0]
    # Ensure trade_creation state is not advanced
    assert mock_context.user_data["trade_creation"]["step"] == "select_trade_type"
    assert "trade_type" not in mock_context.user_data["trade_creation"]

@pytest.mark.asyncio
async def test_handle_trade_type_selection_invalid(mock_update, mock_context):
    """Test handling an invalid trade type selection."""
    mock_context.user_data["trade_creation"] = {"step": "select_trade_type"}
    mock_update.callback_query.data = "trade_type_InvalidFlow"

    await handle_trade_type_selection(mock_update, mock_context)

    mock_update.callback_query.answer.assert_called_once()
    mock_update.callback_query.message.edit_text.assert_called_once()
    args, _ = mock_update.callback_query.message.edit_text.call_args
    assert "Invalid trade type selected" in args[0]
    assert "trade_creation" not in mock_context.user_data # Context should be cleared


@pytest.mark.asyncio
async def test_cancel_handler_with_active_creation(mock_update, mock_context):
    """Test canceling an active trade creation process via message."""
    mock_context.user_data["trade_creation"] = {"step": "some_step"}
    # Simulate it being called from a message for this test case
    mock_update.callback_query = None 

    await cancel_handler(mock_update, mock_context)
    
    assert "trade_creation" not in mock_context.user_data
    mock_update.message.reply_text.assert_called_once()
    args, _ = mock_update.message.reply_text.call_args
    assert "Trade creation process has been cancelled" in args[0]

@pytest.mark.asyncio
async def test_cancel_handler_with_callback_query(mock_update: Update, mock_context: ContextTypes.DEFAULT_TYPE):
    """Test canceling an active trade creation process via callback query using patch.object."""
    mock_context.user_data["trade_creation"] = {"step": "some_step"}
    # Ensure update.message is None so the callback_query path in cancel_handler is taken
    mock_update.message = None 

    # 1. Prepare the mock for the message object that the callback query will have
    # This is the object whose edit_text method we expect to be called.
    the_message_to_be_edited = AsyncMock(spec=Message)
    the_message_to_be_edited.edit_text = AsyncMock() # This is the crucial mock for assertion

    # 2. Prepare the mock for the callback_query itself.
    # This mock will be injected into mock_update.callback_query.
    callback_query_to_inject = AsyncMock(spec=CallbackQuery)
    callback_query_to_inject.answer = AsyncMock() # Mock the answer method
    callback_query_to_inject.message = the_message_to_be_edited # Link to our message mock
    # If the handler uses from_user or data, set them up here too:
    callback_query_to_inject.from_user = mock_update.effective_user 
    callback_query_to_inject.data = "cancel_callback_data"

    # 3. Use patch.object to replace mock_update.callback_query with our prepared mock.
    #    Also, patch InlineKeyboardMarkup to control its behavior.
    with patch.object(mock_update, 'callback_query', callback_query_to_inject), \
         patch('handlers.initiate_trade.InlineKeyboardMarkup', return_value=MagicMock(spec=InlineKeyboardMarkup)) as mock_ikm_constructor:
        
        # At this point, inside cancel_handler, update.callback_query will be callback_query_to_inject
        # and update.callback_query.message will be the_message_to_be_edited.
        await cancel_handler(mock_update, mock_context)

    # 4. Assertions:
    # Ensure the trade creation process was cleared from user_data
    assert "trade_creation" not in mock_context.user_data
    
    # Assert that the answer method of our injected callback_query mock was called
    callback_query_to_inject.answer.assert_called_once()
    
    # Assert that the edit_text method of our message mock was called
    the_message_to_be_edited.edit_text.assert_called_once()
    
    # Check the arguments passed to edit_text
    args, kwargs = the_message_to_be_edited.edit_text.call_args
    assert "Trade creation process has been cancelled" in args[0]
    assert 'reply_markup' in kwargs
    
    # Check that our InlineKeyboardMarkup mock constructor was called
    mock_ikm_constructor.assert_called_once()
    # Check that the instance returned by our mock constructor was passed to edit_text
    assert kwargs['reply_markup'] is mock_ikm_constructor.return_value

@pytest.mark.asyncio
async def test_cancel_handler_no_active_creation(mock_update, mock_context):
    """Test canceling when no trade creation is active."""
    # Ensure trade_creation is not in context
    if "trade_creation" in mock_context.user_data: 
        del mock_context.user_data["trade_creation"]
    mock_update.callback_query = None # Simulate message based

    await cancel_handler(mock_update, mock_context)

    mock_update.message.reply_text.assert_called_once()
    args, _ = mock_update.message.reply_text.call_args
    assert "You don't have any active trade creation process" in args[0]

# Tests for dispatch_to_flow and handle_check_deposit_callback would require more setup
# to mock the interaction with specific flow modules (e.g., CryptoFiatFlow methods).
# These are good candidates for future expansion of this test file. 