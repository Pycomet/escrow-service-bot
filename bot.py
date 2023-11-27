from config import *
from utils import *
from functions import *


# APPROVING PAYMENTS
def validate_pay(msg):
    "Receives the transaction hash for checking"
    trade = get_recent_trade(msg.from_user)

    # trade_hash = msg.text

    status = check_payment(trade)

    if status == "Approved":

        # SEND CONFIRMATION TO SELLER
        bot.send_message(
            trade.seller,
            emoji.emojize(
                f"""
:memo: <b>TRADE ID - {trade.id}</b> :memo:
------------------------------------                  
<b>Buyer Payment Confirmed Successfully :white_check_mark: . Please release the goods to the buyer before being paid</b>
                """,
            ),
            parse_mode="html",
        )

        # SEND CONFIRMATION TO BUYER
        bot.send_message(
            trade.buyer,
            emoji.emojize(
                f"""
:memo: <b>TRADE ID - {trade.id}</b> :memo:
------------------------------------       
<b>Payment Confirmed Sucessfully :white_check_mark: . Seller has been instructed to release the goods to you.</b>
                """,
            ),
            parse_mode="html",
            reply_markup=confirm_goods(),
        )

    else:

        # SEND ALERT TO SELLER
        bot.send_message(
            trade.buyer,
            emoji.emojize(
                f"""
:memo: <b>TRADE ID - {trade.id}</b> :memo:
------------------------------------     
<b>Payment Still Pending! :heavy_exclamation_mark: Please cross check the transaction hash and try again.</b>
                """,
            ),
            parse_mode="html",
        )
    # bot.delete_message(msg.chat.id, msg.message_id)


# REFUND PROCESS FOR BUYER


def refund_to_buyer(msg):
    "Refund Coins Back To Buyer"
    trade = get_recent_trade(msg)

    if trade.payment_status == True:

        question = bot.send_message(
            trade.buyer,
            f"A refund was requested for your funds on trade {trade.id}. Please paste a wallet address to receive in {trade.coin}",
        )
        bot.register_next_step_handler(question, refund_coins)

    else:
        bot.send_message(
            msg.id,
            emoji.emojize(
                ":warning: Buyer Has Not Made Payments Yet!!",
            ),
            parse_mode="html",
        )


def refund_coins(msg):
    "Payout refund"

    wallet = msg.text
    trade = get_recent_trade(msg.from_user)

    status, _ = pay_to_buyer(trade, wallet)
    if status is None:

        send_invoice_to_admin(price=_, address=wallet)
        close_trade(trade)

    bot.send_message(
        ADMIN_ID,
        emoji.emojize(
            """
<b>Refunds Paid</b> :heavy_check_mark:
Txid -> {status}
            """,
        ),
        parse_mode="html",
    )


# PAYOUT FUNDS TO SELLER

##REFUND PROCES SELLER TO RECEIVE FUNDS
def refund_to_seller(msg):
    "Refund Coins Back To Buyer"
    trade = get_recent_trade(msg)
    confirm_pay(trade)

    if trade.payment_status == True:

        status, _ = pay_funds_to_seller(trade)
        if status is None:

            send_invoice_to_admin(price=_, address=trade.wallet)
            close_trade(trade)

        bot.send_message(
            ADMIN_ID,
            emoji.emojize(
                f"""
<b>Paid To Seller</b> :heavy_check_mark:
Txid -> {status}
                """,
            ),
            parse_mode="html",
        )

    else:
        bot.send_message(
            msg.id,
            emoji.emojize(
                ":warning: Buyer Has Not Made Payments Yet!!",
            ),
            parse_mode="html",
        )


# CLOSE TRADE WITH NO PAYOUTS
def close_dispute_trade(msg):
    "Close Order After Dispute & No Body Has Paid"
    trade = get_recent_trade(msg)

    close_trade(trade)

    users = [trade.seller, trade.buyer]

    for user in users:

        bot.send_message(
            user,
            emoji.emojize(
                f"<b>Trade {trade.id} Closed</b> :mailbox_closed: ",
            ),
            parse_mode="html",
        )


def send_invoice_to_admin(price, address):
    "Send An Invoice For Payment To Admin"
    admin = f"@{ADMIN}"

    bot.send_message(
        admin,
        f"""
<b>New Payment Invoice</b>

Cost - {price} BTC
        
<em>{address}</em>
        """,
        parse_mode="HTML",
    )
