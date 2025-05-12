from config import *
from utils import *
from functions import *
from telegram import Update
from telegram.ext import ContextTypes


# APPROVING PAYMENTS
async def validate_pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    "Receives the transaction hash for checking"
    user = UserClient.get_user(update.message)
    trade: TradeType = TradeClient.get_most_recent_trade(user)
    status = TradeClient.get_invoice_status(trade=trade)
    print("Status", status)

    if status.lower() == "approved" or status.lower() == "completed":

        # SEND CONFIRMATION TO SELLER
        await context.bot.send_message(
            chat_id=trade['seller_id'],
            text=emoji.emojize(
                f"""
📝 <b>Trade ID - {trade['_id']}</b> 📝
------------------------------------                  
Buyer's Payment Confirmed Successfully ☑️ 

Please release <b>{trade['terms']}</b>, before you can receive payment.
                """,
            ),
            parse_mode="html",
        )

        # SEND CONFIRMATION TO BUYER
        await context.bot.send_message(
            chat_id=update.message.from_user.id,
            text=emoji.emojize(
                f"""
📝 <b>Trade ID - {trade['_id']}</b> 📝
------------------------------------       
Payment Confirmed Sucessfully ☑️ 

Seller has been instructed to release the goods to you.
                """,
            ),
            parse_mode="html",
            reply_markup=confirm_goods(),
        )

    else:

        # SEND ALERT TO SELLER
        await context.bot.send_message(
            chat_id=update.message.from_user.id,
            text=emoji.emojize(
                f"""
📝 <b>Trade {trade['_id']} - {status}</b> 📝
------------------------------------     
Payment Is Still Pending ❗
                """,
            ),
            parse_mode="html",
        )
    # await context.bot.delete_message(chat_id=update.message.chat.id, message_id=update.message.message_id)


# REFUND PROCESS FOR BUYER
async def refund_to_buyer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    "Refund Coins Back To Buyer"
    user = UserClient.get_user(update.message)
    trade: TradeType = TradeClient.get_most_recent_trade(user)
    
    if trade.payment_status == True:

        question = await context.bot.send_message(
            chat_id=trade.buyer,
            text=f"A refund was requested for your funds on trade {trade.id}. Please paste a wallet address to receive in {trade.coin}",
        )
        context.user_data["next_step"] = refund_coins

    else:
        await context.bot.send_message(
            chat_id=update.message.chat.id,
            text=emoji.emojize(
                ":warning: Buyer Has Not Made Payments Yet!!",
            ),
            parse_mode="html",
        )


async def refund_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    "Payout refund"

    wallet = update.message.text
    trade = get_recent_trade(update.message.from_user)

    status, _ = pay_to_buyer(trade, wallet)
    if status is None:

        await send_invoice_to_admin(price=_, address=wallet)
        close_trade(trade)

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=emoji.emojize(
            f"""
<b>Refunds Paid</b> ☑️
Txid -> {status}
            """,
        ),
        parse_mode="html",
    )


# PAYOUT FUNDS TO SELLER

# REFUND PROCES SELLER TO RECEIVE FUNDS
async def refund_to_seller(update: Update, context: ContextTypes.DEFAULT_TYPE):
    "Refund Coins Back To Buyer"
    trade = get_recent_trade(update.message)
    await confirm_pay(trade)

    if trade.payment_status == True:

        status, _ = pay_funds_to_seller(trade)
        if status is None:

            await send_invoice_to_admin(price=_, address=trade.wallet)
            close_trade(trade)

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=emoji.emojize(
                f"""
<b>Paid To Seller</b> :heavy_check_mark:
Txid -> {status}
                """,
            ),
            parse_mode="html",
        )

    else:
        await context.bot.send_message(
            chat_id=update.message.chat.id,
            text=emoji.emojize(
                ":warning: Buyer Has Not Made Payments Yet!!",
            ),
            parse_mode="html",
        )


# CLOSE TRADE WITH NO PAYOUTS
async def close_dispute_trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    "Close Order After Dispute & No Body Has Paid"
    trade = get_recent_trade(update.message)

    close_trade(trade)

    users = [trade.seller, trade.buyer]

    for user in users:

        await context.bot.send_message(
            chat_id=user,
            text=emoji.emojize(
                f"<b>Trade {trade.id} Closed</b> :mailbox_closed: ",
            ),
            parse_mode="html",
        )


async def send_invoice_to_admin(price, address):
    "Send An Invoice For Payment To Admin"
    admin = ADMIN_ID

    await application.bot.send_message(
        chat_id=int(admin),
        text=f"""
<b>New Payment Invoice</b>

Cost - {price} BTC
        
<em>{address}</em>
        """,
        parse_mode="HTML",
    )
