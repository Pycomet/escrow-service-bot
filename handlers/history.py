from config import *
from utils import *
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
    # import pdb;
    # pdb.set_trace()
    bot.send_chat_action(msg.from_user.id, "typing")
    user = get_user(msg)
    sells, buys = get_trades(user.id)

    all_trades = sells + buys

    bot.send_message(
        user.id,
        f"""
<b>All ({len(all_trades)}) Trades IDs </b>
------------------
{', '.join([f"<b>{trade.id} ({'Seller' if trade.seller_id == user.id else 'Buyer'})</b>" for trade in all_trades])}
        """,
        parse_mode="html",
    )





def send_trade(msg):
    "Returns A Specific Trade Information"

    question = bot.send_message(
        msg.from_user.id,
        emoji.emojize(
            ":warning: What is the ID of the trade ? ",
            
        )
    )
    
    bot.register_next_step_handler(question, view_trade)



def view_trade(msg):
    user = msg.from_user
    trade_id = msg.text

    try:
        trade = get_trade(trade_id)
        status = get_invoice_status(trade=trade)

        bot.send_message(
            msg.from_user.id,
            emoji.emojize(
                f"""
:memo: <b>Trade {trade.id} Payment Details</b> 
-----------------------------------
<b>Terms Of Contract:</b> {trade.terms}

<b>Buyer ID: </b> {trade.buyer_id}
<b>Seller ID: </b> {trade.seller_id}

<b>Transaction Amount:</b> {trade.price} {trade.currency}
<b>Preferred Payment Method:</b> Bitcoin
<b>Trade Initiated On:</b> {datetime.strftime(trade.created_at, "%Y-%m-%d %H:%M:%S")}
<b>Payment Status:</b> {status}
            """),
            parse_mode="html"
        )

    except Exception as e:
        bot.send_message(
            msg.from_user.id,
            "Trade Not Found"
        )