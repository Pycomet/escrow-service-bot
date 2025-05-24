####ADMIN JUDGEMENT ON TRADE
from config import *
from utils import *
from functions import *
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler

# Store trade in context instead of global variable
async def start_dispute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    "Starts The Ticket Review Session"

    if update.message.from_user.id == ADMIN_ID:
        question = await context.bot.send_message(chat_id=ADMIN_ID, text="What is the Dispute ID !")

        context.user_data["next_step"] = call_dispute

    else:
        await update.message.reply_text(text="You are not authorised for this command")


async def call_dispute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send The Verdict To Buyer And Seller"""

    dispute_id = update.message.text

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=emoji.emojize(
            f":warning: Please resolve dispute {dispute_id}",
        ),
    )


    await context.bot.send_message(
        chat_id=update.message.from_user.id,
        text=emoji.emojize(
            ":warning: Feature currently unavailable!",
        ),
    )

#     dispute = get_dispute_by_id(dispute_id)
#     keyboard = give_verdict()

#     if dispute != None:
#         # Store trade in context for later use
#         context.user_data["trade"] = dispute.trade
#         trade = dispute.trade

#         await context.bot.send_message(
#             chat_id=update.message.from_user.id,
#             text=emoji.emojize(
#                 f"""
# :ticket: <b>Dispute Ticket -- {dispute.id}</b>
# ----------------------
# Complaint --> {dispute.complaint}


# Trade Info;
# -------------
# <b>ID --> {trade.id}</b>
# <b>Seller ID --> {trade.seller}</b>
# <b>Buyer ID --> {trade.buyer}</b>
# <b>Price --> {trade.price} {trade.currency}</b>
# <b>Preferred method of payment --> {trade.coin}</b>
# <b>Created on --> {trade.created_at}</b>
# <b>Payment Status --> {trade.payment_status}</b>
# <b>Is Open --> {trade.is_open}</b>

# Give verdict :grey_question:
#                 """,
#             ),
#             reply_markup=keyboard,
#             parse_mode="html",
#         )

#     else:
#         await context.bot.send_message(
#             chat_id=update.message.from_user.id,
#             text=emoji.emojize(
#                 ":warning: Dispute Not Found!",
#             ),
#         )


async def pass_verdict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """This Would Send The Admin Verdict To Both Parties Of The Trade"""
    message = update.message.text
    
    # Get trade from context
    trade = context.user_data.get("trade")
    if not trade:
        await context.bot.send_message(
            chat_id=update.message.from_user.id,
            text="Error: Trade information not found. Please start over."
        )
        return

    users = [
        trade.seller,
        trade.buyer,
        update.message.from_user.id,
    ]

    for user in users:

        await context.bot.send_message(
            chat_id=user,
            text=emoji.emojize(
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

    await context.bot.send_message(
        chat_id=update.message.from_user.id,
        text=emoji.emojize(
            "Who are you assigning payout to :grey_question:",
        ),
        reply_markup=refunds(),
    )


async def give_verdict_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the verdict from the buyer"""
    query = update.callback_query
    await query.answer()

    data = query.data.split("_")
    trade_id = data[1]
    verdict = data[2]

    trade = get_trade_by_id(trade_id)
    if not trade:
        await query.edit_message_text(
            text="❌ Trade not found. Please try again.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
            ]])
        )
        return

    if verdict == "approve":
        # Update trade status
        update_trade_status(trade_id, "completed")
        
        # Notify seller
        await context.bot.send_message(
            chat_id=trade["seller_id"],
            text=f"✅ Trade <b>({trade_id})</b> has been approved by the buyer. The payment has been released to you.",
            parse_mode="html"
        )
        
        # Notify buyer
        await query.edit_message_text(
            text=f"✅ You have approved trade <b>({trade_id})</b>. The payment has been released to the seller.",
            parse_mode="html",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
            ]])
        )
        
    elif verdict == "dispute":
        # Update trade status
        update_trade_status(trade_id, "disputed")
        
        # Notify seller
        await context.bot.send_message(
            chat_id=trade["seller_id"],
            text=f"⚠️ Trade <b>({trade_id})</b> has been disputed by the buyer. An admin will review the case.",
            parse_mode="html"
        )
        
        # Notify buyer
        await query.edit_message_text(
            text=f"⚠️ You have disputed trade <b>({trade_id})</b>. An admin will review your case.",
            parse_mode="html",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
            ]])
        )
        
        # Notify admin
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"⚠️ Trade <b>({trade_id})</b> has been disputed by the buyer. Please review the case.",
            parse_mode="html"
        )


def register_handlers(application):
    """Register handlers for the verdict module"""
    application.add_handler(CallbackQueryHandler(give_verdict_handler, pattern="^verdict_"))

# Register handlers
application.add_handler(CommandHandler("disputes", start_dispute))
