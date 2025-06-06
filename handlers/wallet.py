from config import *
from utils import *
from functions import *
import logging
import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CallbackQueryHandler
from functions.wallet import WalletManager
from utils.messages import Messages
from utils.keyboard import wallet_menu, back_to_menu, wallet_details_menu
from utils.enums import EmojiEnums, CallbackDataEnums

logger = logging.getLogger(__name__)

async def wallet_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle wallet management main page"""
    try:
        query = update.callback_query
        await query.answer()
        user_id = str(query.from_user.id)
        
        # Get user's wallet
        wallet = WalletManager.get_user_wallet(user_id)
        
        if not wallet:
            # User doesn't have a wallet yet
            await query.edit_message_text(
                f"{EmojiEnums.LOCK.value} <b>Welcome to Wallet Management!</b>\n\n"
                "You don't have a wallet yet. Create one to:\n\n"
                f"{EmojiEnums.BITCOIN.value} Store and manage multiple cryptocurrencies\n"
                f"{EmojiEnums.HANDSHAKE.value} Use for escrow trades (ETH/USDT)\n"
                f"{EmojiEnums.LOCK.value} Keep your funds secure with encryption\n"
                "🪙 All coins in one convenient wallet\n\n"
                "Ready to get started?",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Create My Wallet", callback_data="wallet_create")],
                    [InlineKeyboardButton(f"{EmojiEnums.BACK_ARROW.value} Back to Menu", callback_data=CallbackDataEnums.MENU.value)]
                ])
            )
            return
        
        # Get coin addresses
        coin_addresses = WalletManager.get_wallet_coin_addresses(wallet['_id'])
        
        # Build wallet overview message
        wallet_text = f"{EmojiEnums.LOCK.value} <b>My Wallet Overview</b>\n\n"
        wallet_text += f"💼 <b>Wallet:</b> {wallet['wallet_name']}\n"
        wallet_text += f"🆔 <b>ID:</b> <code>{wallet['_id'][:12]}...</code>\n"
        wallet_text += f"🕐 <b>Created:</b> {wallet['created_at'][:16]}\n\n"
        
        if coin_addresses:
            wallet_text += f"💰 <b>Supported Coins ({len(coin_addresses)}):</b>\n"
            
            # Group coins by balance status
            coins_with_balance = []
            coins_zero_balance = []
            
            for coin_address in coin_addresses:
                coin_symbol = coin_address['coin_symbol']
                balance = float(coin_address.get('balance', 0))
                
                coin_emoji = {
                    'BTC': EmojiEnums.BITCOIN.value,
                    'LTC': EmojiEnums.LITECOIN.value,
                    'DOGE': EmojiEnums.DOGECOIN.value,
                    'ETH': EmojiEnums.ETHEREUM.value,
                    'SOL': EmojiEnums.SOLANA.value,
                    'USDT': EmojiEnums.TETHER.value,
                    'BNB': EmojiEnums.YELLOW_CIRCLE.value,
                    'TRX': EmojiEnums.TRON.value
                }.get(coin_symbol, '🪙')
                
                coin_info = f"{coin_emoji} <b>{coin_symbol}:</b> {balance}"
                
                if balance > 0:
                    coins_with_balance.append(coin_info)
                else:
                    coins_zero_balance.append(coin_info)
            
            # Show coins with balance first
            for coin_info in coins_with_balance:
                wallet_text += f"  {coin_info}\n"
            for coin_info in coins_zero_balance:
                wallet_text += f"  {coin_info}\n"
                
            if not any(float(ca.get('balance', 0)) > 0 for ca in coin_addresses):
                wallet_text += f"\n{EmojiEnums.WARNING.value} <i>All balances are zero. Start by receiving some crypto!</i>"
        else:
            wallet_text += f"{EmojiEnums.WARNING.value} <b>No coin addresses found</b>\n"
            wallet_text += "This shouldn't happen. Please contact support."
        
        keyboard = InlineKeyboardMarkup(wallet_menu().inline_keyboard)
        
        await query.edit_message_text(
            wallet_text,
            parse_mode="HTML",
            reply_markup=keyboard
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
            Messages.wallet_creating(),
            parse_mode="HTML"
        )
        
        # Create wallet
        wallet = WalletManager.create_wallet_for_user(user_id, "My Wallet")
        
        if wallet:
            # Get created coin addresses
            coin_addresses = WalletManager.get_wallet_coin_addresses(wallet['_id'])
            
            success_text = Messages.wallet_created_success(wallet, coin_addresses)
            
            await query.edit_message_text(
                success_text,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📊 View My Wallet", callback_data=CallbackDataEnums.MY_WALLETS.value)],
                    [InlineKeyboardButton(f"{EmojiEnums.BACK_ARROW.value} Back to Menu", callback_data=CallbackDataEnums.MENU.value)]
                ])
            )
        else:
            # Error message
            await query.edit_message_text(
                Messages.wallet_creation_failed(),
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Try Again", callback_data=CallbackDataEnums.WALLET_CREATE.value)],
                    [InlineKeyboardButton(f"{EmojiEnums.BACK_ARROW.value} Back to Menu", callback_data=CallbackDataEnums.MENU.value)]
                ])
            )
        
    except Exception as e:
        logger.error(f"Error creating wallet: {e}")
        await handle_error(update, "wallet creation")

async def wallet_refresh_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle wallet balance refresh with specific wallet ID"""
    try:
        query = update.callback_query
        await query.answer()
        
        # Extract wallet ID from callback data
        wallet_id = query.data.replace("wallet_refresh_", "")
        
        # Show loading message
        await query.edit_message_text(
            Messages.wallet_refreshing(),
            parse_mode="HTML"
        )
        
        # Refresh balances
        wallet_manager = WalletManager()
        success = await wallet_manager.refresh_wallet_balances(wallet_id)
        
        if success:
            await query.edit_message_text(
                Messages.wallet_refreshed_success(),
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📊 View Updated Wallet", callback_data=CallbackDataEnums.MY_WALLETS.value)],
                    [InlineKeyboardButton(f"{EmojiEnums.BACK_ARROW.value} Back to Menu", callback_data=CallbackDataEnums.MENU.value)]
                ])
            )
        else:
            await query.edit_message_text(
                Messages.wallet_refresh_partial(),
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Try Again", callback_data=f"wallet_refresh_{wallet_id}")],
                    [InlineKeyboardButton("📊 View Wallet", callback_data=CallbackDataEnums.MY_WALLETS.value)]
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
                Messages.wallet_not_found(),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(f"{EmojiEnums.BACK_ARROW.value} Back to Wallets", callback_data=CallbackDataEnums.MY_WALLETS.value)
                ]])
            )
            return
        
        # Get coin addresses
        coin_addresses = WalletManager.get_wallet_coin_addresses(wallet_id)
        
        # Format wallet details
        details_text = Messages.wallet_details(wallet, coin_addresses)
        
        keyboard = wallet_details_menu(wallet_id)
        
        await query.edit_message_text(
            details_text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"Error showing wallet details: {e}")
        await handle_error(update, "wallet details")

