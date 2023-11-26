from config import *
from utils import *
from functions import *

@bot.message_handler(commands=['start', 'escrow'])
def start(msg):
    """
    Starting the escrow service bot
    """
    bot.send_chat_action(msg.from_user.id, "typing")
    # user = get_user(msg)
    keyboard = main_menu(msg)

    bot.send_photo(
        msg.from_user.id,
        photo="https://ibb.co/DLQ8yys",
        caption=emoji.emojize(
            f"""
    :circus_tent: <b>Welcome to the Telegram Escrow Service {msg.from_user.first_name} </b>
    
My purpose is to create a save trade environment for both seller and buyer subject to my rules.

Your funds are save with me and will be refunded to you if the other party refuses to comply with the rules.
            """
        ),
        reply_markup=keyboard,
        parse_mode="html"
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



