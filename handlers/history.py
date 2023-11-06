from config import *
from keyboard import *
from functions import *


@bot.message_handler(regexp="^Trade")
def trade_history(msg):
    """
    Return all the trades the user is involved in
    """
    user = msg.from_user
    sells, buys = get_trades(user)

    purchases, sales, trades, active, reports = get_trades_report(sells, buys)

    chat, id = get_received_msg(msg)
    bot.delete_message(chat.id, id)


    if sells == [] and buys == []:
        bot.send_message(
            user.id,
            emoji.emojize(
                """
        <b>NO TRADE HISTORY</b>
                """,
                
            ),
            parse_mode="html",
        )

    else:
        
        bot.send_message(
            user.id,
            emoji.emojize(
                f"""
<b>Trade Reports</b> :book:
Here is a record of all your recent trades

👉 <b>Active trades                 {active}</b>
👉 <b>Total trades                  {trades}</b>
👉 <b>Trades as buyer             {purchases}</b>
👉 <b>Trades as seller             {sales}</b>
👉 <b>Reported trades             {reports}</b>


                """,
                
            ),
            reply_markup=select_trade(),
            parse_mode="html",
        )







def send_all_trades(msg):
    """
    Return all the trades the user is involved in
    """
    user = msg.from_user
    sells, buys = get_trades(user)


    for sell in sells:

        bot.send_message(
            user.id,
            emoji.emojize(
                f"""
<b>SELLER ROLE</b> :man:
------------------
<b>ID --> {sell.id}</b>
<b>Price --> {sell.price} {sell.currency}</b>
<b>Preferred method of payment --> {sell.coin}</b>
<b>Created on --> {sell.created_at}</b>
<b>Payment Complete --> {sell.payment_status}</b>
<b>Trade still open --> {sell.is_open}</b>
<b>Affiliate ID --> {sell.agent_id}</b>

<b>Dispute Status --> {sell.is_dispute()}</b>
                """,
                    
                ),
                parse_mode="html",
            )

    for buy in buys:

        bot.send_message(
            user.id,
            emoji.emojize(
                f"""
<b>BUYER ROLE</b> :man:
------------------
<b>ID --> {buy.id}</b>
<b>Price --> {buy.price} {buy.currency}</b>
<b>Preferred method of payment --> {buy.coin}</b>
<b>Created on --> {buy.created_at}</b>
<b>Payment Complete --> {buy.payment_status}</b>
<b>Trade still open --> {buy.is_open}</b>
<b>Affiliate ID --> {buy.agent_id}</b>

<b>Dispute Status --> {buy.is_dispute()}</b>
                """,
                
            ),
            parse_mode="html",
        )



def user_trade_delete(msg):
    user = msg.from_user
    trade_id = msg.text

    response = seller_delete_trade(user.id, trade_id)
    

    bot.send_message(
        user.id,
        emoji.emojize(
            f"""
<b>{response}</b>
            """,
            
        ),
        parse_mode="html",
    )




