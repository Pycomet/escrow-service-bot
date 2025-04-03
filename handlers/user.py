from config import *
from utils import *
from functions import *
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters


async def user_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Returns the user's wallet address
    """
    await context.bot.send_chat_action(chat_id=update.message.from_user.id, action="typing")
    user = UserClient.get_user(update.message)

    await context.bot.send_message(
        chat_id=user["_id"],
        text=f"Your wallet address is: <b>{user['wallet']}</b>",
        parse_mode="html",
    )


async def update_user_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Updates the user's wallet address
    """
    await context.bot.send_chat_action(chat_id=update.message.from_user.id, action="typing")
    user = UserClient.get_user(update.message)

    await context.bot.send_message(
        chat_id=user["_id"],
        text="Please type in your new wallet address ?",
        # reply_markup=types.ReplyKeyboardRemove()
    )

    context.user_data["next_step"] = update_wallet


async def update_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Updates the user's wallet address
    """
    address = update.message.text
    user = UserClient.get_user(update.message)

    UserClient.set_wallet(user["_id"], address)

    await context.bot.send_message(
        chat_id=update.message.from_user.id, 
        text="✅ Wallet updated successfully", 
        reply_markup=trade_menu()
    )

# Register handlers
application.add_handler(CommandHandler("wallet", user_wallet))
application.add_handler(CommandHandler("editwallet", update_user_wallet))
