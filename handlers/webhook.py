from config import *
from functions import *
from utils import *


def handle_invoice_paid_webhook(data):
    "Response to when the invoice has been paid"
    trade = get_trade_by_invoice_id(data["invoiceId"])
    handle_invoice_paid(trade.invoice_id)

    # Notify the seller to fulfill their agreed terms and wait for the buyer's approval
    seller_notification = (
        f"🚀 Congratulations! Trade <b>({trade.id})</b> has been paid, and you're one step closer to completion. "
        "Please fulfill your agreed terms, and once done, request the buyer to approve the transaction on the bot. "
        "Upon approval, the payment will be released to you."
    )
    bot.send_message(
        trade.seller_id,
        seller_notification,
        parse_mode="html",
        reply_markup=review_menu(),
    )

    # Notify the buyer to approve the transaction
    approval_message = (
        f"🎉 Payment of <b>{trade.price} {trade.currency}</b> on trade <b>({trade.id})</b> has been successfully completed! "
        "Please review the terms of the trade and click the button below to approve the transaction. "
        "Your payment will be released to the seller upon approval."
    )

    bot.send_message(
        trade.buyer_id, approval_message, reply_markup=give_verdict(), parse_mode="html"
    )

    completion_message = (
        f"🎉 New Trade Completed! <b>{trade.id}</b> \n\n"
        "✅ The trade has been successfully completed. Buyers and sellers have been notified.\n"
        "Thank you for using our platform!"
    )

    bot.send_message(
        "@trusted_escrow_bot_reviews",
        completion_message,
        parse_mode="html",
        disable_web_page_preview=True,
    )

    # # Notify the buyer that the trade has been successfully completed
    # bot.send_message(
    #     trade.buyer_id,
    #     f"🎉 Trade <b>({trade.id})</b> has been successfully completed! "
    #     "Thank you for your payment. If you have any further questions or need assistance, feel free to reach out. "
    #     "We appreciate your business!",
    #     reply_markup=review_menu(),
    #     parse_mode="html"
    # )

    # # Notify the seller that the trade has been successfully completed
    # bot.send_message(
    #     trade.seller_id,
    #     f"🎉 Trade <b>({trade.id})</b> has been successfully completed! "
    #     f"Payment of {trade.currency} {trade.amount} has been received. "
    #     "If you have any further questions or need assistance, feel free to reach out. "
    #     "We appreciate your business!",
    #     reply_markup=review_menu(),
    #     parse_mode="html"
    # )

    # logger.info("Invoice payment webhook processed successfully")
    return True


def handle_payment_received_webhook(data):
    "Give alert message on new trade alert"
    trade = get_trade_by_invoice_id(data["invoiceId"])
    bot.send_message(
        ADMIN_ID,
        f"New payment received <b>{data['payment']['value']}</b> for Trade {trade.id}",
    )


def handle_invoice_expired_webhook(data):
    "Close trade when the payment url has expired (Send message to both parties)"
    trade = get_trade_by_invoice_id(data["invoiceId"])
    handle_invoice_expired(trade.invoice_id)

    if trade.buyer_id != None:
        # Notify the buyer that the trade has expired and is now closed
        bot.send_message(
            trade.buyer_id,
            f"📪 Trade <b>({trade.id})</b> has expired, and the transaction has been closed. If you have any questions or concerns, please reach out to the seller or our support team. Thank you for using our platform.",
            reply_markup=review_menu(),
            parse_mode="html",
        )

    # Notify the seller that the trade has expired and is now closed
    bot.send_message(
        trade.seller_id,
        f"📪 Trade <b>({trade.id})</b> has expired, and the transaction has been closed. If you have any questions or concerns, please reach out to the buyer or our support team. Thank you for using our platform.",
        reply_markup=review_menu(),
        parse_mode="html",
    )


def process_merchant_webhook(bot):
    data = request.get_json()
    try:
        event_type = data["type"]
        print(event_type)
        # logger.info(f"Webhook event from server merchant: {event_type}")

        if event_type == "InvoiceReceivedPayment":
            handle_payment_received_webhook(data)

        elif event_type in ["InvoicePaymentSettled", "InvoiceSettled"]:
            handle_invoice_paid_webhook(data)

        elif event_type == "InvoiceExpired":
            handle_invoice_expired_webhook(data)

    except UnsupportedMediaType:
        # logger.error('Unsupported Media Type: request payload must be in JSON format')
        return "Unsupported Media Type: request payload must be in JSON format", 200
    except Exception as e:
        print(e)
        # logger.error('Invalid request payload: missing required field')
        return "Invalid request payload: missing required field", 200
    return "", 200
