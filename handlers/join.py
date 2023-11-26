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
    user = get_user(msg)

    question = bot.send_message(
        user.chat,
        emoji.emojize(
            "What is the ID of the trade you wish to join ? ",
            
        )
    )
    bot.register_next_step_handler(question, join_trade)

def join_trade(msg):
    """
    Validate Buyer To Trade ID
    """
    trade_id = msg.text

    user = get_user(msg)

    trade = check_trade(
        user=user,
        trade_id=trade_id)


    if isinstance(trade, str) != True:
        
        payment_url = get_invoice_url(trade=trade)
        status = get_invoice_status(trade=trade)

        #SEND TO BUYER########
        bot.send_message(
            trade.buyer_id,
            emoji.emojize(
                f"""
:memo: <b>Trade {trade.id} Payment Details</b> 
-----------------------------------
<b>Terms Of Contract:</b> {trade.terms}

<b>Transaction Amount:</b> {trade.price} {trade.currency}
<b>Preferred Payment Method:</b> Bitcoin
<b>Trade Initiated On:</b> {datetime.strftime(trade.created_at, "%Y-%m-%d %H:%M:%S")}
<b>Payment Status:</b> {status}

<b>Please follow the url below to make payment on our secured portal. Click the button to confirm after you make payment</b>

You can go to payment portal by clicking the button below.
                """
            ),
            parse_mode="html",
            reply_markup=confirm(payment_url),
        )

        ##SEND ALERT TO SELLER#########
        bot.send_message(
            trade.seller_id,
            emoji.emojize(
                f"<b>{trade.buyer.name}</b> just joined a this trade - {trade.id}</b>",
                
            ),
            parse_mode="html"
        )

    elif trade == "Not Permitted":

        bot.send_message(
            user.chat,
            emoji.emojize(
                "⚠️ You can not be a seller and buyer at the same time",
                
            )
        ) 
    
    elif trade == "Both parties already exists":

        bot.send_message(
            user.chat,
            emoji.emojize(
                "⚠️ There is already a buyer and seller on this trade!",
                
            )
        ) 

    else:
        bot.send_message(
            user.chat,
            emoji.emojize(
                f"⚠️ Trade not found! - {trade}",
                
            )
        )

