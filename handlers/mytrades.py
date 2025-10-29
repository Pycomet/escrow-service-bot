import logging
from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from functions.trade import TradeClient
from utils.enums import CallbackDataEnums, EmojiEnums
from utils.messages import Messages

logger = logging.getLogger(__name__)


def format_trade_age(created_at: datetime) -> str:
    """
    Format the age of a trade in a human-readable format.

    Args:
        created_at: Trade creation datetime

    Returns:
        Human-readable time string (e.g., "2h ago", "3d ago")
    """
    now = datetime.now()
    delta = now - created_at

    if delta.days > 0:
        return f"{delta.days}d ago"
    elif delta.seconds >= 3600:
        hours = delta.seconds // 3600
        return f"{hours}h ago"
    elif delta.seconds >= 60:
        minutes = delta.seconds // 60
        return f"{minutes}m ago"
    else:
        return "just now"


async def mytrades_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /mytrades command - show all active trades for the user."""
    user_id = str(update.effective_user.id)

    logger.info(f"mytrades_handler called for user {user_id}")

    try:
        # Get all active trades for this user
        active_trades = TradeClient.get_active_trades_for_user(user_id)

        if not active_trades:
            # No active trades found
            message = (
                f"{EmojiEnums.INFO.value} <b>No Active Trades</b>\n\n"
                f"You don't have any active trades at the moment.\n\n"
                f"Ready to start a new trade?"
            )
            keyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            f"{EmojiEnums.MONEY_BAG.value} Create New Trade",
                            callback_data=CallbackDataEnums.CREATE_TRADE.value,
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            f"{EmojiEnums.SCROLL.value} Trade History",
                            callback_data=CallbackDataEnums.TRADE_HISTORY.value,
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                            callback_data=CallbackDataEnums.MENU.value,
                        )
                    ],
                ]
            )

            await update.message.reply_text(
                message, parse_mode="HTML", reply_markup=keyboard
            )
            return

        # Build message with all active trades
        message_parts = [
            f"{EmojiEnums.SCROLL.value} <b>Your Active Trades</b>\n",
            f"You have <b>{len(active_trades)}</b> active trade(s):\n",
        ]

        keyboard_buttons = []

        for i, trade in enumerate(active_trades, 1):
            trade_id = trade["_id"]
            amount = trade.get("price", 0)
            currency = trade.get("currency", "USD")
            seller_id = str(trade.get("seller_id", ""))
            buyer_id = str(trade.get("buyer_id", ""))
            status = trade.get("status", "active")
            created_at = trade.get("created_at", datetime.now())
            trade_age = format_trade_age(created_at)

            # Determine user role
            if seller_id == user_id:
                role_icon = "📤"
                role = "Seller"
            elif buyer_id == user_id:
                role_icon = "📥"
                role = "Buyer"
            else:
                role_icon = "❓"
                role = "Unknown"

            # Add trade summary to message
            message_parts.append(
                f"\n{i}. {role_icon} <b>Trade #{trade_id[:8]}</b>\n"
                f"   • Role: {role}\n"
                f"   • Amount: {amount} {currency}\n"
                f"   • Status: {status}\n"
                f"   • Created: {trade_age}"
            )

            # Add action buttons for each trade
            keyboard_buttons.append(
                [
                    InlineKeyboardButton(
                        f"{role_icon} View #{trade_id[:8]}",
                        callback_data=f"mytrade_view_{trade_id}",
                    )
                ]
            )

        # Add navigation buttons
        keyboard_buttons.extend(
            [
                [
                    InlineKeyboardButton(
                        f"{EmojiEnums.SCROLL.value} Full History",
                        callback_data=CallbackDataEnums.TRADE_HISTORY.value,
                    )
                ],
                [
                    InlineKeyboardButton(
                        f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                        callback_data=CallbackDataEnums.MENU.value,
                    )
                ],
            ]
        )

        keyboard = InlineKeyboardMarkup(keyboard_buttons)

        message = "\n".join(message_parts)

        await update.message.reply_text(
            message, parse_mode="HTML", reply_markup=keyboard
        )

    except Exception as e:
        logger.error(f"Error in mytrades_handler: {e}")
        await update.message.reply_text(
            Messages.generic_error(),
            parse_mode="HTML",
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


async def mytrades_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callbacks from the mytrades view."""
    query = update.callback_query
    await query.answer()

    user_id = str(update.effective_user.id)
    callback_data = query.data

    logger.info(f"mytrades_callback_handler: {callback_data} for user {user_id}")

    try:
        if callback_data == "my_trades":
            # Show all active trades (same as /mytrades command)
            active_trades = TradeClient.get_active_trades_for_user(user_id)

            if not active_trades:
                message = (
                    f"{EmojiEnums.INFO.value} <b>No Active Trades</b>\n\n"
                    f"You don't have any active trades at the moment.\n\n"
                    f"Ready to start a new trade?"
                )
                keyboard = InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                f"{EmojiEnums.MONEY_BAG.value} Create New Trade",
                                callback_data=CallbackDataEnums.CREATE_TRADE.value,
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                f"{EmojiEnums.SCROLL.value} Trade History",
                                callback_data=CallbackDataEnums.TRADE_HISTORY.value,
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                                callback_data=CallbackDataEnums.MENU.value,
                            )
                        ],
                    ]
                )

                await query.edit_message_text(
                    message, parse_mode="HTML", reply_markup=keyboard
                )
                return

            # Build message with all active trades
            message_parts = [
                f"{EmojiEnums.SCROLL.value} <b>Your Active Trades</b>\n",
                f"You have <b>{len(active_trades)}</b> active trade(s):\n",
            ]

            keyboard_buttons = []

            for i, trade in enumerate(active_trades, 1):
                trade_id = trade["_id"]
                amount = trade.get("price", 0)
                currency = trade.get("currency", "USD")
                seller_id = str(trade.get("seller_id", ""))
                buyer_id = str(trade.get("buyer_id", ""))
                status = trade.get("status", "active")
                created_at = trade.get("created_at", datetime.now())
                trade_age = format_trade_age(created_at)

                # Determine user role
                if seller_id == user_id:
                    role_icon = "📤"
                    role = "Seller"
                elif buyer_id == user_id:
                    role_icon = "📥"
                    role = "Buyer"
                else:
                    role_icon = "❓"
                    role = "Unknown"

                # Add trade summary to message
                message_parts.append(
                    f"\n{i}. {role_icon} <b>Trade #{trade_id[:8]}</b>\n"
                    f"   • Role: {role}\n"
                    f"   • Amount: {amount} {currency}\n"
                    f"   • Status: {status}\n"
                    f"   • Created: {trade_age}"
                )

                # Add action buttons for each trade
                keyboard_buttons.append(
                    [
                        InlineKeyboardButton(
                            f"{role_icon} View #{trade_id[:8]}",
                            callback_data=f"mytrade_view_{trade_id}",
                        )
                    ]
                )

            # Add navigation buttons
            keyboard_buttons.extend(
                [
                    [
                        InlineKeyboardButton(
                            f"{EmojiEnums.SCROLL.value} Full History",
                            callback_data=CallbackDataEnums.TRADE_HISTORY.value,
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                            callback_data=CallbackDataEnums.MENU.value,
                        )
                    ],
                ]
            )

            keyboard = InlineKeyboardMarkup(keyboard_buttons)
            message = "\n".join(message_parts)

            await query.edit_message_text(
                message, parse_mode="HTML", reply_markup=keyboard
            )

        elif callback_data.startswith("mytrade_view_"):
            # View specific trade details
            trade_id = callback_data.replace("mytrade_view_", "")
            trade = TradeClient.get_trade(trade_id)

            if not trade:
                await query.edit_message_text(
                    Messages.trade_not_found(trade_id),
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    f"{EmojiEnums.BACK_ARROW.value} Back",
                                    callback_data="my_trades",
                                )
                            ]
                        ]
                    ),
                )
                return

            # Verify user has access to this trade
            seller_id = str(trade.get("seller_id", ""))
            buyer_id = str(trade.get("buyer_id", ""))

            if user_id not in [seller_id, buyer_id]:
                await query.edit_message_text(
                    Messages.access_denied(),
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    f"{EmojiEnums.BACK_ARROW.value} Back",
                                    callback_data="my_trades",
                                )
                            ]
                        ]
                    ),
                )
                return

            # Get trade status
            from utils.trade_status import format_trade_status, get_trade_status

            status, status_emoji = get_trade_status(trade)
            formatted_status = format_trade_status(status)

            # Determine user role
            if seller_id == user_id:
                role_icon = "📤"
                role = "Seller"
            elif buyer_id == user_id:
                role_icon = "📥"
                role = "Buyer"
            else:
                role_icon = "❓"
                role = "Unknown"

            # Show detailed trade information
            message = Messages.trade_details(trade, formatted_status)

            # Add role information
            message += f"\n{role_icon} <b>Your Role:</b> {role}"

            # Build action buttons based on role and trade status
            keyboard_buttons = []

            # Add refresh button
            keyboard_buttons.append(
                [
                    InlineKeyboardButton(
                        f"{EmojiEnums.REFRESH.value} Refresh",
                        callback_data=f"mytrade_view_{trade_id}",
                    )
                ]
            )

            # Add cancel trade button if trade is active
            if trade.get("is_active", False):
                keyboard_buttons.append(
                    [
                        InlineKeyboardButton(
                            f"{EmojiEnums.CROSS_MARK.value} Cancel Trade",
                            callback_data=f"cancel_trade_{trade_id}",
                        )
                    ]
                )

            # Add support button
            keyboard_buttons.append(
                [
                    InlineKeyboardButton(
                        f"{EmojiEnums.QUESTION.value} Get Support",
                        callback_data=f"support_trade_{trade_id}",
                    )
                ]
            )

            # Add navigation buttons
            keyboard_buttons.append(
                [
                    InlineKeyboardButton(
                        f"{EmojiEnums.BACK_ARROW.value} Back to My Trades",
                        callback_data="my_trades",
                    )
                ]
            )

            keyboard = InlineKeyboardMarkup(keyboard_buttons)

            await query.edit_message_text(
                message, parse_mode="HTML", reply_markup=keyboard
            )

    except Exception as e:
        logger.error(f"Error in mytrades_callback_handler: {e}")
        await query.edit_message_text(
            Messages.generic_error(),
            parse_mode="HTML",
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


def register_handlers(application):
    """Register mytrades handlers."""
    # Command handler for /mytrades
    application.add_handler(CommandHandler("mytrades", mytrades_handler))

    # Callback query handlers for mytrades
    application.add_handler(
        CallbackQueryHandler(mytrades_callback_handler, pattern="^my_trades$")
    )
    application.add_handler(
        CallbackQueryHandler(mytrades_callback_handler, pattern="^mytrade_view_")
    )

    logger.info("MyTrades handlers registered successfully")
