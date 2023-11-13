from config import *
from keyboard import *
from functions import *


@bot.message_handler(regexp="^Trade")
def trade_history(msg):
    """
    Return all the trades the user is involved in
    """

    bot.send_chat_action(msg.from_user.id, "typing")
    user = get_user(msg)
    sells, buys = get_trades(msg.from_user.id)

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
                f"""
<b>Trade Reports</b> 📚
Here is a record of all your recent trades

👉 <b>Active trades                 {active}</b>
👉 <b>Total trades                  {trades}</b>
👉 <b>Trades as buyer             {purchases}</b>
👉 <b>Trades as seller             {sales}</b>
👉 <b>Reported trades             {reports}</b>
                """,
            reply_markup=select_trade(),
            parse_mode="html",
        )







def send_all_trades(msg):
    """
    Return all the trades the user is involved in
    """
    bot.send_chat_action(msg.from_user.id, "typing")
    user = get_user(msg)
    sells, buys = get_trades(user.id)

    all_trades = sells + buys

    bot.send_message(
        user.id,
        f"""
<b>All Trades IDs - ({len(all_trades)})</b>
------------------
{', '.join([f"<b>{trade.id} ({'Seller' if trade.seller_id == user.id else 'Buyer'})</b>" for trade in all_trades])}
        """,
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




