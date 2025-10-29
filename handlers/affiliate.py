import logging
import random
import string

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


def generate_affiliate_code(length=8):
    """Generate a random affiliate code"""
    characters = string.ascii_letters + string.digits
    return "".join(random.choice(characters) for _ in range(length))


def get_affiliate_code(user_id):
    """Get or create an affiliate code for a user"""
    try:
        # Check if user already has an affiliate code
        user = trades_db.get_user(user_id)
        if user and user.get("affiliate_code"):
            return user["affiliate_code"]

        # Generate new affiliate code
        affiliate_code = generate_affiliate_code()

        # Save affiliate code to user
        trades_db.update_user(user_id, {"affiliate_code": affiliate_code})

        return affiliate_code
    except Exception as e:
        logger.error(f"Error getting affiliate code: {e}")
        return None


async def start_affiliate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    This is the handler to start affiliate options
    """
    user = UserClient.get_user(update.message)

    #  WRTIE A PROCESS TO CHECK ADMIN AND SEND REQUEST TO PROCESS WITH USER
    username = update.message.from_user.username
    if user["_id"] != ADMIN_ID or user["verified"] == False:
        await context.bot.send_message(
            chat_id=user["_id"],
            text=emoji.emojize(
                """
    :robot: Awaiting authorization from support. Contact @Telescrowbotsupport to pass screening process
                """,
            ),
        )

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"""
    User ID - {user['_id']} just attempted adding this bot to a group
            """,
            parse_mode="HTML",
        )

    else:

        question = await context.bot.send_message(
            chat_id=user["_id"],
            text=emoji.emojize(
                """
    :robot: To use escrow service on your group, I would need the following information.
                
    Please reply with the your Group Username :grey_question: (example -> @GetGroupIDRobot)
                """,
            ),
        )

        context.user_data["next_step"] = add_addresses


async def add_addresses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_id = update.message.text
    try:
        chat = await context.bot.get_chat(group_id)

        if not chat.id:
            return await context.bot.send_message(
                chat_id=update.message.from_user.id, text="Invalid Group ID"
            )

        agent = AgentAction().create_agent(update.message.from_user.id)

        affiliate = create_affiliate(agent, str(chat.id))
        logger.debug(f"Affiliate creation result: {affiliate}")
        if affiliate != "Already Exists":
            await context.bot.send_message(
                chat_id=update.message.from_user.id,
                text=emoji.emojize(
                    ":+1: Congrats!! You can now add TeleEscrow Service(@tele_escrowbot) to your public group and receive your affiliate charge for trade performed by your members, selecting their roles on the group. Good Luck!!",
                ),
            )

        else:
            await context.bot.send_message(
                chat_id=update.message.from_user.id,
                text=emoji.emojize(
                    ":construction: This Group Is Already Registered",
                ),
            )
    except Exception as e:
        logger.error(f"Error adding addresses in affiliate: {e}")
        await context.bot.send_message(
            chat_id=update.message.from_user.id,
            text="Invalid Group ID or bot doesn't have access to the group",
        )


async def affiliate_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /affiliate command"""
    try:
        user_id = update.effective_user.id

        # Get user's affiliate code
        affiliate_code = get_affiliate_code(user_id)
        if not affiliate_code:
            raise Exception("Failed to generate affiliate code")

        # Get user's affiliate stats
        stats = trades_db.get_affiliate_stats(user_id)
        referrals = stats.get("referrals", 0)
        earnings = stats.get("earnings", 0)

        affiliate_text = f"""
🎯 <b>Affiliate Program</b>

Your unique affiliate code: <code>{affiliate_code}</code>

📊 <b>Your Stats</b>
• Total Referrals: {referrals}
• Total Earnings: {earnings} USDT

💰 <b>How It Works</b>
• Share your affiliate code with others
• Earn 20% of our fees from their trades
• Get paid automatically in USDT
• No minimum payout threshold

🔄 <b>Commission Structure</b>
• Level 1 (Direct): 20%
• Level 2 (Indirect): 5%
• Lifetime commissions
• Instant payouts

📱 <b>Share Your Link</b>
https://t.me/{context.bot.username}?start=ref_{affiliate_code}

Start sharing and earning today! 💪
"""

        # Check if this is from a callback query or direct command
        if update.callback_query:
            query = update.callback_query
            await query.answer()
            await query.edit_message_text(
                affiliate_text,
                parse_mode="html",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "📤 Share",
                                switch_inline_query=f"Join using my code: {affiliate_code}",
                            )
                        ],
                        [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")],
                    ]
                ),
            )
        else:
            await update.message.reply_text(
                affiliate_text,
                parse_mode="html",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "📤 Share",
                                switch_inline_query=f"Join using my code: {affiliate_code}",
                            )
                        ],
                        [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")],
                    ]
                ),
            )

    except Exception as e:
        logger.error(f"Error in affiliate handler: {e}")
        # Determine which message object to use
        message = (
            update.callback_query.message if update.callback_query else update.message
        )
        if message:
            await message.reply_text(
                "❌ An error occurred while accessing affiliate information. Please try again later.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]]
                ),
            )


async def handle_affiliate_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle affiliate-related callback queries"""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data.startswith("copy_link_"):
        link = data.replace("copy_link_", "")
        await query.edit_message_text(
            text=f"🔗 Here's your affiliate link:\n\n{link}\n\nCopy and share it with others!",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Back", callback_data="affiliate_menu")]]
            ),
        )

    elif data == "affiliate_stats":
        user_id = query.from_user.id
        stats = get_affiliate_stats(user_id)

        await query.edit_message_text(
            text=f"📊 <b>Your Affiliate Statistics</b>\n\n"
            f"Total referrals: {stats['total_referrals']}\n"
            f"Active referrals: {stats['active_referrals']}\n"
            f"Total earnings: ${stats['total_earnings']:.2f}\n\n"
            f"Keep sharing your link to earn more!",
            parse_mode="html",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Back", callback_data="affiliate_menu")]]
            ),
        )

    elif data == "affiliate_menu":
        # Return to main affiliate menu
        await affiliate_handler(update, context)


def register_handlers(application):
    """Register handlers for the affiliate module"""
    application.add_handler(CommandHandler("affiliate", affiliate_handler))
    application.add_handler(
        CallbackQueryHandler(
            handle_affiliate_callback,
            pattern="^(copy_link_|affiliate_stats|affiliate_menu)",
        )
    )


# Use the registry system to avoid import-time application creation
from .registry import register_handler_later

# Register handlers for later registration
register_handler_later(
    MessageHandler(filters.Regex("^Add Bot To Your Group"), start_affiliate)
)


def register_handlers(application):
    """Register affiliate handlers with the application (for main.py compatibility)"""
    try:
        application.add_handler(
            MessageHandler(filters.Regex("^Add Bot To Your Group"), start_affiliate)
        )
    except Exception as e:
        logger.error(f"Failed to register affiliate handlers: {e}")
