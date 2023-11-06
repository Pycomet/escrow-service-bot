from config import *
from keyboard import *
from functions import *

@bot.message_handler(regexp="^Initiate")
def open_trade(msg):
    """
    This opens a new trade with seller actions
    """
    keyboard = local_currency_menu()

    chat, id = get_received_msg(msg)
    bot.delete_message(chat.id, id)

    bot.send_message(
        msg.chat.id,
        emoji.emojize(
            ":money_bag: To create a new trade today, select which is your local currency of choice... ",
            
        ),
        reply_markup=keyboard
    )





def select_coin(user):
    """
    Selecting the right coin option for trade
    """
    keyboard = coin_menu()

    bot.send_message(
        user.id,
        emoji.emojize(
            ":money_bag: What is your preferred coin for payment ? ",
            
        ),
        reply_markup=keyboard
    )


##############TRADE CREATION
def trade_price(user):
    """
    Receive user input on trade price
    """
    question = bot.send_message(
        user.id,
        emoji.emojize(
            ":money_bag: How much are you expecting to be paid in your local currency? ",
            
        )
    )
    question = question.wait()
    
    bot.register_next_step_handler(question, trade_address)

def trade_address(msg):
    """
    Recieve user input on trade wallet address
    """
    price = msg.text

    add_price(
        user=msg.from_user,
        price=float(price)
        )

    #REQUEST WALLET ADDRESS
    question = bot.send_message(
        msg.from_user.id,
        emoji.emojize(
            ":money_bag: Paste the wallet address to which you will recieve payment referenced to the coin you selected above (Confirm the wallet address to make sure it is correct) ",
            
        )
    )
    question = question.wait()

    bot.register_next_step_handler(question, process_trade)



def process_trade(msg):
    """
    Assigning of trade wallet
    """
    wallet = msg.text

    add_wallet(
        user=msg.from_user,
        address=wallet
    )

    trade = get_recent_trade(msg.from_user)

    payment_link = send_invoice(trade)

    bot.send_message(
        trade.seller,
        emoji.emojize(
            f"""
:memo: <b>Trade Details</b> :memo:
-----------------------

   :beginner: <b>ID --> {trade.id}</b>
   :beginner: <b>Payment Portal--> {payment_link}</b>
   :beginner: <b>Preferred method of payment --> {trade.coin}</b>
   :beginner: <b>Created on --> {trade.created_at}</b>

Share only the trade ID with your customer to allow his/her join the trade. They would receive all the related information when they join.
            """,
            
        ),
        parse_mode="html",
    )
