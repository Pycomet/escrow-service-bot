from config import *
from utils import *
from functions import *
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters


async def report_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /report command"""
    user_id = update.effective_user.id
    
    # Check if user is in a trade
    trade = trades_db.get_active_trade_by_user_id(user_id)
    if not trade:
        await update.message.reply_text(
            "❌ You are not currently involved in any active trade. Please start a trade first.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
            ]])
        )
        return
    
    # Store trade ID in context for later use
    context.user_data["report_trade_id"] = trade["_id"]
    
    await update.message.reply_text(
        "Please describe the issue you're experiencing with this trade. "
        "Include as many details as possible to help us understand the situation.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Cancel", callback_data="menu")
        ]])
    )
    
    # Set state to wait for report description
    context.user_data["waiting_for_report"] = True


async def handle_report_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the report description from the user"""
    if not context.user_data.get("waiting_for_report"):
        return
    
    user_id = update.effective_user.id
    trade_id = context.user_data.get("report_trade_id")
    description = update.message.text
    
    # Save report to database
    save_report(user_id, trade_id, description)
    
    # Notify admin
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"⚠️ New report received for trade <b>({trade_id})</b>\n\n"
             f"From user: {user_id}\n"
             f"Description: {description}",
        parse_mode="html"
    )
    
    # Clear state
    context.user_data.pop("waiting_for_report", None)
    context.user_data.pop("report_trade_id", None)
    
    # Confirm to user
    await update.message.reply_text(
        "✅ Your report has been submitted. Our team will review it and get back to you soon.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
        ]])
    )


def register_handlers(application):
    """Register handlers for the report module"""
    application.add_handler(CommandHandler("report", report_handler))
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE,
        handle_report_description
    ))
