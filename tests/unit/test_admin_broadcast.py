import asyncio
import os
import sys
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest

# Add project root to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from telegram import Bot, CallbackQuery, Chat, InlineKeyboardMarkup, Message, Update, User
from telegram.ext import ContextTypes

from handlers.admin import AdminBroadcastManager, admin_broadcast_handler, admin_broadcast_confirm_handler


class TestAdminBroadcastManager:
    """Test suite for AdminBroadcastManager functionality"""

    @pytest.mark.asyncio
    async def test_get_all_users_for_broadcast_success(self):
        """Test successful user data retrieval with proper categorization"""
        
        # Mock user data from database
        mock_users = [
            {"_id": "123", "chat": "123", "disabled": False, "name": "Alice"},
            {"_id": "456", "chat": "-456", "disabled": False, "name": "Group1"},
            {"_id": "789", "chat": "789", "disabled": True, "name": "Bob"},
            {"_id": "101", "chat": "-101", "disabled": True, "name": "Group2"},
            {"_id": "202", "chat": "202", "disabled": False, "name": "Charlie"},
        ]
        
        with patch('handlers.admin.db') as mock_db:
            mock_db.users.find.return_value = mock_users
            
            result = await AdminBroadcastManager.get_all_users_for_broadcast()
            
            assert result is not None
            assert result['stats']['total_users'] == 5
            assert result['stats']['active_users'] == 3
            assert result['stats']['disabled_users'] == 2
            assert result['stats']['private_chats'] == 3  # 123, 789, 202
            assert result['stats']['group_chats'] == 2   # -456, -101
            
            # Verify active users are correctly identified
            active_user_ids = [user['_id'] for user in result['active_users']]
            assert "123" in active_user_ids
            assert "456" in active_user_ids
            assert "202" in active_user_ids
            assert "789" not in active_user_ids  # disabled
            assert "101" not in active_user_ids  # disabled

    @pytest.mark.asyncio
    async def test_get_all_users_for_broadcast_database_error(self):
        """Test error handling when database query fails"""
        
        with patch('handlers.admin.db') as mock_db:
            mock_db.users.find.side_effect = Exception("Database connection error")
            
            result = await AdminBroadcastManager.get_all_users_for_broadcast()
            
            assert result is None

    def test_create_broadcast_message(self):
        """Test broadcast message creation with proper formatting"""
        
        with patch('handlers.admin.REVIEW_CHANNEL', 'test_reviews'), \
             patch('handlers.admin.TRADING_CHANNEL', 'test_trading'), \
             patch('handlers.admin.CONTACT_SUPPORT', 'test_support'):
            
            message = AdminBroadcastManager.create_broadcast_message()
            
            assert "🚀" in message
            assert "Your Escrow Service: Now Faster & More Secure!" in message
            assert "@test_reviews" in message
            assert "@test_trading" in message
            assert "@test_support" in message
            assert "<code>/start</code>" in message
            assert len(message) > 100  # Ensure message has substantial content

    @pytest.mark.asyncio
    async def test_send_broadcast_message_success(self):
        """Test successful broadcast message sending with rate limiting"""
        
        # Mock users data
        users_data = {
            'active_users': [
                {"_id": "123", "chat": "123", "name": "Alice"},
                {"_id": "456", "chat": "456", "name": "Bob"},
            ],
            'stats': {'active_users': 2}
        }
        
        # Mock bot
        mock_bot = AsyncMock(spec=Bot)
        mock_bot.send_message = AsyncMock()
        
        # Mock progress callback
        progress_callback = AsyncMock()
        
        with patch('asyncio.sleep', new_callable=AsyncMock):  # Speed up test
            result = await AdminBroadcastManager.send_broadcast_message(
                mock_bot, users_data, progress_callback
            )
        
        # Verify results
        assert result['sent_successfully'] == 2
        assert result['failed_sends'] == 0
        assert result['private_successful'] == 2
        assert result['group_successful'] == 0
        
        # Verify bot.send_message was called correctly
        assert mock_bot.send_message.call_count == 2
        mock_bot.send_message.assert_any_call(
            chat_id="123",
            text=ANY,
            parse_mode='HTML'
        )
        mock_bot.send_message.assert_any_call(
            chat_id="456", 
            text=ANY,
            parse_mode='HTML'
        )

    @pytest.mark.asyncio
    async def test_send_broadcast_message_with_failures(self):
        """Test broadcast handling of blocked users and failures"""
        
        users_data = {
            'active_users': [
                {"_id": "123", "chat": "123", "name": "Alice"},
                {"_id": "456", "chat": "456", "name": "Bob"},
                {"_id": "789", "chat": "-789", "name": "Group"},
            ],
            'stats': {'active_users': 3}
        }
        
        mock_bot = AsyncMock(spec=Bot)
        
        # Configure mock to fail for specific users
        def mock_send_message(**kwargs):
            if kwargs['chat_id'] == "456":
                raise Exception("Forbidden: bot was blocked by the user")
            elif kwargs['chat_id'] == "-789":
                raise Exception("Bad Request: chat not found")
            return AsyncMock()
        
        mock_bot.send_message.side_effect = mock_send_message
        
        with patch('asyncio.sleep', new_callable=AsyncMock):
            result = await AdminBroadcastManager.send_broadcast_message(
                mock_bot, users_data, None
            )
        
        # Verify failure handling
        assert result['sent_successfully'] == 1
        assert result['failed_sends'] == 2
        assert result['blocked_users'] == 1  # User 456
        assert result['invalid_chats'] == 1  # Group -789
        assert result['private_successful'] == 1  # User 123
        assert len(result['errors']) == 2


