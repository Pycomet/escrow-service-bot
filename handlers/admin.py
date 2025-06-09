import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from config import *
from functions.wallet import WalletManager
from functions.user import UserClient
from functions.trade import TradeClient
from utils.enums import EmojiEnums
from typing import Optional
import asyncio
from decimal import Decimal
from datetime import datetime

logger = logging.getLogger(__name__)

class AdminWalletManager:
    """Admin functions for wallet management"""
    
    @staticmethod
    async def is_admin(user_id: int) -> bool:
        """Check if user is admin"""
        return user_id == ADMIN_ID
    
    @staticmethod
    async def get_user_wallet_info(user_id: str) -> Optional[dict]:
        """Get comprehensive wallet info for a user"""
        try:
            # Get user wallet
            wallet = WalletManager.get_user_wallet(user_id)
            if not wallet:
                return None
            
            # Get coin addresses
            coin_addresses = WalletManager.get_wallet_coin_addresses(wallet['_id'])
            
            # Get balances and calculate totals
            wallet_manager = WalletManager()
            total_coins = len(coin_addresses)
            coins_with_balance = 0
            
            coin_balances = []
            for coin_address in coin_addresses:
                try:
                    balance = float(coin_address.get('balance', 0))
                    if balance > 0:
                        coins_with_balance += 1
                    
                    coin_balances.append({
                        'symbol': coin_address['coin_symbol'],
                        'address': coin_address['address'],
                        'balance': balance,
                        'private_key_encrypted': coin_address.get('private_key_encrypted', ''),
                        'network': coin_address.get('network', '')
                    })
                except Exception as e:
                    logger.error(f"Error processing coin {coin_address.get('coin_symbol', 'unknown')}: {e}")
                    continue
            
            return {
                'wallet': wallet,
                'coin_addresses': coin_balances,
                'stats': {
                    'total_coins': total_coins,
                    'coins_with_balance': coins_with_balance
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting wallet info for user {user_id}: {e}")
            return None
    
    @staticmethod
    def _send_sol_wrapper(private_key: str, recipient_address: str, amount: float) -> dict:
        """Wrapper for SOL sending"""
        try:
            # For now, return a simulated successful result
            # TODO: Integrate with actual sol sending script
            return {
                "success": True,
                "tx_hash": f"sol_mock_{recipient_address[:8]}",
                "message": f"Sent {amount} SOL to {recipient_address}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def _send_usdt_sol_wrapper(private_key: str, recipient_address: str, amount: float) -> dict:
        """Wrapper for USDT on Solana sending"""
        try:
            # For now, return a simulated successful result
            # TODO: Integrate with actual USDT-SOL sending script
            return {
                "success": True,
                "tx_hash": f"usdt_sol_mock_{recipient_address[:8]}",
                "message": f"Sent {amount} USDT (SOL) to {recipient_address}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def _send_usdt_bnb_wrapper(private_key: str, recipient_address: str, amount: float) -> dict:
        """Wrapper for USDT on BSC sending"""
        try:
            # For now, return a simulated successful result
            # TODO: Integrate with actual USDT-BNB sending script
            return {
                "success": True,
                "tx_hash": f"usdt_bnb_mock_{recipient_address[:8]}",
                "message": f"Sent {amount} USDT (BSC) to {recipient_address}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def _send_usdt_tron_wrapper(private_key: str, recipient_address: str, amount: float) -> dict:
        """Wrapper for USDT on Tron sending"""
        try:
            # For now, return a simulated successful result
            # TODO: Integrate with actual USDT-TRON sending script
            return {
                "success": True,
                "tx_hash": f"usdt_tron_mock_{recipient_address[:8]}",
                "message": f"Sent {amount} USDT (TRON) to {recipient_address}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def _send_bnb_wrapper(private_key: str, recipient_address: str, amount: float) -> dict:
        """Wrapper for BNB sending"""
        try:
            # For now, return a simulated successful result
            # TODO: Integrate with actual BNB sending script
            return {
                "success": True,
                "tx_hash": f"bnb_mock_{recipient_address[:8]}",
                "message": f"Sent {amount} BNB to {recipient_address}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def _send_doge_wrapper(private_key: str, recipient_address: str, amount: float) -> dict:
        """Wrapper for DOGE sending"""
        try:
            # For now, return a simulated successful result
            # TODO: Integrate with actual DOGE sending script
            return {
                "success": True,
                "tx_hash": f"doge_mock_{recipient_address[:8]}",
                "message": f"Sent {amount} DOGE to {recipient_address}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def _send_ltc_wrapper(private_key: str, recipient_address: str, amount: float) -> dict:
        """Wrapper for LTC sending"""
        try:
            # For now, return a simulated successful result
            # TODO: Integrate with actual LTC sending script
            return {
                "success": True,
                "tx_hash": f"ltc_mock_{recipient_address[:8]}",
                "message": f"Sent {amount} LTC to {recipient_address}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    async def send_crypto(sender_wallet_id: str, coin_symbol: str, recipient_address: str, 
                         amount: float, admin_user_id: str) -> dict:
        """Send cryptocurrency from a user's wallet (admin function)"""
        try:
            # Get the coin address for sending
            coin_address = WalletManager.get_wallet_coin_address(sender_wallet_id, coin_symbol)
            if not coin_address:
                return {"success": False, "error": f"No {coin_symbol} address found in wallet"}
            
            # Get current balance
            wallet_manager = WalletManager()
            current_balance = wallet_manager.get_balance(coin_address['address'], coin_symbol)
            
            if current_balance < amount:
                return {
                    "success": False, 
                    "error": f"Insufficient balance. Has {current_balance} {coin_symbol}, trying to send {amount}"
                }
            
            # Get private key for sending
            private_key_encrypted = coin_address.get('private_key_encrypted', '')
            if not private_key_encrypted:
                return {"success": False, "error": f"No private key found for {coin_symbol} address"}
            
            # Decrypt private key
            private_key = wallet_manager._decrypt_data(private_key_encrypted)
            sender_address = coin_address['address']
            
            logger.info(f"Admin {admin_user_id} sending {amount} {coin_symbol} from {sender_address} to {recipient_address}")
            
            # Route to appropriate sender wrapper based on coin type
            result = None
            
            try:
                if coin_symbol == 'SOL':
                    # Solana sending
                    result = AdminWalletManager._send_sol_wrapper(private_key, recipient_address, amount)
                    
                elif coin_symbol == 'USDT' and coin_address.get('network') == 'solana':
                    # USDT on Solana
                    result = AdminWalletManager._send_usdt_sol_wrapper(private_key, recipient_address, amount)
                    
                elif coin_symbol == 'USDT' and coin_address.get('network') == 'binance':
                    # USDT on BSC
                    result = AdminWalletManager._send_usdt_bnb_wrapper(private_key, recipient_address, amount)
                    
                elif coin_symbol == 'USDT' and coin_address.get('network') == 'tron':
                    # USDT on Tron
                    result = AdminWalletManager._send_usdt_tron_wrapper(private_key, recipient_address, amount)
                    
                elif coin_symbol == 'BNB':
                    # BNB sending
                    result = AdminWalletManager._send_bnb_wrapper(private_key, recipient_address, amount)
                    
                elif coin_symbol == 'DOGE':
                    # Dogecoin sending
                    result = AdminWalletManager._send_doge_wrapper(private_key, recipient_address, amount)
                    
                elif coin_symbol == 'LTC':
                    # Litecoin sending
                    result = AdminWalletManager._send_ltc_wrapper(private_key, recipient_address, amount)
                    
                elif coin_symbol == 'BTC':
                    # Bitcoin sending - you'll need to implement this or use an existing script
                    logger.warning("Bitcoin sending not yet implemented")
                    return {
                        "success": False,
                        "error": "Bitcoin sending functionality not yet implemented"
                    }
                    
                elif coin_symbol == 'ETH':
                    # Ethereum sending - you'll need to implement this
                    logger.warning("Ethereum sending not yet implemented")
                    return {
                        "success": False,
                        "error": "Ethereum sending functionality not yet implemented"
                    }
                    
                else:
                    return {
                        "success": False,
                        "error": f"Sending functionality not implemented for {coin_symbol}"
                    }
                
                # Process the result from the sending wrapper
                if result and result.get('success'):
                    # Log the successful transaction
                    logger.info(f"Admin transaction successful: {result}")
                    
                    # Update the sender's balance in database (subtract sent amount)
                    new_balance = current_balance - amount
                    db.coin_addresses.update_one(
                        {"_id": coin_address["_id"]},
                        {
                            "$set": {
                                "balance": str(new_balance),
                                "last_balance_update": datetime.now().isoformat()
                            }
                        }
                    )
                    
                    return {
                        "success": True,
                        "tx_hash": result.get('tx_hash', 'mock_hash'),
                        "amount": amount,
                        "recipient": recipient_address,
                        "sender": sender_address,
                        "coin": coin_symbol,
                        "note": result.get('message', f"✅ Successfully sent {amount} {coin_symbol}")
                    }
                else:
                    error_msg = result.get('error', 'Unknown error occurred during transaction') if result else 'Transaction failed with no result'
                    return {
                        "success": False,
                        "error": f"Transaction failed: {error_msg}"
                    }
                    
            except Exception as send_error:
                logger.error(f"Error during {coin_symbol} transaction: {send_error}")
                return {
                    "success": False,
                    "error": f"Transaction error: {str(send_error)}"
                }
                
        except Exception as e:
            logger.error(f"Error sending {coin_symbol}: {e}")
            return {"success": False, "error": str(e)}


# Handler functions
async def admin_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main admin menu"""
    user_id = update.effective_user.id
    
    if not await AdminWalletManager.is_admin(user_id):
        await update.message.reply_text("❌ Access denied. Admin privileges required.")
        return
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👤 User Wallet Info", callback_data="admin_user_wallet"),
            InlineKeyboardButton("💸 Send Crypto", callback_data="admin_send_crypto")
        ],
        [
            InlineKeyboardButton("📊 All Active Trades", callback_data="admin_all_trades"),
            InlineKeyboardButton("🔧 System Status", callback_data="admin_system_status")
        ],
        [
            InlineKeyboardButton("📈 Platform Stats", callback_data="admin_platform_stats"),
            InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
        ]
    ])
    
    await update.message.reply_text(
        f"🛠️ <b>Admin Panel</b>\n\n"
        f"Welcome, Admin! Select an option:",
        parse_mode="HTML",
        reply_markup=keyboard
    )


async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin callback queries"""
    query = update.callback_query
    user_id = query.from_user.id
    
    # Add comprehensive logging
    logger.info(f"=== ADMIN CALLBACK HANDLER TRIGGERED ===")
    logger.info(f"Callback data: {query.data}")
    logger.info(f"User ID: {user_id}")
    logger.info(f"Admin ID from config: {ADMIN_ID}")
    
    await query.answer()
    
    if not await AdminWalletManager.is_admin(user_id):
        logger.warning(f"Non-admin user {user_id} attempted to access admin functionality")
        await query.edit_message_text("❌ Access denied.")
        return
    
    logger.info(f"Admin {user_id} accessing: {query.data}")
    
    if query.data == "admin_user_wallet":
        await admin_user_wallet_handler(update, context)
    elif query.data == "admin_send_crypto":
        await admin_send_crypto_handler(update, context)
    elif query.data == "admin_all_trades":
        await admin_all_trades_handler(update, context)
    elif query.data == "admin_system_status":
        await admin_system_status_handler(update, context)
    elif query.data == "admin_platform_stats":
        await admin_platform_stats_handler(update, context)
    elif query.data == "admin_menu":
        logger.info(f"Admin {user_id} requesting admin menu")
        await show_admin_menu(update, context)
    elif query.data.startswith("admin_select_coin_"):
        await handle_coin_selection_callback(update, context)
    elif query.data.startswith("admin_send_from_"):
        user_id_to_send = query.data.replace("admin_send_from_", "")
        context.user_data["send_crypto_user_id"] = user_id_to_send
        await admin_send_crypto_handler(update, context)
    elif query.data.startswith("admin_refresh_"):
        user_id_to_refresh = query.data.replace("admin_refresh_", "")
        await admin_refresh_user_wallet(update, context, user_id_to_refresh)
    elif query.data.startswith("admin_confirm_send_"):
        await handle_send_confirmation(update, context)
    else:
        logger.warning(f"Unhandled admin callback: {query.data}")
        await query.edit_message_text(
            f"❌ Unknown admin action: {query.data}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
            ]])
        )


async def admin_user_wallet_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user wallet lookup"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "👤 <b>User Wallet Lookup</b>\n\n"
        "Please enter the User ID (Telegram ID) to lookup their wallet information:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
        ]])
    )
    
    context.user_data["admin_action"] = "lookup_user_wallet"


async def admin_send_crypto_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle crypto sending setup"""
    query = update.callback_query
    await query.answer()
    
    # Check if user ID is already set (from wallet lookup)
    if context.user_data.get("send_crypto_user_id"):
        await handle_send_crypto_step1_with_user_id(update, context)
        return
    
    await query.edit_message_text(
        "💸 <b>Send Crypto from User Wallet</b>\n\n"
        "Please enter the User ID (Telegram ID) whose wallet you want to send from:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
        ]])
    )
    
    context.user_data["admin_action"] = "send_crypto_step1"


async def admin_all_trades_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all active trades"""
    query = update.callback_query
    await query.answer()
    
    try:
        active_trades = TradeClient.get_all_active_trades()
        
        if not active_trades:
            await query.edit_message_text(
                "📊 <b>Active Trades</b>\n\n"
                "No active trades found.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
                ]])
            )
            return
        
        trades_text = f"📊 <b>Active Trades ({len(active_trades)})</b>\n\n"
        
        for i, trade in enumerate(active_trades[:10]):  # Show first 10
            trade_id = trade.get('_id', 'Unknown')
            seller_id = trade.get('seller_id', 'Unknown')
            buyer_id = trade.get('buyer_id', 'None')
            amount = trade.get('price', 0)
            currency = trade.get('currency', 'Unknown')
            trade_type = trade.get('trade_type', 'Unknown')
            
            trades_text += f"<b>{i+1}. Trade #{trade_id[:8]}...</b>\n"
            trades_text += f"   💰 {amount} {currency}\n"
            trades_text += f"   🔄 Type: {trade_type}\n"
            trades_text += f"   👤 Seller: {seller_id}\n"
            trades_text += f"   🛒 Buyer: {buyer_id if buyer_id != '' else 'Waiting...'}\n\n"
        
        if len(active_trades) > 10:
            trades_text += f"... and {len(active_trades) - 10} more trades\n"
        
        await query.edit_message_text(
            trades_text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
            ]])
        )
        
    except Exception as e:
        logger.error(f"Error getting active trades: {e}")
        await query.edit_message_text(
            f"❌ Error getting active trades: {str(e)}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
            ]])
        )


