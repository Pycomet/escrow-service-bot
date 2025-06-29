import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CommandHandler, ContextTypes, MessageHandler, filters

from config import *
from functions import *
from utils import *
from utils.enums import CallbackDataEnums, EmojiEnums
from utils.keyboard import main_menu
from utils.messages import Messages

logger = logging.getLogger(__name__)


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command"""
    try:
        # Get the user's first name
        user_name = update.effective_user.first_name or "User"

        welcome_text = (
            f"🎪 <b>Welcome {user_name} to the Telegram Escrow Service Bot!</b>\n\n"
            "I help facilitate secure transactions between buyers and sellers. "
            "Here's what you can do:\n\n"
            f"{EmojiEnums.MONEY_BAG.value} Creating secure trades\n"
            f"{EmojiEnums.HANDSHAKE.value} Joining existing trades\n"
            f"{EmojiEnums.SCROLL.value} Viewing trade history\n"
            f"{EmojiEnums.LOCK.value} Managing your crypto wallets\n\n"
            "💡 <b>Tip:</b> All your funds are secured through our escrow system until both parties are satisfied!\n\n"
            "Choose an option below to get started:"
        )

        await update.message.reply_text(
            welcome_text,
            parse_mode="HTML",
            reply_markup=await main_menu(update, context),
        )

    except Exception as e:
        logger.error(f"Error in start handler: {e}")
        await update.message.reply_text(
            f"{EmojiEnums.CROSS_MARK.value} <b>Welcome!</b>\n\n"
            "Something went wrong, but don't worry - you can still use the bot!\n"
            "Use the menu below to get started:",
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


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /help command"""
    help_text = (
        "🆘 <b>Need Help?</b>\n\n"
        "Here are some common commands:\n\n"
        "/start - Start the bot\n"
        "/trade - Create a new trade\n"
        "/join - Join an existing trade\n"
        "/history - View your trade history\n"
        "/rules - View our service rules\n"
        "/community - Join our community\n"
        "/affiliate - Learn about our affiliate program\n"
        "/help - Show this help message\n\n"
        "For more assistance, please contact our support team."
    )

    await update.message.reply_text(
        help_text,
        parse_mode="html",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "📞 Contact Support", url=f"https://t.me/{SUPPORT_USERNAME}"
                    ),
                    InlineKeyboardButton(
                        f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                        callback_data=CallbackDataEnums.MENU.value,
                    ),
                ]
            ]
        ),
    )


def register_handlers(application):
    """Register handlers for the start module"""
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("help", help_handler))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Starting the escrow service bot
    """
    user = update.message.from_user
    await context.bot.send_chat_action(chat_id=user.id, action="typing")
    user_data: UserType = UserClient.get_user(update.message)
    keyboard = await main_menu(update, context)

    await update.message.reply_text(
        text=Messages.welcome(user.first_name),
        reply_markup=keyboard,
        parse_mode="html",
    )


async def start_trade_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    This is the handler to start trade seller or buyer options
    """
    # keyboard = trade_menu()

    await update.message.reply_text(
        "<b>Welcome! Please select an option from the menu below?</b>",
        # reply_markup=keyboard,
        parse_mode="html",
    )
