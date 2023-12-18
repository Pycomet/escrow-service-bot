from config import *
from utils import *
from functions import *


@bot.message_handler(commands=["start", "escrow"])
def start(msg):
    """
    Starting the escrow service bot
    """
    bot.send_chat_action(msg.from_user.id, "typing")
    user: UserType = UserClient.get_user(msg)
    keyboard = main_menu(msg)

    bot.send_photo(
        user["_id"],
        photo="https://ibb.co/DLQ8yys",
        caption=Messages.welcome(msg.from_user.first_name),
        reply_markup=keyboard,
        parse_mode="html",
    )


def start_trade_menu(msg):
    """
    This is the handler to start trade seller or buyer options
    """
    keyboard = trade_menu()
    user: UserType = UserClient.get_user(msg)

    bot.send_message(
        user["_id"],
        "<b>Welcome! Please select an option from the menu below?</b>",
        reply_markup=keyboard,
        parse_mode="html",
    )