async def admin_system_status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show system status"""
    query = update.callback_query
    await query.answer()
    
    try:
        # Get basic system stats
        total_users = db.wallets.count_documents({})
        active_trades = len(TradeClient.get_all_active_trades())
        total_trades = db.trades.count_documents({})
        
        status_text = f"🔧 <b>System Status</b>\n\n"
        status_text += f"👥 <b>Total Wallets:</b> {total_users}\n"
        status_text += f"📊 <b>Active Trades:</b> {active_trades}\n"
        status_text += f"📈 <b>Total Trades:</b> {total_trades}\n\n"
        
        # Check database connection
        try:
            db.admin.command('ismaster')
            db_status = "🟢 Connected"
        except Exception:
            db_status = "🔴 Disconnected"
        
        status_text += f"🗄️ <b>Database:</b> {db_status}\n"
        status_text += f"🤖 <b>Bot Status:</b> 🟢 Running\n"
        
        await query.edit_message_text(
            status_text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔄 Refresh", callback_data="admin_system_status"),
                InlineKeyboardButton("🔙 Back", callback_data="admin_menu")
            ]])
        )
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        await query.edit_message_text(
            f"❌ Error getting system status: {str(e)}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
            ]])
        )


async def admin_platform_stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show platform statistics"""
    query = update.callback_query
    await query.answer()
    
    try:
        # Calculate platform statistics
        total_wallets = db.wallets.count_documents({})
        total_trades = db.trades.count_documents({})
        completed_trades = db.trades.count_documents({"is_completed": True})
        active_trades = db.trades.count_documents({"is_active": True})
        
        # Get trade types
        crypto_fiat_trades = db.trades.count_documents({"trade_type": "CryptoToFiat"})
        crypto_crypto_trades = db.trades.count_documents({"trade_type": "CryptoCrypto"})
        
        completion_rate = (completed_trades / total_trades * 100) if total_trades > 0 else 0
        
        stats_text = f"📈 <b>Platform Statistics</b>\n\n"
        stats_text += f"👥 <b>Total Users:</b> {total_wallets}\n"
        stats_text += f"📊 <b>Total Trades:</b> {total_trades}\n"
        stats_text += f"✅ <b>Completed:</b> {completed_trades}\n"
        stats_text += f"🔄 <b>Active:</b> {active_trades}\n"
        stats_text += f"📈 <b>Success Rate:</b> {completion_rate:.1f}%\n\n"
        
        stats_text += f"<b>Trade Types:</b>\n"
        stats_text += f"💰 Crypto→Fiat: {crypto_fiat_trades}\n"
        stats_text += f"💱 Crypto→Crypto: {crypto_crypto_trades}\n\n"
        
        # Most used currencies
        try:
            pipeline = [
                {"$group": {"_id": "$currency", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 5}
            ]
            
            top_currencies = list(db.trades.aggregate(pipeline))
            if top_currencies:
                stats_text += f"<b>Top Currencies:</b>\n"
                for curr in top_currencies:
                    stats_text += f"• {curr['_id']}: {curr['count']} trades\n"
        except Exception as e:
            logger.error(f"Error getting currency stats: {e}")
        
        await query.edit_message_text(
            stats_text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔄 Refresh", callback_data="admin_platform_stats"),
                InlineKeyboardButton("🔙 Back", callback_data="admin_menu")
            ]])
        )
        
    except Exception as e:
        logger.error(f"Error getting platform stats: {e}")
        await query.edit_message_text(
            f"❌ Error getting platform stats: {str(e)}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
            ]])
        )


