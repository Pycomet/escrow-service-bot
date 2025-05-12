from config import *
from utils import *
from functions import *
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler

RULES_TEXT = """
📜 <b>Escrow Service Rules</b>

1️⃣ <b>General Rules</b>
• All trades must be conducted through the bot
• Be respectful to other users
• No fraudulent activities
• Keep communication clear and professional

2️⃣ <b>Trade Rules</b>
• Verify trade details before confirming
• Only join trades you can complete
• Follow payment instructions carefully
• Report any issues immediately

3️⃣ <b>Payment Rules</b>
• Use only supported payment methods
• Never share payment details in chat
• Wait for confirmation before releasing funds
• Keep payment receipts

4️⃣ <b>Dispute Resolution</b>
• Report disputes within 24 hours
• Provide evidence when requested
• Follow moderator instructions
• Accept final decisions

5️⃣ <b>Security</b>
• Never share your private keys
• Use secure payment methods
• Report suspicious activity
• Enable 2FA when available

❗️ Violation of these rules may result in account suspension.
"""

async def rules_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /rules command"""
    try:
        # Check if this is from a callback query or direct command
        if update.callback_query:
            query = update.callback_query
            await query.answer()
            await query.edit_message_text(
                RULES_TEXT,
                parse_mode="html",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
                ]])
            )
        else:
            await update.message.reply_text(
                RULES_TEXT,
                parse_mode="html",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
                ]])
            )
    except Exception as e:
        logger.error(f"Error in rules handler: {e}")
        # Determine which message object to use
        message = update.callback_query.message if update.callback_query else update.message
        if message:
            await message.reply_text(
                "❌ An error occurred while displaying the rules. Please try again later.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
                ]])
            )


async def community_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /community command"""
    try:
        community_text = """
🌐 <b>Join Our Community</b>

Stay connected with our growing community:

📢 <b>Official Channels</b>
• Announcements: @escrow_announcements
• Support Group: @escrow_support
• Trading Group: @escrow_trading

🤝 <b>Community Guidelines</b>
• Be respectful to others
• No spam or advertising
• Keep discussions relevant
• Follow moderator instructions

Join us to:
• Get trading tips
• Find trading partners
• Stay updated on features
• Get community support
"""
        # Check if this is from a callback query or direct command
        if update.callback_query:
            query = update.callback_query
            await query.answer()
            await query.edit_message_text(
                community_text,
                parse_mode="html",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
                ]])
            )
        else:
            await update.message.reply_text(
                community_text,
                parse_mode="html",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
                ]])
            )
    except Exception as e:
        logger.error(f"Error in community handler: {e}")
        # Determine which message object to use
        message = update.callback_query.message if update.callback_query else update.message
        if message:
            await message.reply_text(
                "❌ An error occurred while displaying community information. Please try again later.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
                ]])
            )


def register_handlers(application):
    """Register handlers for the rules module"""
    application.add_handler(CommandHandler("rules", rules_handler))
    application.add_handler(CommandHandler("community", community_handler))
