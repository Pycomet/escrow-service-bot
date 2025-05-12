from config import *
from utils import *
from functions import *
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from functions.trade import TradeClient


async def delete_trade_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /delete_trade command"""
    user_id = str(update.effective_user.id)
    
    # Get user's active trades
    active_trade = TradeClient.get_active_trade_by_user_id(user_id)
    if not active_trade:
        await update.message.reply_text(
            "❌ You don't have any active trades to delete.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
            ]])
        )
        return
    
    # Create keyboard with trade option
    keyboard = [[
        InlineKeyboardButton(
            f"Trade #{active_trade['_id']} - {active_trade['price']} {active_trade['currency']}",
            callback_data=f"delete_trade_{active_trade['_id']}"
        )
    ]]
    
    keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")])
    
    await update.message.reply_text(
        "🗑 Select a trade to delete:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_delete_trade_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle delete trade callback queries"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("delete_trade_"):
        trade_id = data.replace("delete_trade_", "")
        trade = get_trade_by_id(trade_id)
        
        if not trade:
            await query.edit_message_text(
                "❌ Trade not found. Please try again.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
                ]])
            )
            return
        
        # Check if user is authorized to delete this trade
        if trade["seller_id"] != query.from_user.id and trade["buyer_id"] != query.from_user.id:
            await query.edit_message_text(
                "❌ You are not authorized to delete this trade.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
                ]])
            )
            return
        
        # Confirm deletion
        await query.edit_message_text(
            f"⚠️ Are you sure you want to delete Trade #{trade_id}?\n\n"
            f"This action cannot be undone.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Yes, Delete", callback_data=f"confirm_delete_{trade_id}")],
                [InlineKeyboardButton("❌ No, Cancel", callback_data="menu")]
            ])
        )
    
    elif data.startswith("confirm_delete_"):
        trade_id = data.replace("confirm_delete_", "")
        
        # Delete the trade
        if delete_trade(trade_id):
            await query.edit_message_text(
                f"✅ Trade #{trade_id} has been successfully deleted.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
                ]])
            )
        else:
            await query.edit_message_text(
                "❌ Failed to delete trade. Please try again later.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
                ]])
            )


def register_handlers(application):
    """Register handlers for the delete trade module"""
    application.add_handler(CommandHandler("delete_trade", delete_trade_handler))
    application.add_handler(CallbackQueryHandler(handle_delete_trade_callback, pattern="^(delete_trade_|confirm_delete_)"))
