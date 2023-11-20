from config import *
from keyboard import *
from functions import *

@bot.message_handler(commands=['start', 'escrow'])
def start(msg):
    """
    Starting the escrow service bot
    """
    print(f"New User - {msg.from_user.username} - {msg.from_user.id}")
    user = get_user(msg)
    keyboard = main_menu(msg)

    bot.send_photo(
        user.id,
        photo="https://ibb.co/DLQ8yys",
        caption=emoji.emojize(
            f"""
    Hello {msg.from_user.first_name},

:circus_tent: Welcome to the Telegram Escrow Service Bot. My purpose is to create a save trade environment for both seller and buyer subject to my rules.

Your funds are save with me and will be refunded to you if the other party refuses to comply with the rules.
            """
        ),
        allow_sending_without_reply=True,
        reply_markup=keyboard
    )




def start_trade_menu(msg):
    """
    This is the handler to start trade seller or buyer options
    """
    keyboard = trade_menu()
    user = get_user(msg)

    bot.send_message(
        user.id,
        "<b>Welcome! Please select an option from the menu below?</>",
        reply_markup=keyboard,
        parse_mode="html"
    )