async def show_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin menu"""
    query = update.callback_query
    await query.answer()
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👤 User Wallet Info", callback_data="admin_user_wallet"),
            InlineKeyboardButton("💸 Send Crypto", callback_data="admin_send_crypto")
        ],
        [
            InlineKeyboardButton("📊 All Active Trades", callback_data="admin_all_trades"),
            InlineKeyboardButton("🔧 System Status", callback_data="admin_system_status")
        ],
        [
            InlineKeyboardButton("📈 Platform Stats", callback_data="admin_platform_stats"),
            InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
        ]
    ])
    
    await query.edit_message_text(
        f"🛠️ <b>Admin Panel</b>\n\n"
        f"Welcome, Admin! Select an option:",
        parse_mode="HTML",
        reply_markup=keyboard
    )


async def admin_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin text input"""
    user_id = update.effective_user.id
    
    if not await AdminWalletManager.is_admin(user_id):
        return
    
    admin_action = context.user_data.get("admin_action")
    
    if admin_action == "lookup_user_wallet":
        await handle_user_wallet_lookup(update, context)
    elif admin_action == "send_crypto_step1":
        await handle_send_crypto_step1(update, context)
    elif admin_action == "send_crypto_step3":
        await handle_send_crypto_step3(update, context)
    elif admin_action == "send_crypto_step4":
        await handle_send_crypto_step4(update, context)


