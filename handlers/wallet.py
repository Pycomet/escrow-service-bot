from config import *
from utils import *
from functions import *
from functions.wallet import WalletManager
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler
import logging
import asyncio

logger = logging.getLogger(__name__)

async def wallet_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle wallet-related commands and callbacks"""
    try:
        is_callback = bool(update.callback_query)
        message = update.callback_query.message if is_callback else update.message
        user_id = str(update.effective_user.id)
        
        if is_callback:
            await update.callback_query.answer()
        
        # Get user's wallet
        user_wallet = WalletManager.get_user_wallet(user_id)
        
        if not user_wallet:
            # No wallet found - offer to create one
            await send_message_or_edit(
                message,
                "🔐 <b>My Wallet</b>\n\n"
                "You don't have a wallet yet. Create your first wallet to get started!\n\n"
                "Your wallet will include addresses for:\n"
                "• Bitcoin (BTC)\n"
                "• Litecoin (LTC)\n"
                "• Dogecoin (DOGE)\n"
                "• Ethereum (ETH)\n"
                "• Solana (SOL)\n"
                "• Tether USDT (ERC-20)\n\n"
                "🔐 All private keys will be encrypted and stored securely.",
                InlineKeyboardMarkup([
                    [InlineKeyboardButton("🆕 Create My Wallet", callback_data="wallet_create")],
                    [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]
                ]),
                is_callback,
                parse_mode="HTML"
            )
            return
        
        # Get coin addresses for the wallet
        coin_addresses = WalletManager.get_wallet_coin_addresses(user_wallet['_id'])
        
        # Show wallet overview
        wallet_text = f"🔐 <b>My Wallet</b>\n\n"
        wallet_text += f"💼 <b>Wallet Name:</b> {user_wallet['wallet_name']}\n"
        wallet_text += f"🆔 <b>Wallet ID:</b> <code>{user_wallet['_id']}</code>\n"
        wallet_text += f"🕐 <b>Created:</b> {user_wallet['created_at'][:10]}\n\n"
        
        if coin_addresses:
            wallet_text += "💰 <b>Your Coin Addresses:</b>\n\n"
            for coin_address in coin_addresses:
                coin_symbol = coin_address['coin_symbol']
                address = coin_address['address']
                balance = coin_address.get('balance', '0')
                
                # Truncate address for display
                display_address = f"{address[:8]}...{address[-6:]}"
                
                # Add coin emoji
                coin_emoji = {
                    'BTC': '₿', 'LTC': 'Ł', 'DOGE': 'Ð', 'ETH': 'Ξ', 
                    'SOL': '◎', 'USDT': '₮', 'BNB': '🟡', 'TRX': 'ⓣ'
                }.get(coin_symbol, '🪙')
                
                wallet_text += f"{coin_emoji} <b>{coin_symbol}</b>\n"
                wallet_text += f"   📍 <code>{display_address}</code>\n"
                wallet_text += f"   💰 {balance} {coin_symbol}\n\n"
        else:
            wallet_text += "❌ No coin addresses found. Please contact support.\n\n"
        
        # Create keyboard with wallet options
        keyboard = [
            [
                InlineKeyboardButton("🔄 Refresh Balances", callback_data=f"wallet_refresh_{user_wallet['_id']}"),
                InlineKeyboardButton("📊 Detailed View", callback_data=f"wallet_details_{user_wallet['_id']}")
            ],
            [
                InlineKeyboardButton("📜 Transaction History", callback_data=f"wallet_transactions_{user_wallet['_id']}"),
                InlineKeyboardButton("💸 Send Crypto", callback_data=f"wallet_send_{user_wallet['_id']}")
            ],
            [
                InlineKeyboardButton("➕ Add Coin", callback_data=f"wallet_add_coin_{user_wallet['_id']}"),
                InlineKeyboardButton("⚙️ Settings", callback_data=f"wallet_settings_{user_wallet['_id']}")
            ],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]
        ]
        
        await send_message_or_edit(
            message,
            wallet_text,
            InlineKeyboardMarkup(keyboard),
            is_callback,
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Error in wallet handler: {e}")
        await handle_error(update, "wallet management")

async def wallet_create_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle wallet creation"""
    try:
        query = update.callback_query
        await query.answer()
        user_id = str(query.from_user.id)
        
        # Show loading message
        await query.edit_message_text(
            "⏳ <b>Creating Your Multi-Currency Wallet</b>\n\n"
            "Please wait while we set up your secure wallet...\n\n"
            "🔐 Generating master mnemonic phrase\n"
            "🪙 Creating addresses for default coins\n"
            "🛡️ Encrypting all private data\n"
            "💾 Saving to secure database",
            parse_mode="HTML"
        )
        
        # Create wallet
        wallet = WalletManager.create_wallet_for_user(user_id, "My Wallet")
        
        if wallet:
            # Get created coin addresses
            coin_addresses = WalletManager.get_wallet_coin_addresses(wallet['_id'])
            
            success_text = (
                f"✅ <b>Wallet Created Successfully!</b>\n\n"
                f"💼 <b>Wallet Name:</b> {wallet['wallet_name']}\n"
                f"🆔 <b>Wallet ID:</b> <code>{wallet['_id']}</code>\n\n"
                f"🪙 <b>Created {len(coin_addresses)} coin addresses:</b>\n"
            )
            
            for coin_address in coin_addresses[:6]:  # Show first 6
                coin_symbol = coin_address['coin_symbol']
                address = coin_address['address']
                display_address = f"{address[:10]}...{address[-6:]}"
                success_text += f"• {coin_symbol}: <code>{display_address}</code>\n"
            
            success_text += (
                f"\n🔐 <b>Security Features:</b>\n"
                f"• All private keys encrypted with AES-256\n"
                f"• Master mnemonic securely stored\n"
                f"• One wallet, multiple currencies\n\n"
                f"⚠️ <b>Important:</b> Keep your account secure!"
            )
            
            await query.edit_message_text(
                success_text,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📊 View My Wallet", callback_data="my_wallets")],
                    [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]
                ])
            )
        else:
            # Error message
            await query.edit_message_text(
                "❌ <b>Failed to Create Wallet</b>\n\n"
                "An error occurred while creating your wallet. "
                "Please try again or contact support if the problem persists.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Try Again", callback_data="wallet_create")],
                    [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]
                ])
            )
        
    except Exception as e:
        logger.error(f"Error creating wallet: {e}")
        await handle_error(update, "wallet creation")

