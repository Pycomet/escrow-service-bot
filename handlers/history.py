from config import *
from utils import *
from functions import *


@bot.message_handler(regexp="^Trade")
def trade_history(msg):
    """
    Return all the trades the user is involved in
    """

    bot.send_chat_action(msg.from_user.id, "typing")
    user = UserClient.get_user(msg)
    sells, buys = TradeClient.get_trades(str(msg.from_user.id))
    purchases, sales, trades, active, reports = TradeClient.get_trades_report(
        sells, buys
    )

    chat, id = get_received_msg(msg)
    bot.delete_message(chat.id, id)

    if sells == [] and buys == []:
        bot.send_message(
            user["_id"],
            emoji.emojize(
                """
        <b>NO TRADE HISTORY</b>
                """,
            ),
            parse_mode="html",
        )

    else:

        bot.send_message(
            user["_id"],
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
    user = UserClient.get_user(msg)
    sells, buys = TradeClient.get_trades(user["_id"])

    all_trades = sells + buys

    bot.send_message(
        user["_id"],
        f"""
<b>All ({len(all_trades)}) Trades IDs </b>
------------------
{', '.join([f"<b>{trade['_id']} ({'Seller' if trade['seller_id'] == user['_id'] else 'Buyer'})</b>" for trade in all_trades])}
        """,
        parse_mode="html",
    )


def send_trade(msg):
    "Returns A Specific Trade Information"

    question = bot.send_message(
        msg.from_user.id,
        emoji.emojize(
            ":warning: What is the ID of the trade ? ",
        ),
    )

    bot.register_next_step_handler(question, view_trade)


def view_trade(msg):
    user = msg.from_user
    trade_id = msg.text

    try:
        trade = TradeClient.get_trade(trade_id)
        status = TradeClient.get_invoice_status(trade=trade)

        bot.send_message(
            msg.from_user.id,
            Messages.trade_details(trade, status),
            parse_mode="html",
        )

    except Exception as e:
        print(e)
        bot.send_message(msg.from_user.id, "Trade Not Found")