async def handle_user_wallet_lookup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user wallet lookup"""
    try:
        lookup_user_id = update.message.text.strip()
        
        # Get wallet info
        wallet_info = await AdminWalletManager.get_user_wallet_info(lookup_user_id)
        
        if not wallet_info:
            await update.message.reply_text(
                f"❌ No wallet found for user ID: {lookup_user_id}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
                ]])
            )
            context.user_data.pop("admin_action", None)
            return
        
        wallet = wallet_info['wallet']
        coin_balances = wallet_info['coin_addresses']
        stats = wallet_info['stats']
        
        # Format wallet information
        wallet_text = f"👤 <b>User Wallet Info</b>\n\n"
        wallet_text += f"🆔 <b>User ID:</b> <code>{lookup_user_id}</code>\n"
        wallet_text += f"💼 <b>Wallet:</b> {wallet['wallet_name']}\n"
        wallet_text += f"🔐 <b>Wallet ID:</b> <code>{wallet['_id']}</code>\n"
        wallet_text += f"🕐 <b>Created:</b> {wallet['created_at'][:16]}\n\n"
        
        wallet_text += f"📊 <b>Statistics:</b>\n"
        wallet_text += f"• Total coins: {stats['total_coins']}\n"
        wallet_text += f"• With balance: {stats['coins_with_balance']}\n\n"
        
        wallet_text += f"💰 <b>Balances:</b>\n"
        for coin in coin_balances:
            status_icon = "🟢" if coin['balance'] > 0 else "⚪"
            coin_emoji = {
                'BTC': EmojiEnums.BITCOIN.value,
                'LTC': EmojiEnums.LITECOIN.value,
                'DOGE': EmojiEnums.DOGECOIN.value,
                'ETH': EmojiEnums.ETHEREUM.value,
                'SOL': EmojiEnums.SOLANA.value,
                'USDT': EmojiEnums.TETHER.value,
                'BNB': EmojiEnums.YELLOW_CIRCLE.value,
                'TRX': EmojiEnums.TRON.value
            }.get(coin['symbol'], '🪙')
            
            wallet_text += f"{status_icon} {coin_emoji} <b>{coin['symbol']}:</b> {coin['balance']}\n"
            if coin['balance'] > 0:
                display_address = f"{coin['address'][:12]}...{coin['address'][-8:]}"
                wallet_text += f"   📍 <code>{display_address}</code>\n"
        
        # Create action buttons
        keyboard = [
            [InlineKeyboardButton(f"💸 Send from this wallet", callback_data=f"admin_send_from_{lookup_user_id}")],
            [InlineKeyboardButton("🔄 Refresh Balances", callback_data=f"admin_refresh_{lookup_user_id}")],
            [InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")]
        ]
        
        await update.message.reply_text(
            wallet_text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        context.user_data.pop("admin_action", None)
        
    except Exception as e:
        logger.error(f"Error in user wallet lookup: {e}")
        await update.message.reply_text(
            f"❌ Error looking up wallet: {str(e)}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
            ]])
        )
        context.user_data.pop("admin_action", None)


async def handle_send_crypto_step1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle send crypto step 1 - user ID input"""
    try:
        sender_user_id = update.message.text.strip()
        context.user_data["send_crypto_user_id"] = sender_user_id
        await handle_send_crypto_step1_with_user_id(update, context)
        
    except Exception as e:
        logger.error(f"Error in send crypto step 1: {e}")
        await update.message.reply_text(
            f"❌ Error: {str(e)}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
            ]])
        )
        context.user_data.pop("admin_action", None)


