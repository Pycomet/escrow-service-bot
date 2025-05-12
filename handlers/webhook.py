from config import *
from functions import *
from utils import *
from telegram import Bot
from quart import request
import logging

logger = logging.getLogger(__name__)


async def handle_invoice_paid_webhook(data, bot: Bot):
    "Response to when the invoice has been paid"
    try:
        logger.info(f"Processing invoice paid webhook for invoice: {data['invoiceId']}")
        trade = TradeClient.get_trade_by_invoice_id(data["invoiceId"])
        
        if not trade:
            logger.error(f"No trade found for invoice ID: {data['invoiceId']}")
            return False
            
        TradeClient.handle_invoice_paid(data["invoiceId"])
        logger.info(f"Trade {trade['_id']} marked as paid")

        # Convert IDs to integers and validate
        try:
            seller_id = int(trade["seller_id"])
            buyer_id = int(trade["buyer_id"]) if trade.get("buyer_id") else None
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid user IDs in trade {trade['_id']}: {e}")
            return False

        if not seller_id:
            logger.error(f"No seller_id found for trade {trade['_id']}")
            return False

        # Notify the seller
        seller_notification = (
            f"🚀 Congratulations! Trade <b>({trade['_id']})</b> has been paid, and you're one step closer to completion. "
            "Please fulfill your agreed terms, and once done, request the buyer to approve the transaction on the bot. "
            "Upon approval, the payment will be released to you."
        )
        try:
            await bot.send_message(
                chat_id=seller_id,
                text=seller_notification,
                parse_mode="html",
                reply_markup=review_menu(),
            )
            logger.info(f"Sent payment notification to seller {seller_id}")
        except Exception as e:
            logger.error(f"Failed to send notification to seller {seller_id}: {e}")

        # Notify the buyer if available
        if buyer_id:
            approval_message = (
                f"🎉 Payment of <b>{trade['price']} {trade['currency']}</b> on trade <b>({trade['_id']})</b> has been successfully completed! "
                "Please review the terms of the trade and click the button below to approve the transaction. "
                "Your payment will be released to the seller upon approval."
            )
            try:
                await bot.send_message(
                    chat_id=buyer_id,
                    text=approval_message,
                    reply_markup=give_verdict(),
                    parse_mode="html",
                )
                logger.info(f"Sent approval request to buyer {buyer_id}")
            except Exception as e:
                logger.error(f"Failed to send notification to buyer {buyer_id}: {e}")

        # Send announcement to review channel
        try:
            completion_message = (
                f"🎉 New Trade Completed! <b>{trade['_id']}</b> \n\n"
                "✅ The trade has been successfully completed. Buyers and sellers have been notified.\n"
                "Thank you for using our platform!"
            )
            await bot.send_message(
                chat_id="@trusted_escrow_bot_reviews",
                text=completion_message,
                parse_mode="html",
                disable_web_page_preview=True,
            )
            logger.info("Trade completion announcement sent to review channel")
        except Exception as e:
            logger.error(f"Failed to send announcement to review channel: {e}")

        return True
        
    except Exception as e:
        logger.error(f"Error in handle_invoice_paid_webhook: {e}", exc_info=True)
        return False


async def handle_payment_received_webhook(data, bot: Bot):
    "Give alert message on new trade alert"
    logger.info(f"Processing payment received webhook for invoice: {data['invoiceId']}")
    trade = TradeClient.get_trade_by_invoice_id(data["invoiceId"])
    if not trade:
        logger.error(f"No trade found for invoice ID: {data['invoiceId']}")
        return
        
    logging.info(f"Trade Data From Webhook: {data}")
    trade_id = trade.get('_id') if isinstance(trade, dict) else getattr(trade, '_id', None)
    if not trade_id:
        logger.error(f"Could not get trade ID from trade object: {trade}")
        return
        
    await bot.send_message(
        chat_id=ADMIN_ID,
        text=f"New payment received for Trade {trade_id}",
        parse_mode="html"
    )
    logger.info(f"Payment received notification sent to admin for trade {trade_id}")


async def handle_invoice_expired_webhook(data, bot: Bot):
    "Close trade when the payment url has expired (Send message to both parties)"
    logger.info(f"Processing invoice expired webhook for invoice: {data['invoiceId']}")
    trade = TradeClient.get_trade_by_invoice_id(data["invoiceId"])
    TradeClient.handle_invoice_expired(trade["invoice_id"])
    logger.info(f"Trade {trade['_id']} marked as expired")

    if trade["buyer_id"] != None:
        # Notify the buyer that the trade has expired and is now closed
        await bot.send_message(
            chat_id=trade["buyer_id"],
            text=f"📪 Trade <b>({trade['_id']})</b> has expired, and the transaction has been closed. If you have any questions or concerns, please reach out to the seller or our support team. Thank you for using our platform.",
            reply_markup=review_menu(),
            parse_mode="html",
        )
        logger.info(f"Expiration notification sent to buyer {trade['buyer_id']}")

    # Notify the seller that the trade has expired and is now closed
    await bot.send_message(
        chat_id=trade["seller_id"],
        text=f"📪 Trade <b>({trade['_id']})</b> has expired, and the transaction has been closed. If you have any questions or concerns, please reach out to the buyer or our support team. Thank you for using our platform.",
        reply_markup=review_menu(),
        parse_mode="html",
    )
    logger.info(f"Expiration notification sent to seller {trade['seller_id']}")


async def process_merchant_webhook(bot: Bot):
    try:
        data = await request.get_json()
        logger.info(f"Received merchant webhook: {data}")
        
        event_type = data["type"]
        logger.info(f"Processing webhook event type: {event_type}")

        if event_type == "InvoiceReceivedPayment":
            await handle_payment_received_webhook(data, bot)
            logger.info("Successfully processed InvoiceReceivedPayment webhook")

        elif event_type in ["InvoicePaymentSettled", "InvoiceSettled"]:
            await handle_invoice_paid_webhook(data, bot)
            logger.info("Successfully processed InvoicePaymentSettled/InvoiceSettled webhook")

        elif event_type == "InvoiceExpired":
            await handle_invoice_expired_webhook(data, bot)
            logger.info("Successfully processed InvoiceExpired webhook")
        else:
            logger.warning(f"Received unknown webhook event type: {event_type}")

    except Exception as e:
        logger.error(f"Error processing merchant webhook: {e}", exc_info=True)
        return f"Error: {str(e)}", 500
    
    return "Webhook processed successfully", 200
