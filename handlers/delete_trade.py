from config import *
from utils import *
from functions import *


@bot.message_handler(regexp="^Delete")
def delete_request(msg):
    """
    This is an option to delete trade by id
    """
    chat, id = get_received_msg(msg)
    bot.delete_message(chat.id, id)

    question = bot.send_message(
        msg.from_user.id,
        emoji.emojize(
            ":warning: What is the ID of the trade ? ",
        ),
    )

    bot.register_next_step_handler(question, trade_delete)


def trade_delete(msg):
    """
    Deleting the trade
    """
    user = msg.from_user
    trade_id = msg.text

    response = TradeClient.seller_delete_trade(user['_id'], trade_id)

    bot.send_message(
        user['_id'],
        emoji.emojize(
            f"""
<b>{response}</b>
            """,
        ),
        parse_mode="html",
    )