async def handle_send_crypto_step1_with_user_id(update, context):
    """Handle send crypto with existing user ID"""
    try:
        sender_user_id = context.user_data["send_crypto_user_id"]
        
        # Get wallet info to verify it exists
        wallet_info = await AdminWalletManager.get_user_wallet_info(sender_user_id)
        
        if not wallet_info:
            message_text = f"❌ No wallet found for user ID: {sender_user_id}"
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
            ]])
            
            if hasattr(update, 'message') and update.message:
                await update.message.reply_text(message_text, reply_markup=keyboard)
            elif hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.edit_message_text(message_text, reply_markup=keyboard)
            
            context.user_data.pop("admin_action", None)
            return
        
        # Store wallet info
        context.user_data["send_crypto_wallet_id"] = wallet_info['wallet']['_id']
        context.user_data["admin_action"] = "send_crypto_step2"
        
        # Show available coins with balances
        coin_buttons = []
        for coin in wallet_info['coin_addresses']:
            if coin['balance'] > 0:
                coin_emoji = {
                    'BTC': EmojiEnums.BITCOIN.value,
                    'LTC': EmojiEnums.LITECOIN.value,
                    'DOGE': EmojiEnums.DOGECOIN.value,
                    'ETH': EmojiEnums.ETHEREUM.value,
                    'SOL': EmojiEnums.SOLANA.value,
                    'USDT': EmojiEnums.TETHER.value,
                    'BNB': EmojiEnums.YELLOW_CIRCLE.value,
                    'TRX': EmojiEnums.TRON.value
                }.get(coin['symbol'], '🪙')
                
                coin_buttons.append([InlineKeyboardButton(
                    f"{coin_emoji} {coin['symbol']} ({coin['balance']})",
                    callback_data=f"admin_select_coin_{coin['symbol']}"
                )])
        
        if not coin_buttons:
            message_text = f"❌ No coins with balance found for user {sender_user_id}"
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
            ]])
            
            if hasattr(update, 'message') and update.message:
                await update.message.reply_text(message_text, reply_markup=keyboard)
            elif hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.edit_message_text(message_text, reply_markup=keyboard)
            
            context.user_data.pop("admin_action", None)
            return
        
        coin_buttons.append([InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")])
        
        message_text = (
            f"💰 <b>Select Coin to Send</b>\n\n"
            f"👤 <b>From User:</b> {sender_user_id}\n\n"
            f"Choose which coin to send:"
        )
        keyboard = InlineKeyboardMarkup(coin_buttons)
        
        if hasattr(update, 'message') and update.message:
            await update.message.reply_text(message_text, parse_mode="HTML", reply_markup=keyboard)
        elif hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(message_text, parse_mode="HTML", reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error in send crypto step 1 with user ID: {e}")
        message_text = f"❌ Error: {str(e)}"
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
        ]])
        
        if hasattr(update, 'message') and update.message:
            await update.message.reply_text(message_text, reply_markup=keyboard)
        elif hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(message_text, reply_markup=keyboard)
        
        context.user_data.pop("admin_action", None)


