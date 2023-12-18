from config import *
from utils import *
from functions import *


@bot.message_handler(regexp="^Join A Trade")
def join_request(msg):
    """
    Lets a user receive trade information by ID
    """

    chat, id = get_received_msg(msg)
    bot.delete_message(chat.id, id)
    user = UserClient.get_user(msg)

    question = bot.send_message(
        msg.chat.id,
        emoji.emojize(
            "What is the ID of the trade you wish to join ? ",
        ),
    )
    bot.register_next_step_handler(question, join_trade)


def join_trade(msg):
    """
    Validate Buyer To Trade ID
    """
    trade_id = msg.text

    user = UserClient.get_user(msg)

    trade: TradeType = TradeClient.check_trade(user=user, trade_id=trade_id)
    print(trade)

    # import pdb; pdb.set_trace()

    if isinstance(trade, str) != True:

        payment_url = TradeClient.get_invoice_url(trade=trade)
        status = TradeClient.get_invoice_status(trade=trade)

        # SEND TO BUYER########
        bot.send_message(
            trade["buyer_id"],
            Messages.trade_joined(trade, status),
            parse_mode="html",
            reply_markup=confirm(payment_url) if status is not "Expired" else None,
        )

        ##SEND ALERT TO SELLER#########
        bot.send_message(
            trade["seller_id"],
            emoji.emojize(
                f"⚠️{trade['buyer_id']} has just joined a this trade - {trade['_id']}",
            ),
            parse_mode="html",
        )

    elif trade == "Not Permitted":

        bot.send_message(
            str(user["chat"]),
            emoji.emojize(
                "⚠️ You can not be a seller and buyer at the same time",
            ),
        )

    elif trade == "Both parties already exists":

        bot.send_message(
            str(user["chat"]),
            emoji.emojize(
                "⚠️ There is already a buyer and seller on this trade!",
            ),
        )

    else:
        bot.send_message(
            str(user["chat"]),
            emoji.emojize(
                f"⚠️ Trade not found! - {trade}",
            ),
        )
