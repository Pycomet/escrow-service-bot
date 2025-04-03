from config import *
from utils import *
from functions import *
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler


async def history_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /history command"""
    user_id = update.effective_user.id
    
    # Get user's trades
    trades = get_trades_by_user_id(user_id)
    if not trades:
        await update.message.reply_text(
            "❌ You don't have any trade history yet.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
            ]])
        )
        return
    
    # Create keyboard with trade options
    keyboard = []
    for trade in trades[:5]:  # Limit to 5 most recent trades
        status_emoji = {
            "pending": "⏳",
            "completed": "✅",
            "disputed": "⚠️",
            "cancelled": "❌"
        }.get(trade["status"], "❓")
        
        keyboard.append([
            InlineKeyboardButton(
                f"{status_emoji} Trade #{trade['_id']} - {trade['amount']} {trade['currency']}",
                callback_data=f"view_trade_{trade['_id']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")])
    
    await update.message.reply_text(
        "📋 Your Trade History:\n\n"
        "Select a trade to view details:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_trade_view_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle trade view callback queries"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("view_trade_"):
        trade_id = data.replace("view_trade_", "")
        trade = get_trade_by_id(trade_id)
        
        if not trade:
            await query.edit_message_text(
                "❌ Trade not found. Please try again.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
                ]])
            )
            return
        
        # Format trade details
        status_emoji = {
            "pending": "⏳",
            "completed": "✅",
            "disputed": "⚠️",
            "cancelled": "❌"
        }.get(trade["status"], "❓")
        
        details = (
            f"📋 <b>Trade Details</b>\n\n"
            f"ID: <code>{trade['_id']}</code>\n"
            f"Status: {status_emoji} {trade['status'].title()}\n"
            f"Amount: {trade['amount']} {trade['currency']}\n"
            f"Created: {trade['created_at']}\n"
            f"Updated: {trade['updated_at']}\n\n"
        )
        
        if trade.get("description"):
            details += f"Description: {trade['description']}\n\n"
        
        # Add action buttons based on trade status
        keyboard = [[InlineKeyboardButton("🔙 Back to History", callback_data="history")]]
        
        if trade["status"] == "pending":
            if trade["seller_id"] == query.from_user.id:
                keyboard.append([InlineKeyboardButton("❌ Cancel Trade", callback_data=f"delete_trade_{trade_id}")])
            elif trade["buyer_id"] == query.from_user.id:
                keyboard.append([InlineKeyboardButton("⚠️ Report Issue", callback_data=f"report_trade_{trade_id}")])
        
        await query.edit_message_text(
            details,
            parse_mode="html",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif data == "history":
        # Return to history menu
        await history_handler(update, context)


def register_handlers(application):
    """Register handlers for the history module"""
    application.add_handler(CommandHandler("history", history_handler))
    application.add_handler(CallbackQueryHandler(handle_trade_view_callback, pattern="^(view_trade_|history)"))