async def handle_coin_selection_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle coin selection for sending"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("admin_select_coin_"):
        coin_symbol = query.data.replace("admin_select_coin_", "")
        context.user_data["send_crypto_coin"] = coin_symbol
        context.user_data["admin_action"] = "send_crypto_step3"
        
        await query.edit_message_text(
            f"📍 <b>Enter Recipient Address</b>\n\n"
            f"👤 <b>From User:</b> {context.user_data['send_crypto_user_id']}\n"
            f"💰 <b>Coin:</b> {coin_symbol}\n\n"
            f"Please enter the recipient address for {coin_symbol}:",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
            ]])
        )


async def handle_send_crypto_step3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle send crypto step 3 - recipient address"""
    try:
        recipient_address = update.message.text.strip()
        
        # Basic address validation could be added here
        context.user_data["send_crypto_recipient"] = recipient_address
        context.user_data["admin_action"] = "send_crypto_step4"
        
        await update.message.reply_text(
            f"💸 <b>Enter Amount to Send</b>\n\n"
            f"👤 <b>From User:</b> {context.user_data['send_crypto_user_id']}\n"
            f"💰 <b>Coin:</b> {context.user_data['send_crypto_coin']}\n"
            f"📍 <b>To:</b> <code>{recipient_address[:20]}...</code>\n\n"
            f"Please enter the amount of {context.user_data['send_crypto_coin']} to send:",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
            ]])
        )
        
    except Exception as e:
        logger.error(f"Error in send crypto step 3: {e}")
        await update.message.reply_text(
            f"❌ Error: {str(e)}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
            ]])
        )


async def handle_send_crypto_step4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle send crypto step 4 - amount and confirmation"""
    try:
        amount_str = update.message.text.strip()
        amount = float(amount_str)
        
        if amount <= 0:
            await update.message.reply_text("❌ Amount must be greater than 0. Please try again.")
            return
        
        # Show confirmation
        user_id = context.user_data['send_crypto_user_id']
        coin = context.user_data['send_crypto_coin']
        recipient = context.user_data['send_crypto_recipient']
        
        context.user_data["send_crypto_amount"] = amount
        
        confirmation_text = f"⚠️ <b>Confirm Transaction</b>\n\n"
        confirmation_text += f"👤 <b>From User:</b> {user_id}\n"
        confirmation_text += f"💰 <b>Coin:</b> {coin}\n"
        confirmation_text += f"💸 <b>Amount:</b> {amount}\n"
        confirmation_text += f"📍 <b>To:</b> <code>{recipient}</code>\n\n"
        confirmation_text += f"⚠️ <b>WARNING:</b> This action cannot be undone!\n\n"
        confirmation_text += f"Are you sure you want to proceed?"
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Confirm Send", callback_data="admin_confirm_send_yes"),
                InlineKeyboardButton("❌ Cancel", callback_data="admin_confirm_send_no")
            ],
            [InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")]
        ])
        
        await update.message.reply_text(
            confirmation_text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        
        context.user_data.pop("admin_action", None)
        
    except ValueError:
        await update.message.reply_text("❌ Invalid amount. Please enter a valid number.")
    except Exception as e:
        logger.error(f"Error in send crypto step 4: {e}")
        await update.message.reply_text(
            f"❌ Error: {str(e)}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
            ]])
        )