async def wallet_balances_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle wallet balances view - same as main wallet handler but focused on balances"""
    try:
        query = update.callback_query
        await query.answer()
        user_id = str(query.from_user.id)
        
        # Get user's wallet
        wallet = WalletManager.get_user_wallet(user_id)
        
        if not wallet:
            await query.edit_message_text(
                f"{EmojiEnums.WARNING.value} <b>No Wallet Found</b>\n\n"
                "You need to create a wallet first before viewing balances.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Create Wallet", callback_data=CallbackDataEnums.WALLET_CREATE.value)],
                    [InlineKeyboardButton(f"{EmojiEnums.BACK_ARROW.value} Back to Menu", callback_data=CallbackDataEnums.MENU.value)]
                ])
            )
            return
        
        # Get coin addresses
        coin_addresses = WalletManager.get_wallet_coin_addresses(wallet['_id'])
        
        # Build detailed balance message
        balance_text = f"📊 <b>Wallet Balance Overview</b>\n\n"
        balance_text += f"💼 <b>Wallet:</b> {wallet['wallet_name']}\n"
        balance_text += f"🆔 <b>ID:</b> <code>{wallet['_id'][:12]}...</code>\n\n"
        
        if coin_addresses:
            total_value = 0
            balance_text += f"💰 <b>Your Balances:</b>\n\n"
            
            for coin_address in coin_addresses:
                coin_symbol = coin_address['coin_symbol']
                balance = float(coin_address.get('balance', 0))
                
                coin_emoji = {
                    'BTC': EmojiEnums.BITCOIN.value,
                    'LTC': EmojiEnums.LITECOIN.value,
                    'DOGE': EmojiEnums.DOGECOIN.value,
                    'ETH': EmojiEnums.ETHEREUM.value,
                    'SOL': EmojiEnums.SOLANA.value,
                    'USDT': EmojiEnums.TETHER.value,
                    'BNB': EmojiEnums.YELLOW_CIRCLE.value,
                    'TRX': EmojiEnums.TRON.value
                }.get(coin_symbol, '🪙')
                
                status_icon = "🟢" if balance > 0 else "⚪"
                balance_text += f"{status_icon} {coin_emoji} <b>{coin_symbol}:</b> {balance}\n"
                
                if balance > 0:
                    total_value += 1  # Just count non-zero balances for now
            
            balance_text += f"\n📈 <b>Summary:</b>\n"
            balance_text += f"• Total coins: {len(coin_addresses)}\n"
            balance_text += f"• With balance: {total_value}\n"
            balance_text += f"• Last updated: Just now\n"
            
        else:
            balance_text += f"{EmojiEnums.WARNING.value} No coin addresses found."
        
        await query.edit_message_text(
            balance_text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(f"{EmojiEnums.REFRESH.value} Refresh Now", callback_data=f"wallet_refresh_{wallet['_id']}"),
                    InlineKeyboardButton("📋 Details", callback_data=f"wallet_details_{wallet['_id']}")
                ],
                [InlineKeyboardButton(f"{EmojiEnums.BACK_ARROW.value} Back to Wallet", callback_data=CallbackDataEnums.MY_WALLETS.value)]
            ])
        )
        
    except Exception as e:
        logger.error(f"Error in wallet balances handler: {e}")
        await handle_error(update, "wallet balance view")

async def wallet_refresh_general_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle general wallet refresh (without specific wallet ID)"""
    try:
        query = update.callback_query
        await query.answer()
        user_id = str(query.from_user.id)
        
        # Get user's wallet
        wallet = WalletManager.get_user_wallet(user_id)
        
        if not wallet:
            await query.edit_message_text(
                f"{EmojiEnums.WARNING.value} <b>No Wallet Found</b>\n\n"
                "You need to create a wallet first before refreshing balances.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Create Wallet", callback_data=CallbackDataEnums.WALLET_CREATE.value)],
                    [InlineKeyboardButton(f"{EmojiEnums.BACK_ARROW.value} Back to Menu", callback_data=CallbackDataEnums.MENU.value)]
                ])
            )
            return
        
        # Show loading message
        await query.edit_message_text(
            Messages.wallet_refreshing(),
            parse_mode="HTML"
        )
        
        # Refresh balances
        wallet_manager = WalletManager()
        success = await wallet_manager.refresh_wallet_balances(wallet['_id'])
        
        if success:
            await query.edit_message_text(
                Messages.wallet_refreshed_success(),
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📊 View Balances", callback_data=CallbackDataEnums.WALLET_BALANCES.value)],
                    [InlineKeyboardButton(f"{EmojiEnums.BACK_ARROW.value} Back to Wallet", callback_data=CallbackDataEnums.MY_WALLETS.value)]
                ])
            )
        else:
            await query.edit_message_text(
                Messages.wallet_refresh_partial(),
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Try Again", callback_data=CallbackDataEnums.WALLET_REFRESH.value)],
                    [InlineKeyboardButton("📊 View Wallet", callback_data=CallbackDataEnums.MY_WALLETS.value)]
                ])
            )
        
    except Exception as e:
        logger.error(f"Error refreshing wallet (general): {e}")
        await handle_error(update, "wallet refresh")

