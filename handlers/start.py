from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from config import *
from functions import *
from utils import *


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command"""
    user = update.effective_user
    await context.bot.send_chat_action(chat_id=user.id, action="typing")
    
    # Check if user has a referral code
    args = context.args
    if args:
        referral_code = args[0]
        # Store referral code for later use
        context.user_data["referral_code"] = referral_code
    
    # Get user data
    user_data = UserClient.get_user(update.message)
    
    # Welcome message
    welcome_text = (
        f"👋 Welcome {user.first_name}!\n\n"
        "I'm your Escrow Service Bot. I can help you with:\n\n"
        "💰 Creating secure trades\n"
        "🤝 Joining existing trades\n"
        "📜 Viewing trade history\n"
        "📋 Reading rules and guidelines\n"
        "👥 Joining our community\n"
        "🎯 Participating in our affiliate program\n\n"
        "What would you like to do?"
    )
    
    await update.message.reply_text(
        text=welcome_text,
        reply_markup=await main_menu(update, context),
        parse_mode="html"
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
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("📞 Contact Support", url=f"https://t.me/{SUPPORT_USERNAME}"),
            InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
        ]])
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