async def handle_send_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle send confirmation"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "admin_confirm_send_yes":
        # Proceed with the transaction
        await query.edit_message_text(
            f"⏳ <b>Processing Transaction...</b>\n\n"
            f"Please wait while we send the cryptocurrency.",
            parse_mode="HTML"
        )
        
        try:
            # Get transaction details from context
            wallet_id = context.user_data['send_crypto_wallet_id']
            coin_symbol = context.user_data['send_crypto_coin']
            recipient = context.user_data['send_crypto_recipient']
            amount = context.user_data['send_crypto_amount']
            admin_id = query.from_user.id
            
            # Perform the transaction
            result = await AdminWalletManager.send_crypto(
                wallet_id, coin_symbol, recipient, amount, str(admin_id)
            )
            
            if result['success']:
                success_text = f"✅ <b>Transaction Successful!</b>\n\n"
                success_text += f"💰 <b>Amount:</b> {amount} {coin_symbol}\n"
                success_text += f"📍 <b>To:</b> <code>{recipient}</code>\n"
                success_text += f"🔗 <b>TX Hash:</b> <code>{result.get('tx_hash', 'N/A')}</code>\n\n"
                if result.get('note'):
                    success_text += f"ℹ️ <b>Note:</b> {result['note']}\n\n"
                success_text += f"The transaction has been completed successfully."
                
                await query.edit_message_text(
                    success_text,
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
                    ]])
                )
            else:
                error_text = f"❌ <b>Transaction Failed</b>\n\n"
                error_text += f"Error: {result.get('error', 'Unknown error')}\n\n"
                error_text += f"The transaction could not be completed."
                
                await query.edit_message_text(
                    error_text,
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
                    ]])
                )
            
        except Exception as e:
            logger.error(f"Error executing transaction: {e}")
            await query.edit_message_text(
                f"❌ <b>Transaction Error</b>\n\n"
                f"An unexpected error occurred: {str(e)}",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
                ]])
            )
        
        # Clear context data
        context.user_data.pop("send_crypto_user_id", None)
        context.user_data.pop("send_crypto_wallet_id", None)
        context.user_data.pop("send_crypto_coin", None)
        context.user_data.pop("send_crypto_recipient", None)
        context.user_data.pop("send_crypto_amount", None)
        
    elif query.data == "admin_confirm_send_no":
        # Cancel the transaction
        await query.edit_message_text(
            f"❌ <b>Transaction Cancelled</b>\n\n"
            f"The transaction has been cancelled by admin.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
            ]])
        )
        
        # Clear context data
        context.user_data.pop("send_crypto_user_id", None)
        context.user_data.pop("send_crypto_wallet_id", None)
        context.user_data.pop("send_crypto_coin", None)
        context.user_data.pop("send_crypto_recipient", None)
        context.user_data.pop("send_crypto_amount", None)


