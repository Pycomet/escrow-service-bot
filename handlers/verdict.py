####ADMIN JUDGEMENT ON TRADE
from config import *
from utils import *
from functions import *

trade = ""


@bot.message_handler(commands=["disputes"])
def start_dispute(msg):
    "Starts The Ticket Review Session"

    if msg.from_user.id == ADMIN_ID:
        question = bot.send_message(ADMIN_ID, "What is the Dispute ID !")

        bot.register_next_step_handler(question, call_dispute)

    else:
        bot.reply_to(msg, "You are not authorised for this command")


def call_dispute(msg):
    """Send The Verdict To Buyer And Seller"""

    global trade
    dispute_id = msg.text

    dispute = get_dispute_by_id(dispute_id)
    keyboard = give_verdict()

    if dispute != None:
        trade = dispute.trade

        bot.send_message(
            msg.from_user.id,
            emoji.emojize(
                f"""
:ticket: <b>Dispute Ticket -- {dispute.id}</b>
----------------------
Complaint --> {dispute.complaint}


Trade Info;
-------------
<b>ID --> {trade.id}</b>
<b>Seller ID --> {trade.seller}</b>
<b>Buyer ID --> {trade.buyer}</b>
<b>Price --> {trade.price} {trade.currency}</b>
<b>Preferred method of payment --> {trade.coin}</b>
<b>Created on --> {trade.created_at}</b>
<b>Payment Status --> {trade.payment_status}</b>
<b>Is Open --> {trade.is_open}</b>

Give verdict :grey_question:
                """,
            ),
            reply_markup=keyboard,
            parse_mode="html",
        )

    else:
        bot.send_message(
            msg.from_user.id,
            emoji.emojize(
                ":warning: Dispute Not Found!",
            ),
        )


def pass_verdict(msg):
    """This Would Send The Admin Verdict To Both Parties Of The Trade"""
    message = msg.text

    users = [
        trade.seller,
        trade.buyer,
        msg.from_user.id,
    ]

    for user in users:

        bot.send_message(
            user,
            emoji.emojize(
                """
:ticket: <b>Administrative Decision On Trade %s</b>
-----------------------------------------
Ticket ID --> %s

%s
                """
                % (trade.id, trade.dispute[0].id, message),
            ),
            parse_mode="html",
        )

    bot.send_message(
        msg.from_user.id,
        emoji.emojize(
            "Who are you assigning payout to :grey_question:",
        ),
        reply_markup=refunds(),
    )
