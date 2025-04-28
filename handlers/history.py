from config import *
from utils import *
from functions import *
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler
import logging

logger = logging.getLogger(__name__)

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

async def history_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /history command"""
    try:
        user_id = update.effective_user.id
        is_callback = bool(update.callback_query)
        message = update.callback_query.message if is_callback else update.message
        
        if is_callback:
            await update.callback_query.answer()
        
        logger.info(f"User ID: {user_id}")
        
        # Get user's trades
        trades = trades_db.get_trades(user_id)
        if not trades:
            await send_message_or_edit(
                message,
                "❌ You don't have any trade history yet.",
                InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
                ]]),
                is_callback
            )
            return
        
        # Create keyboard with trade options
        keyboard = []
        # Convert trades to list if it's not already
        trades_list = list(trades) if not isinstance(trades, list) else trades
        logger.info(f"Trades: {trades_list}")
        
        for trade in trades_list[:5]:  # Limit to 5 most recent trades
            logger.info(trade)
            try:
                # Handle both dictionary and list formats
                if isinstance(trade, dict):
                    trade_id = str(trade.get('_id', ''))
                    amount = str(trade.get('amount', '0'))
                    currency = str(trade.get('currency', 'Unknown'))
                    status = str(trade.get('status', 'unknown')).lower()
                else:
                    # Assuming trade is a list with ordered values
                    trade_id = str(trade[0]) if len(trade) > 0 else ''
                    amount = str(trade[1]) if len(trade) > 1 else '0'
                    currency = str(trade[2]) if len(trade) > 2 else 'Unknown'
                    status = str(trade[3]).lower() if len(trade) > 3 else 'unknown'
                
                status_emoji = {
                    "pending": "⏳",
                    "completed": "✅",
                    "disputed": "⚠️",
                    "cancelled": "❌"
                }.get(status, "❓")
                
                keyboard.append([
                    InlineKeyboardButton(
                        f"{status_emoji} Trade #{trade_id} - {amount} {currency}",
                        callback_data=f"view_trade_{trade_id}"
                    )
                ])
            except Exception as e:
                logger.error(f"Error processing trade in history: {e}")
                continue
        
        keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")])
        
        await send_message_or_edit(
            message,
            "📋 Your Trade History:\n\nSelect a trade to view details:",
            InlineKeyboardMarkup(keyboard),
            is_callback
        )
            
    except Exception as e:
        logger.error(f"Error in history handler: {e}")
        # Try to send error message
        try:
            message = update.callback_query.message if update.callback_query else update.message
            if message:
                await send_message_or_edit(
                    message,
                    "❌ An error occurred while fetching your trade history. Please try again later.",
                    InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
                    ]]),
                    bool(update.callback_query)
                )
        except Exception as e2:
            logger.error(f"Error sending error message: {e2}")


async def handle_trade_view_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle trade view callback queries"""
    try:
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data.startswith("view_trade_"):
            trade_id = data.replace("view_trade_", "")
            logger.info(f"Trade ID: {trade_id}")
            trade = trades_db.get_trade(trade_id)
            
            if not trade:
                await query.message.edit_text(
                    "❌ Trade not found. Please try again.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
                    ]])
                )
                return
            
            # Format trade details
            status = str(trade.get('status', 'unknown')).lower()
            status_emoji = {
                "pending": "⏳",
                "completed": "✅",
                "disputed": "⚠️",
                "cancelled": "❌"
            }.get(status, "❓")
            
            details = (
                f"📋 <b>Trade Details</b>\n\n"
                f"ID: <code>{trade.get('_id', 'Unknown')}</code>\n"
                f"Status: {status_emoji} {status.title()}\n"
                f"Amount: {trade.get('amount', '0')} {trade.get('currency', 'Unknown')}\n"
                f"Created: {trade.get('created_at', 'Unknown')}\n"
                f"Updated: {trade.get('updated_at', 'Unknown')}\n\n"
            )
            
            if trade.get("description"):
                details += f"Description: {trade['description']}\n\n"
            
            # Add action buttons based on trade status
            keyboard = [[InlineKeyboardButton("🔙 Back to History", callback_data="history")]]
            
            if status == "pending":
                if str(trade.get("seller_id")) == str(query.from_user.id):
                    keyboard.append([InlineKeyboardButton("❌ Cancel Trade", callback_data=f"delete_trade_{trade_id}")])
                elif str(trade.get("buyer_id")) == str(query.from_user.id):
                    keyboard.append([InlineKeyboardButton("⚠️ Report Issue", callback_data=f"report_trade_{trade_id}")])
            
            await query.message.edit_text(
                details,
                parse_mode="html",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        elif data == "history":
            # Return to history menu
            await history_handler(update, context)
            
    except Exception as e:
        logger.error(f"Error in trade view callback: {e}")
        try:
            if query and query.message:
                await query.message.edit_text(
                    "❌ An error occurred while viewing trade details. Please try again later.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
                    ]])
                )
        except Exception as e2:
            logger.error(f"Error sending error message: {e2}")


def register_handlers(application):
    """Register handlers for the history module"""
    application.add_handler(CommandHandler("history", history_handler))
    application.add_handler(CallbackQueryHandler(handle_trade_view_callback, pattern="^(view_trade_|history)"))