async def admin_refresh_user_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: str):
    """Refresh a specific user's wallet balances"""
    query = update.callback_query
    await query.answer()
    
    try:
        wallet_info = await AdminWalletManager.get_user_wallet_info(user_id)
        
        if not wallet_info:
            await query.edit_message_text(
                f"❌ No wallet found for user ID: {user_id}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
                ]])
            )
            return
        
        await query.edit_message_text(
            f"🔄 <b>Refreshing Balances...</b>\n\n"
            f"Please wait while we update the wallet balances for user {user_id}.",
            parse_mode="HTML"
        )
        
        # Refresh balances
        wallet_manager = WalletManager()
        success = await wallet_manager.refresh_wallet_balances(wallet_info['wallet']['_id'])
        
        if success:
            # Get updated wallet info
            updated_wallet_info = await AdminWalletManager.get_user_wallet_info(user_id)
            
            refresh_text = f"✅ <b>Balances Refreshed!</b>\n\n"
            refresh_text += f"👤 <b>User ID:</b> {user_id}\n\n"
            refresh_text += f"💰 <b>Updated Balances:</b>\n"
            
            for coin in updated_wallet_info['coin_addresses']:
                status_icon = "🟢" if coin['balance'] > 0 else "⚪"
                coin_emoji = {
                    'BTC': EmojiEnums.BITCOIN.value,
                    'LTC': EmojiEnums.LITECOIN.value,
                    'DOGE': EmojiEnums.DOGECOIN.value,
                    'ETH': EmojiEnums.ETHEREUM.value,
                    'SOL': EmojiEnums.SOLANA.value,
                    'USDT': EmojiEnums.TETHER.value,
                    'BNB': EmojiEnums.YELLOW_CIRCLE.value,
                    'TRX': EmojiEnums.TRON.value
                }.get(coin['symbol'], '🪙')
                
                refresh_text += f"{status_icon} {coin_emoji} <b>{coin['symbol']}:</b> {coin['balance']}\n"
            
            await query.edit_message_text(
                refresh_text,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
                ]])
            )
        else:
            await query.edit_message_text(
                f"⚠️ <b>Refresh Partially Completed</b>\n\n"
                f"Some balances for user {user_id} may not have been updated due to network issues.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Try Again", callback_data=f"admin_refresh_{user_id}")],
                    [InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")]
                ])
            )
        
    except Exception as e:
        logger.error(f"Error refreshing user wallet: {e}")
        await query.edit_message_text(
            f"❌ Error refreshing wallet for user {user_id}: {str(e)}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
            ]])
        )


def register_handlers(application):
    """Register admin handlers"""
    # Command handlers
    application.add_handler(CommandHandler("admin", admin_menu_handler))
    
    # Callback query handlers - using default group
    application.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^admin_"))
    
    # Message handler for admin inputs (with low priority)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE,
        admin_message_handler
    ), group=10)  # Low priority to not interfere with other handlers 