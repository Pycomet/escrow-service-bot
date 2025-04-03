from config import *
from utils import *
from functions import *
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler


async def join_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /join command"""
    await update.message.reply_text(
        "🔍 Please enter the Trade ID you want to join:",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
        ]])
    )
    
    # Set state to wait for trade ID
    context.user_data["waiting_for_trade_id"] = True


async def handle_trade_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the trade ID input"""
    if not context.user_data.get("waiting_for_trade_id"):
        return
    
    trade_id = update.message.text
    user_id = update.effective_user.id
    
    # Clear state
    context.user_data.pop("waiting_for_trade_id", None)
    
    # Get trade details
    trade = get_trade_by_id(trade_id)
    if not trade:
        await update.message.reply_text(
            "❌ Trade not found. Please check the ID and try again.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
            ]])
        )
        return
    
    # Check if trade is available for joining
    if trade["status"] != "pending":
        await update.message.reply_text(
            f"❌ This trade is no longer available for joining (Status: {trade['status']}).",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
            ]])
        )
        return
    
    # Check if user is already involved in the trade
    if trade["seller_id"] == user_id or trade["buyer_id"] == user_id:
        await update.message.reply_text(
            "❌ You are already involved in this trade.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
            ]])
        )
        return
    
    # Store trade ID in context for later use
    context.user_data["join_trade_id"] = trade_id
    
    # Show trade details and confirmation
    details = (
        f"📋 <b>Trade Details</b>\n\n"
        f"ID: <code>{trade['_id']}</code>\n"
        f"Amount: {trade['amount']} {trade['currency']}\n"
        f"Created: {trade['created_at']}\n\n"
    )
    
    if trade.get("description"):
        details += f"Description: {trade['description']}\n\n"
    
    details += "Would you like to join this trade as a buyer?"
    
    await update.message.reply_text(
        details,
        parse_mode="html",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Yes, Join Trade", callback_data=f"confirm_join_{trade_id}")],
            [InlineKeyboardButton("❌ No, Cancel", callback_data="menu")]
        ])
    )


async def handle_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle join-related callback queries"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("confirm_join_"):
        trade_id = data.replace("confirm_join_", "")
        user_id = query.from_user.id
        
        # Join the trade
        if join_trade(trade_id, user_id):
            # Notify seller
            trade = get_trade_by_id(trade_id)
            await context.bot.send_message(
                chat_id=trade["seller_id"],
                text=f"✅ A new buyer has joined your trade #{trade_id}.",
                parse_mode="html"
            )
            
            # Confirm to buyer
            await query.edit_message_text(
                f"✅ You have successfully joined trade #{trade_id}.\n\n"
                "Please proceed with the payment to complete the trade.",
                parse_mode="html",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("💳 Make Payment", callback_data=f"pay_{trade_id}"),
                    InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
                ]])
            )
        else:
            await query.edit_message_text(
                "❌ Failed to join trade. Please try again later.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
                ]])
            )


def register_handlers(application):
    """Register handlers for the join module"""
    application.add_handler(CommandHandler("join", join_handler))
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE,
        handle_trade_id
    ))
    application.add_handler(CallbackQueryHandler(handle_join_callback, pattern="^confirm_join_"))