async def wallet_transactions_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle wallet transaction history view"""
    try:
        query = update.callback_query
        await query.answer()
        user_id = str(query.from_user.id)
        
        # Get user's wallet
        wallet = WalletManager.get_user_wallet(user_id)
        
        if not wallet:
            await query.edit_message_text(
                f"{EmojiEnums.WARNING.value} <b>No Wallet Found</b>\n\n"
                "You need to create a wallet first before viewing transaction history.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Create Wallet", callback_data=CallbackDataEnums.WALLET_CREATE.value)],
                    [InlineKeyboardButton(f"{EmojiEnums.BACK_ARROW.value} Back to Menu", callback_data=CallbackDataEnums.MENU.value)]
                ])
            )
            return
        
        # For now, show a placeholder since transaction history isn't fully implemented
        transactions_text = f"📜 <b>Transaction History</b>\n\n"
        transactions_text += f"💼 <b>Wallet:</b> {wallet['wallet_name']}\n"
        transactions_text += f"🆔 <b>ID:</b> <code>{wallet['_id'][:12]}...</code>\n\n"
        transactions_text += f"📊 <b>Transaction History:</b>\n\n"
        transactions_text += f"🔍 <i>No transactions found yet.</i>\n\n"
        transactions_text += f"💡 <b>Note:</b> Transaction history will appear here when you:\n"
        transactions_text += f"• Receive cryptocurrency\n"
        transactions_text += f"• Send cryptocurrency\n"
        transactions_text += f"• Use wallet for escrow trades\n\n"
        transactions_text += f"Start by receiving some crypto to your wallet addresses!"
        
        await query.edit_message_text(
            transactions_text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📊 View Balances", callback_data=CallbackDataEnums.WALLET_BALANCES.value),
                    InlineKeyboardButton(f"{EmojiEnums.REFRESH.value} Refresh", callback_data=CallbackDataEnums.WALLET_REFRESH.value)
                ],
                [InlineKeyboardButton(f"{EmojiEnums.BACK_ARROW.value} Back to Wallet", callback_data=CallbackDataEnums.MY_WALLETS.value)]
            ])
        )
        
    except Exception as e:
        logger.error(f"Error in wallet transactions handler: {e}")
        await handle_error(update, "wallet transaction history")

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
        
        await send_message_or_edit(
            message, 
            f"{EmojiEnums.CROSS_MARK.value} <b>Error in {operation}</b>\n\n"
            "Something went wrong. Please try again or contact support if the problem persists.",
            back_to_menu(),
            is_callback=bool(update.callback_query),
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Error in error handler: {e}") 