async def wallet_refresh_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle wallet balance refresh"""
    try:
        query = update.callback_query
        await query.answer()
        
        # Extract wallet ID from callback data
        wallet_id = query.data.replace("wallet_refresh_", "")
        
        # Show loading message
        await query.edit_message_text(
            "🔄 <b>Refreshing Wallet Balances</b>\n\n"
            "Please wait while we fetch the latest balance information from the blockchain...",
            parse_mode="HTML"
        )
        
        # Refresh balances
        wallet_manager = WalletManager()
        success = await wallet_manager.refresh_wallet_balances(wallet_id)
        
        if success:
            await query.edit_message_text(
                "✅ <b>Balances Refreshed!</b>\n\n"
                "Your wallet balances have been updated with the latest information from the blockchain.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📊 View Updated Wallet", callback_data="my_wallets")],
                    [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]
                ])
            )
        else:
            await query.edit_message_text(
                "⚠️ <b>Refresh Partially Complete</b>\n\n"
                "Some balances may not have been updated due to network issues. "
                "You can try refreshing again in a moment.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Try Again", callback_data=f"wallet_refresh_{wallet_id}")],
                    [InlineKeyboardButton("📊 View Wallet", callback_data="my_wallets")]
                ])
            )
        
    except Exception as e:
        logger.error(f"Error refreshing wallet: {e}")
        await handle_error(update, "wallet refresh")

async def wallet_details_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle wallet details view"""
    try:
        query = update.callback_query
        await query.answer()
        
        # Extract wallet ID from callback data
        wallet_id = query.data.replace("wallet_details_", "")
        user_id = str(query.from_user.id)
        
        # Get wallet
        wallet = WalletManager.get_user_wallet(user_id)
        if not wallet or wallet['_id'] != wallet_id:
            await query.edit_message_text(
                "❌ Wallet not found or access denied.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Wallets", callback_data="my_wallets")
                ]])
            )
            return
        
        # Get coin addresses
        coin_addresses = WalletManager.get_wallet_coin_addresses(wallet_id)
        
        # Format wallet details
        details_text = f"📊 <b>Wallet Details</b>\n\n"
        details_text += f"💼 <b>Name:</b> {wallet['wallet_name']}\n"
        details_text += f"🆔 <b>ID:</b> <code>{wallet['_id']}</code>\n"
        details_text += f"👤 <b>Owner:</b> {wallet['user_id']}\n"
        details_text += f"🕐 <b>Created:</b> {wallet['created_at'][:16]}\n\n"
        
        if coin_addresses:
            details_text += f"💰 <b>Coin Addresses ({len(coin_addresses)}):</b>\n\n"
            for coin_address in coin_addresses:
                coin_symbol = coin_address['coin_symbol']
                address = coin_address['address']
                balance = coin_address.get('balance', '0')
                
                coin_emoji = {
                    'BTC': '₿', 'LTC': 'Ł', 'DOGE': 'Ð', 'ETH': 'Ξ', 
                    'SOL': '◎', 'USDT': '₮', 'BNB': '🟡', 'TRX': 'ⓣ'
                }.get(coin_symbol, '🪙')
                
                details_text += f"{coin_emoji} <b>{coin_symbol}</b>\n"
                details_text += f"   💰 Balance: {balance}\n"
                details_text += f"   📍 <code>{address}</code>\n\n"
        
        keyboard = [
            [
                InlineKeyboardButton("🔄 Refresh", callback_data=f"wallet_refresh_{wallet_id}"),
                InlineKeyboardButton("📋 Copy Address", callback_data=f"wallet_copy_{wallet_id}")
            ],
            [InlineKeyboardButton("🔙 Back to Wallet", callback_data="my_wallets")]
        ]
        
        await query.edit_message_text(
            details_text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except Exception as e:
        logger.error(f"Error showing wallet details: {e}")
        await handle_error(update, "wallet details")

async def send_message_or_edit(message, text, reply_markup, is_callback=False, parse_mode=None):
    """Helper function to either send a new message or edit existing one"""
    try:
        if is_callback:
            return await message.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
        else:
            return await message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception as e:
        logger.error(f"Error in send_message_or_edit: {e}")
        raise

async def handle_error(update: Update, operation: str):
    """Handle errors gracefully"""
    try:
        message = update.callback_query.message if update.callback_query else update.message
        if message:
            await send_message_or_edit(
                message,
                f"❌ An error occurred during {operation}. Please try again later.",
                InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
                ]]),
                bool(update.callback_query)
            )
    except Exception as e:
        logger.error(f"Error sending error message: {e}")

def register_handlers(application):
    """Register handlers for the wallet module"""
    application.add_handler(CallbackQueryHandler(wallet_handler, pattern="^my_wallets$"))
    application.add_handler(CallbackQueryHandler(wallet_create_handler, pattern="^wallet_create$"))
    application.add_handler(CallbackQueryHandler(wallet_refresh_handler, pattern="^wallet_refresh_"))
    application.add_handler(CallbackQueryHandler(wallet_details_handler, pattern="^wallet_details_")) 