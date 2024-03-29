from config import *
from utils import *
from functions import *


@bot.message_handler(commands=["wallet"])
def user_wallet(msg):
    """
    Returns the user's wallet address
    """
    bot.send_chat_action(msg.from_user.id, "typing")
    user = UserClient.get_user(msg)

    bot.send_message(
        user["_id"],
        f"Your wallet address is: <b>{user['wallet']}</b>",
        parse_mode="html",
    )


@bot.message_handler(commands=["editwallet"])
def update_user_wallet(msg):
    """
    Updates the user's wallet address
    """
    bot.send_chat_action(msg.from_user.id, "typing")
    user = UserClient.get_user(msg)

    bot.send_message(
        user["_id"],
        "Please type in your new wallet address ?",
        # reply_markup=types.ReplyKeyboardRemove()
    )

    bot.register_next_step_handler(msg, update_wallet)


def update_wallet(msg):
    """
    Updates the user's wallet address
    """
    address = msg.text
    user = UserClient.get_user(msg)

    UserClient.set_wallet(user["_id"], address)

    bot.send_message(
        msg.from_user.id, "✅ Wallet updated successfully", reply_markup=trade_menu()
    )
