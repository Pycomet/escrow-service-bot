import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from config import *
from functions import *
from utils import *
from utils.enums import CallbackDataEnums, EmojiEnums

logger = logging.getLogger(__name__)

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
    """Handle rules display"""
    try:
        query = update.callback_query
        await query.answer()

        rules_text = (
            f"{EmojiEnums.SCROLL.value} <b>Escrow Service Rules</b>\n\n"
            "Please read and follow these rules for a safe trading experience:\n\n"
            "1️⃣ <b>Trade Creation</b>\n"
            "• Provide accurate trade details\n"
            "• Set reasonable amounts and timeframes\n"
            "• Use clear descriptions\n"
            "• Specify exact payment methods\n\n"
            "2️⃣ <b>Payment Process</b>\n"
            "• Follow payment instructions exactly\n"
            "• Provide valid payment proofs\n"
            "• Use only supported payment methods\n"
            "• Don't share sensitive information\n\n"
            "3️⃣ <b>Communication</b>\n"
            "• Be respectful and professional\n"
            "• Respond promptly to messages\n"
            "• Keep discussions trade-related\n\n"
            "4️⃣ <b>Dispute Resolution</b>\n"
            "• Provide evidence if disputes arise\n"
            "• Cooperate with moderators\n"
            "• Accept final decisions\n\n"
            "5️⃣ <b>Security Guidelines</b>\n"
            "• Never share login credentials\n"
            "• Use secure payment methods\n"
            "• Report suspicious activities\n"
            "• Keep transaction records\n\n"
            f"{EmojiEnums.WARNING.value} <b>Violations may result in account suspension or trade cancellation.</b>"
        )

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "👥 Community Guidelines", callback_data="community_rules"
                    )
                ],
                [
                    InlineKeyboardButton(
                        f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                        callback_data=CallbackDataEnums.MENU.value,
                    )
                ],
            ]
        )

        await query.edit_message_text(
            rules_text, parse_mode="HTML", reply_markup=keyboard
        )

    except Exception as e:
        logger.error(f"Error displaying rules: {e}")
        await query.edit_message_text(
            f"{EmojiEnums.CROSS_MARK.value} <b>Error</b>\n\n"
            "Failed to load rules. Please try again.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                            callback_data=CallbackDataEnums.MENU.value,
                        )
                    ]
                ]
            ),
        )


async def community_rules_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle community guidelines display"""
    try:
        query = update.callback_query
        await query.answer()

        community_text = (
            "🌐 <b>Join Our Community</b>\n\n"
            "Stay connected with our growing community:\n\n"
            "📢 <b>Official Channels</b>\n"
            "• Announcements: @escrow_announcements\n"
            "• Support Group: @escrow_support\n"
            "• Trading Group: @escrow_trading\n\n"
            f"{EmojiEnums.HANDSHAKE.value} <b>Community Guidelines</b>\n"
            "• Be respectful to others\n"
            "• No spam or advertising\n"
            "• Keep discussions relevant\n"
            "• Follow moderator instructions\n\n"
            "Join us to:\n"
            "• Get trading tips\n"
            "• Find trading partners\n"
            "• Stay updated on features\n"
            "• Get community support"
        )

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        f"{EmojiEnums.SCROLL.value} Trading Rules",
                        callback_data="rules",
                    )
                ],
                [
                    InlineKeyboardButton(
                        f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                        callback_data=CallbackDataEnums.MENU.value,
                    )
                ],
            ]
        )

        await query.edit_message_text(
            community_text, parse_mode="HTML", reply_markup=keyboard
        )

    except Exception as e:
        logger.error(f"Error in community rules handler: {e}")
        await query.edit_message_text(
            f"{EmojiEnums.CROSS_MARK.value} Error loading community information. Please try again.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                            callback_data=CallbackDataEnums.MENU.value,
                        )
                    ]
                ]
            ),
        )


async def community_info_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle community information display"""
    try:
        query = update.callback_query
        await query.answer()

        community_text = (
            f"{EmojiEnums.HANDSHAKE.value} <b>Community Guidelines</b>\n\n"
            "Welcome to our trading community! Please follow these guidelines:\n\n"
            "✅ <b>Do's:</b>\n"
            "• Be honest and transparent\n"
            "• Provide accurate information\n"
            "• Communicate clearly\n"
            "• Report issues promptly\n"
            "• Help newcomers\n"
            "• Follow all rules\n\n"
            f"{EmojiEnums.CROSS_MARK.value} <b>Don'ts:</b>\n"
            "• Attempt fraud or scams\n"
            "• Share false information\n"
            "• Harass other users\n"
            "• Use offensive language\n"
            "• Spam or advertise\n"
            "• Manipulate trades\n\n"
            "💡 <b>Remember:</b> Our community thrives on trust and respect. "
            "Help us maintain a safe trading environment for everyone!"
        )

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        f"{EmojiEnums.SCROLL.value} Trading Rules",
                        callback_data="rules",
                    )
                ],
                [
                    InlineKeyboardButton(
                        f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                        callback_data=CallbackDataEnums.MENU.value,
                    )
                ],
            ]
        )

        await query.edit_message_text(
            community_text, parse_mode="HTML", reply_markup=keyboard
        )

    except Exception as e:
        logger.error(f"Error displaying community info: {e}")
        await query.edit_message_text(
            f"{EmojiEnums.CROSS_MARK.value} An error occurred while displaying community information. Please try again later.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                            callback_data=CallbackDataEnums.MENU.value,
                        )
                    ]
                ]
            ),
        )


def register_handlers(application):
    """Register handlers for the rules module"""
    application.add_handler(CommandHandler("rules", rules_handler))
    application.add_handler(CommandHandler("community", community_rules_handler))
