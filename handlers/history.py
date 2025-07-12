import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from config import *
from functions import *
from functions.trade import TradeClient
from functions.user import UserClient
from utils import *
from utils.enums import CallbackDataEnums, EmojiEnums
from utils.messages import Messages
from utils.trade_status import format_trade_status, get_trade_status

logger = logging.getLogger(__name__)


async def send_message_or_edit(
    message, text, reply_markup, is_callback=False, parse_mode=None
):
    """Helper function to either send a new message or edit existing one"""
    try:
        if is_callback:
            return await message.edit_text(
                text, reply_markup=reply_markup, parse_mode=parse_mode
            )
        else:
            return await message.reply_text(
                text, reply_markup=reply_markup, parse_mode=parse_mode
            )
    except Exception as e:
        logger.error(f"Error in send_message_or_edit: {e}")
        raise


async def history_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /history command"""
    try:
        user_id = str(update.effective_user.id)
        is_callback = bool(update.callback_query)
        message = update.callback_query.message if is_callback else update.message

        if is_callback:
            await update.callback_query.answer()

        logger.info(f"User ID: {user_id}")

        # Get user's trades
        trades = trades_db.get_trades(user_id)
        if not trades:
            await send_message_or_edit(
                message,
                f"{EmojiEnums.CROSS_MARK.value} You don't have any trade history yet.",
                InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                                callback_data=CallbackDataEnums.MENU.value,
                            )
                        ]
                    ]
                ),
                is_callback,
            )
            return

        # Create keyboard with trade options
        keyboard = []
        # Convert trades to list if it's not already
        trades_list = list(trades) if not isinstance(trades, list) else trades
        logger.info(f"Trades: {trades_list}")

        for trade in trades_list[:5]:  # Limit to 5 most recent trades
            logger.info(trade)
            try:
                # Handle both dictionary and list formats
                if isinstance(trade, dict):
                    trade_id = str(trade.get("_id", ""))
                    amount = str(trade.get("price", "0"))
                    currency = str(trade.get("currency", "Unknown"))
                    status, status_emoji = get_trade_status(trade)
                else:
                    # Assuming trade is a list with ordered values
                    trade_id = str(trade[0]) if len(trade) > 0 else ""
                    amount = str(trade[1]) if len(trade) > 1 else "0"
                    currency = str(trade[2]) if len(trade) > 2 else "Unknown"
                    # For list format, we'll use a simple pending/completed status
                    status = "completed" if len(trade) > 3 and trade[3] else "pending"
                    status_emoji = (
                        EmojiEnums.CHECK_MARK.value
                        if status == "completed"
                        else EmojiEnums.HOURGLASS.value
                    )

                keyboard.append(
                    [
                        InlineKeyboardButton(
                            f"{status_emoji} Trade #{trade_id} - {amount} {currency}",
                            callback_data=f"view_trade_{trade_id}",
                        )
                    ]
                )
            except Exception as e:
                logger.error(f"Error processing trade in history: {e}")
                continue

        keyboard.append(
            [
                InlineKeyboardButton(
                    f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                    callback_data=CallbackDataEnums.MENU.value,
                )
            ]
        )

        await send_message_or_edit(
            message,
            f"{EmojiEnums.CLIPBOARD.value} Your Trade History:\n\nSelect a trade to view details:",
            InlineKeyboardMarkup(keyboard),
            is_callback,
        )

    except Exception as e:
        logger.error(f"Error in history handler: {e}")
        # Try to send error message
        try:
            message = (
                update.callback_query.message
                if update.callback_query
                else update.message
            )
            if message:
                await send_message_or_edit(
                    message,
                    f"{EmojiEnums.CROSS_MARK.value} An error occurred while fetching your trade history. Please try again later.",
                    InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                                    callback_data=CallbackDataEnums.MENU.value,
                                )
                            ]
                        ]
                    ),
                    bool(update.callback_query),
                )
        except Exception as e2:
            logger.error(f"Error sending error message: {e2}")


async def handle_trade_view_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handle trade view callback queries"""
    try:
        query = update.callback_query
        await query.answer()

        data = query.data

        if data.startswith("view_trade_"):
            trade_id = data.replace("view_trade_", "")
            logger.info(f"Trade ID: {trade_id}")
            trade = trades_db.get_trade(trade_id)

            if not trade:
                await query.message.edit_text(
                    f"{EmojiEnums.CROSS_MARK.value} Trade not found. Please try again.",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                                    callback_data=CallbackDataEnums.MENU.value,
                                )
                            ]
                        ]
                    ),
                )
                return

            # Get trade status and emoji
            status, status_emoji = get_trade_status(trade)
            formatted_status = format_trade_status(status)

            details = (
                f"{EmojiEnums.CLIPBOARD.value} <b>Trade Details</b>\n\n"
                f"ID: <code>{trade.get('_id', 'Unknown')}</code>\n"
                f"Type: {trade.get('trade_type', 'Unknown')}\n"
                f"Status: {status_emoji} {formatted_status}\n"
                f"Amount: {trade.get('price', '0')} {trade.get('currency', 'Unknown')}\n"
                f"Created: {trade.get('created_at', 'Unknown')}\n"
                f"Updated: {trade.get('updated_at', 'Unknown')}\n\n"
            )

            if trade.get("description"):
                details += f"Description: {trade['description']}\n\n"

            # Add action buttons based on trade status
            keyboard = [
                [
                    InlineKeyboardButton(
                        f"{EmojiEnums.BACK_ARROW.value} Back to History",
                        callback_data="history",
                    )
                ]
            ]

            # Only show action buttons for non-completed trades
            if status not in ["completed", "cancelled"]:
                if str(trade.get("seller_id")) == str(query.from_user.id):
                    keyboard.append(
                        [
                            InlineKeyboardButton(
                                f"{EmojiEnums.CROSS_MARK.value} Cancel Trade",
                                callback_data=f"delete_trade_{trade_id}",
                            )
                        ]
                    )
                elif str(trade.get("buyer_id")) == str(query.from_user.id):
                    keyboard.append(
                        [
                            InlineKeyboardButton(
                                f"{EmojiEnums.WARNING.value} Report Issue",
                                callback_data=f"report_trade_{trade_id}",
                            )
                        ]
                    )

            await query.message.edit_text(
                details, parse_mode="html", reply_markup=InlineKeyboardMarkup(keyboard)
            )

        elif data == "history":
            # Return to history menu
            await history_handler(update, context)

    except Exception as e:
        logger.error(f"Error in trade view callback: {e}")
        try:
            if query and query.message:
                await query.message.edit_text(
                    f"{EmojiEnums.CROSS_MARK.value} An error occurred while viewing trade details. Please try again later.",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                                    callback_data=CallbackDataEnums.MENU.value,
                                )
                            ]
                        ]
                    ),
                )
        except Exception as e2:
            logger.error(f"Error sending error message: {e2}")


def register_handlers(application):
    """Register handlers for the history module"""
    application.add_handler(CommandHandler("history", history_handler))
    application.add_handler(
        CallbackQueryHandler(
            handle_trade_view_callback, pattern="^(view_trade_|history)"
        )
    )
