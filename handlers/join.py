from config import *
from keyboard import *
from functions import *


@bot.message_handler(regexp="^Join")
def join_request(msg):
    """
    Lets a user receive trade information by ID
    """

    chat, id = get_received_msg(msg)
    bot.delete_message(chat.id, id)

    question = bot.send_message(
        msg.from_user.id,
        emoji.emojize(
            "What is the ID of the trade you wish to join ? ",
            
        )
    )
    question = question.wait()
    
    bot.register_next_step_handler(question, join_trade)

def join_trade(msg):
    """
    Validate Buyer To Trade ID
    """
    trade_id = msg.text

    trade = check_trade(
        user=msg.from_user,
        trade_id=trade_id)

    if isinstance(trade, str) != True:
        
        #Amount To Be Paid
        coin_price = get_coin_price(
            coin_code=trade.coin,
            currency_code=trade.currency
        )
  
        agent = get_agent(trade)
        payment_url = client.get_payment_url(trade, agent)

        receive_wallet = get_receive_address(trade)

        #SEND TO BUYER########
        bot.send_message(
            trade.buyer,
            emoji.emojize(
                f"""
:memo: <b>{trade.id} Trade Details</b> 
-----------------------------------
:beginner: <b>Price --> {trade.price} {trade.currency}</b>
:beginner: <b>Preferred method of payment --> {trade.coin}</b>
:beginner: <b>Created on --> {trade.created_at}</b>
:beginner: <b>Payment Complete --> {trade.payment_status}</b>

:point_right: <b>Please follow the url below to make payment on our secured portal. Click the button to confirm after you make payment</b>

You can make your payment to the address below

{payment_url}

:point_right: {receive_wallet}

                """,
                
            ),
            parse_mode="html",
            reply_markup=confirm(),
        )

        ##SEND ALERT TO SELLER#########
        bot.send_message(
            trade.seller,
            emoji.emojize(
                "<b>Buyer Just Joined Trade!!</b>",
                
            ),
            parse_mode="html"
        )

    elif trade == "Not Permitted":

        bot.send_message(
            msg.from_user.id,
            emoji.emojize(
                ":warning: You can not be a seller and buyer at the same time!",
                
            )
        ) 

    else:
        bot.send_message(
            msg.from_user.id,
            emoji.emojize(
                ":warning: Trade Not Found!",
                
            )
        )