class TestAdminBroadcastHandlers:
    """Test suite for admin broadcast handler functions"""
    
    @pytest.fixture
    def mock_update_callback(self):
        """Create mock callback query update"""
        update = AsyncMock(spec=Update)
        update.callback_query = AsyncMock(spec=CallbackQuery)
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.callback_query.from_user = AsyncMock(spec=User)
        update.callback_query.from_user.id = 123456
        return update
    
    @pytest.fixture
    def mock_context(self):
        """Create mock context"""
        context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {}
        context.bot = AsyncMock(spec=Bot)
        return context

    @pytest.mark.asyncio
    async def test_admin_broadcast_handler_success(self, mock_update_callback, mock_context):
        """Test successful broadcast handler initiation"""
        
        mock_users_data = {
            'stats': {
                'total_users': 10,
                'active_users': 8,
                'disabled_users': 2,
                'private_chats': 6,
                'group_chats': 4
            }
        }
        
        with patch.object(AdminBroadcastManager, 'get_all_users_for_broadcast', 
                         return_value=mock_users_data), \
             patch.object(AdminBroadcastManager, 'create_broadcast_message',
                         return_value="Test message"):
            
            await admin_broadcast_handler(mock_update_callback, mock_context)
            
            # Verify confirmation message was sent
            mock_update_callback.callback_query.edit_message_text.assert_called_once()
            args = mock_update_callback.callback_query.edit_message_text.call_args
            
            assert "Broadcast Message Confirmation" in args[0][0]
            assert "8" in args[0][0]  # active users count
            assert "2" in args[0][0]  # disabled users count
            
            # Verify users data stored in context
            assert 'broadcast_users_data' in mock_context.user_data

    @pytest.mark.asyncio
    async def test_admin_broadcast_handler_no_users(self, mock_update_callback, mock_context):
        """Test broadcast handler when no users found"""
        
        with patch.object(AdminBroadcastManager, 'get_all_users_for_broadcast', 
                         return_value=None):
            
            await admin_broadcast_handler(mock_update_callback, mock_context)
            
            # Verify error message was sent
            mock_update_callback.callback_query.edit_message_text.assert_called_once()
            args = mock_update_callback.callback_query.edit_message_text.call_args
            
            assert "Error" in args[0][0]
            assert "Failed to fetch user data" in args[0][0]

    @pytest.mark.asyncio
    async def test_admin_broadcast_confirm_handler_success(self, mock_update_callback, mock_context):
        """Test successful broadcast confirmation and execution"""
        
        # Setup context with users data
        mock_users_data = {
            'active_users': [{"_id": "123", "chat": "123", "name": "Alice"}],
            'stats': {'active_users': 1, 'disabled_users': 0}
        }
        mock_context.user_data['broadcast_users_data'] = mock_users_data
        
        # Mock successful broadcast result
        mock_result = {
            'sent_successfully': 1,
            'failed_sends': 0,
            'blocked_users': 0,
            'invalid_chats': 0,
            'private_successful': 1,
            'group_successful': 0,
            'private_failed': 0,
            'group_failed': 0
        }
        
        with patch.object(AdminBroadcastManager, 'send_broadcast_message',
                         return_value=mock_result):
            
            await admin_broadcast_confirm_handler(mock_update_callback, mock_context)
            
            # Verify multiple message updates (progress and final)
            assert mock_update_callback.callback_query.edit_message_text.call_count >= 2
            
            # Check that final message contains success information
            final_call_args = mock_update_callback.callback_query.edit_message_text.call_args_list[-1]
            final_message = final_call_args[0][0]
            
            assert "Broadcast Completed!" in final_message
            assert "Successfully Sent: 1" in final_message
            assert "100.0%" in final_message  # Success rate

    @pytest.mark.asyncio
    async def test_admin_broadcast_confirm_handler_no_data(self, mock_update_callback, mock_context):
        """Test broadcast confirmation when session data is missing"""
        
        # Context without broadcast data
        mock_context.user_data = {}
        
        await admin_broadcast_confirm_handler(mock_update_callback, mock_context)
        
        # Verify error message about expired session
        mock_update_callback.callback_query.edit_message_text.assert_called_once()
        args = mock_update_callback.callback_query.edit_message_text.call_args
        
        assert "Session expired" in args[0][0]

    @pytest.mark.asyncio
    async def test_admin_broadcast_confirm_handler_broadcast_failure(self, mock_update_callback, mock_context):
        """Test broadcast confirmation when broadcast execution fails"""
        
        # Setup context with users data
        mock_users_data = {
            'active_users': [{"_id": "123", "chat": "123", "name": "Alice"}],
            'stats': {'active_users': 1}
        }
        mock_context.user_data['broadcast_users_data'] = mock_users_data
        
        with patch.object(AdminBroadcastManager, 'send_broadcast_message',
                         side_effect=Exception("Network error")):
            
            await admin_broadcast_confirm_handler(mock_update_callback, mock_context)
            
            # Verify error message was sent
            final_call_args = mock_update_callback.callback_query.edit_message_text.call_args_list[-1]
            final_message = final_call_args[0][0]
            
            assert "Broadcast Failed" in final_message
            assert "Network error" in final_message


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 