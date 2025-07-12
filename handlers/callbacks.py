import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ContextTypes

from config import *
from functions import *

# from handlers.initiate_trade import *
from handlers import *
from handlers.affiliate import affiliate_handler
from handlers.history import history_handler
from handlers.initiate_trade import initiate_trade_handler
from handlers.join import join_handler
from handlers.report import report_handler
from handlers.review import review_handler
from handlers.rules import community_rules_handler, rules_handler
from handlers.trade_flows.fiat import CryptoFiatFlow
from handlers.wallet import (
    wallet_balances_handler,
    wallet_create_handler,
    wallet_details_handler,
    wallet_handler,
    wallet_refresh_general_handler,
    wallet_refresh_handler,
    wallet_transactions_handler,
)
from utils import *
from utils.enums import CallbackDataEnums, EmojiEnums
from utils.keyboard import back_to_menu, main_menu, trade_type_menu
from utils.messages import Messages

# Configure logging
logger = logging.getLogger(__name__)


# Callback Handlers
async def handle_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle main menu navigation callbacks"""
    query = update.callback_query
    await query.answer()

    data = query.data
    logger.info(f"Menu callback received: {data}")

    try:
        if data == CallbackDataEnums.MENU.value:
            # Show main menu
            await query.edit_message_text(
                Messages.main_menu_welcome(),
                parse_mode="html",
                reply_markup=await main_menu(update, context),
            )

        elif data == CallbackDataEnums.CREATE_TRADE.value:
            # Start trade creation process using edit_message instead of expecting a reply_text
            logger.info("Starting trade creation process")
            user_id = update.effective_user.id

            # Check if user already has a trade creation in progress
            if context.user_data.get("trade_creation"):
                await query.edit_message_text(
                    Messages.trade_creation_in_progress(),
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

            # Check if user is already involved in an active trade
            active_trade = trades_db.get_active_trade_by_user_id(str(user_id))
            if active_trade:
                await query.edit_message_text(
                    Messages.active_trade_exists(active_trade["_id"]),
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

            # Start trade creation process - now ask for trade type first
            keyboard = await trade_type_menu()

            await query.edit_message_text(
                Messages.trade_creation_start(), reply_markup=keyboard
            )

            # Set state to wait for trade type selection
            context.user_data["trade_creation"] = {"step": "select_trade_type"}

        elif data == CallbackDataEnums.JOIN_TRADE.value:
            # Start trade joining process
            logger.info("Starting trade joining process")
            await join_handler(update, context)

        elif data == CallbackDataEnums.TRADE_HISTORY.value:
            # Show trade history
            logger.info("Showing trade history")
            await history_handler(update, context)

        elif data == CallbackDataEnums.MY_WALLETS.value:
            # Show wallet management
            logger.info("Showing wallet management")
            await wallet_handler(update, context)

        elif data == CallbackDataEnums.RULES.value:
            # Show rules
            logger.info("Showing rules")
            await rules_handler(update, context)

        elif data == CallbackDataEnums.COMMUNITY.value:
            # Show community links
            logger.info("Showing community links")
            await community_rules_handler(update, context)

        elif data == CallbackDataEnums.AFFILIATE.value:
            # Show affiliate program
            logger.info("Showing affiliate program")
            await affiliate_handler(update, context)

        elif data == CallbackDataEnums.SUPPORT.value:
            # Show support options
            logger.info("Showing support options")
            await query.edit_message_text(
                Messages.support_menu(),
                parse_mode="html",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "📝 Report an Issue", callback_data="report"
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                f"{EmojiEnums.QUESTION.value} FAQ", callback_data="faq"
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                "📞 Contact Support",
                                url=f"https://t.me/{SUPPORT_USERNAME}",
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                                callback_data=CallbackDataEnums.MENU.value,
                            )
                        ],
                    ]
                ),
            )

        elif data == "report":
            # Start report process
            logger.info("Starting report process")
            await report_handler(update, context)

        elif data == "faq":
            # Show FAQ
            logger.info("Showing FAQ")
            await query.edit_message_text(
                Messages.faq(),
                parse_mode="html",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                f"{EmojiEnums.BACK_ARROW.value} Back to Support",
                                callback_data=CallbackDataEnums.SUPPORT.value,
                            )
                        ]
                    ]
                ),
            )

    except Exception as e:
        logger.error(f"Error in menu callback: {e}")
        try:
            await query.edit_message_text(
                Messages.generic_error(), reply_markup=back_to_menu()
            )
        except Exception:
            pass


async def handle_deposit_check_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handle deposit check callbacks by routing to appropriate trade flow"""
    query = update.callback_query
    await query.answer()

    logger.info(f"Deposit check callback received: {query.data}")

    # Extract trade_id from callback_data
    if query.data and query.data.startswith("check_deposit_"):
        trade_id = query.data.split("_", 2)[-1]
        logger.info(f"Trade ID extracted: {trade_id}")

        # Get trade to determine type
        trade = TradeClient.get_trade(trade_id)
        if not trade:
            logger.error(f"Trade {trade_id} not found")
            await query.bot.send_message(
                query.message.chat_id, Messages.trade_not_found(trade_id)
            )
            return

        trade_type = trade.get("trade_type")
        logger.info(f"Trade type: {trade_type}")

        # Route to appropriate flow handler
        if trade_type == "CryptoToFiat":
            await CryptoFiatFlow.handle_deposit_check(update, context)
        else:
            logger.warning(f"No deposit check handler for trade type: {trade_type}")
            await query.bot.send_message(
                query.message.chat_id,
                Messages.deposit_check_not_implemented(trade_type),
            )
    else:
        logger.error(f"Invalid deposit check callback data: {query.data}")
        await query.bot.send_message(
            query.message.chat_id, Messages.invalid_deposit_check()
        )


async def handle_cancel_trade_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handle cancel trade callbacks"""
    query = update.callback_query
    await query.answer()

    logger.info(f"Cancel trade callback received: {query.data}")

    # Extract trade_id from callback_data
    if query.data and query.data.startswith("cancel_trade_"):
        trade_id = query.data.split("_", 2)[-1]
        logger.info(f"Cancelling trade ID: {trade_id}")

        # Get trade to verify ownership
        trade = TradeClient.get_trade(trade_id)
        if not trade:
            logger.error(f"Trade {trade_id} not found")
            await query.edit_message_text(
                Messages.trade_not_found(trade_id), reply_markup=back_to_menu()
            )
            return

        user_id = str(query.from_user.id)
        seller_id = trade.get("seller_id")
        buyer_id = trade.get("buyer_id")

        # Check if user is authorized to cancel
        if user_id not in [seller_id, buyer_id]:
            await query.edit_message_text(
                Messages.trade_cancel_not_authorized(trade_id),
                reply_markup=back_to_menu(),
            )
            return

        # Show confirmation dialog
        from utils.keyboard import confirmation_menu

        await query.edit_message_text(
            Messages.trade_cancel_confirmation(trade_id),
            parse_mode="html",
            reply_markup=confirmation_menu("cancel_trade", trade_id),
        )

    else:
        logger.error(f"Invalid cancel trade callback data: {query.data}")
        await query.edit_message_text(
            Messages.generic_error(), reply_markup=back_to_menu()
        )


async def handle_confirm_cancel_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handle confirmation of trade cancellation"""
    query = update.callback_query
    await query.answer()

    logger.info(f"Confirm cancel callback received: {query.data}")

    if query.data and query.data.startswith("confirm_cancel_trade_"):
        trade_id = query.data.split("_", 3)[-1]
        logger.info(f"Confirming cancellation of trade ID: {trade_id}")

        try:
            # Cancel the trade
            success = TradeClient.cancel_trade(
                trade_id=trade_id, user_id=str(query.from_user.id)
            )

            if success:
                await query.edit_message_text(
                    Messages.trade_cancelled_success(trade_id),
                    parse_mode="html",
                    reply_markup=back_to_menu(),
                )
            else:
                await query.edit_message_text(
                    Messages.trade_cancel_failed(trade_id),
                    parse_mode="html",
                    reply_markup=back_to_menu(),
                )

        except Exception as e:
            logger.error(f"Error cancelling trade {trade_id}: {e}")
            await query.edit_message_text(
                Messages.trade_cancel_failed(trade_id),
                parse_mode="html",
                reply_markup=back_to_menu(),
            )

    elif query.data and query.data.startswith("cancel_cancel_trade_"):
        # User cancelled the cancellation
        trade_id = query.data.split("_", 3)[-1]
        await query.edit_message_text(
            f"{EmojiEnums.CHECK_MARK.value} <b>Cancellation Aborted</b>\n\n"
            f"Trade #{trade_id} will continue as normal.",
            parse_mode="html",
            reply_markup=back_to_menu(),
        )


async def handle_support_trade_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handle support requests for specific trades"""
    query = update.callback_query
    await query.answer()

    logger.info(f"Support trade callback received: {query.data}")

    if query.data and query.data.startswith("support_trade_"):
        trade_id = query.data.split("_", 2)[-1]
        logger.info(f"Support requested for trade ID: {trade_id}")

        # Get trade to verify existence
        trade = TradeClient.get_trade(trade_id)
        if not trade:
            await query.edit_message_text(
                Messages.trade_not_found(trade_id), reply_markup=back_to_menu()
            )
            return

        # Show support options for this trade
        await query.edit_message_text(
            Messages.support_trade_options(trade_id),
            parse_mode="html",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🚨 Report Issue",
                            callback_data=f"report_trade_issue_{trade_id}",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "📞 Contact Support", url=f"https://t.me/{SUPPORT_USERNAME}"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "📝 Trade Details",
                            callback_data=f"trade_details_{trade_id}",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                            callback_data=CallbackDataEnums.MENU.value,
                        )
                    ],
                ]
            ),
        )


async def handle_trade_details_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handle trade details callback queries"""
    query = update.callback_query
    await query.answer()

    logger.info(f"Trade details callback received: {query.data}")

    if query.data and query.data.startswith("trade_details_"):
        trade_id = query.data.split("_", 2)[-1]
        logger.info(f"Trade details requested for trade ID: {trade_id}")

        # Get trade to verify existence and show details
        trade = TradeClient.get_trade(trade_id)
        if not trade:
            await query.edit_message_text(
                Messages.trade_not_found(trade_id), reply_markup=back_to_menu()
            )
            return

        # Get trade status for display
        from utils.trade_status import format_trade_status, get_trade_status

        status, status_emoji = get_trade_status(trade)
        formatted_status = format_trade_status(status)

        # Show detailed trade information using the Messages.trade_details function
        await query.edit_message_text(
            Messages.trade_details(trade, formatted_status),
            parse_mode="html",
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


async def handle_payment_review_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handle payment review callbacks by routing to appropriate trade flow"""
    await CryptoFiatFlow.handle_seller_payment_review(update, context)


async def handle_broker_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle broker-related callbacks in trade creation flow"""
    query = update.callback_query
    await query.answer()

    logger.info(f"Broker callback received: {query.data}")

    # Explicitly exclude cancel_creation callbacks - these should be handled by initiate_trade.py
    if query.data == "cancel_creation":
        logger.info(
            "Broker callback handler: Ignoring cancel_creation callback - should be handled by initiate_trade.py"
        )
        return

    # Check if we're in a trade creation flow
    if not context.user_data or "trade_creation" not in context.user_data:
        logger.warning("Broker callback received but no trade creation in progress")
        await query.edit_message_text(
            "❌ No active trade creation process found. Please start a new trade with /trade.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🆕 Start New Trade", callback_data="create_trade"
                        ),
                        InlineKeyboardButton("🔙 Back to Menu", callback_data="menu"),
                    ]
                ]
            ),
        )
        return

    # Route broker callbacks to the trade flow dispatcher
    from handlers.initiate_trade import dispatch_to_flow

    await dispatch_to_flow(update, context)


def register_handlers(application):
    """Register all callback handlers"""
    # Menu navigation callbacks
    application.add_handler(
        CallbackQueryHandler(
            handle_menu_callback,
            pattern="^(menu|create_trade|join_trade|trade_history|my_wallets|rules|community|affiliate|support|report|faq)$",
        )
    )

    # Broker callbacks - NEW
    application.add_handler(
        CallbackQueryHandler(
            handle_broker_callbacks, pattern="^(broker_yes|broker_no|select_broker_)"
        )
    )

    # Wallet callbacks
    application.add_handler(
        CallbackQueryHandler(wallet_handler, pattern=CallbackDataEnums.MY_WALLETS.value)
    )
    application.add_handler(
        CallbackQueryHandler(
            wallet_create_handler, pattern=CallbackDataEnums.WALLET_CREATE.value
        )
    )
    application.add_handler(
        CallbackQueryHandler(wallet_refresh_handler, pattern="^wallet_refresh_")
    )
    application.add_handler(
        CallbackQueryHandler(wallet_details_handler, pattern="^wallet_details_")
    )
    application.add_handler(
        CallbackQueryHandler(
            wallet_balances_handler, pattern=CallbackDataEnums.WALLET_BALANCES.value
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            wallet_refresh_general_handler,
            pattern=CallbackDataEnums.WALLET_REFRESH.value,
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            wallet_transactions_handler,
            pattern=CallbackDataEnums.WALLET_TRANSACTIONS.value,
        )
    )

    # Trade action callbacks
    application.add_handler(
        CallbackQueryHandler(handle_deposit_check_callback, pattern="^check_deposit_")
    )
    application.add_handler(
        CallbackQueryHandler(handle_cancel_trade_callback, pattern="^cancel_trade_")
    )
    application.add_handler(
        CallbackQueryHandler(
            handle_confirm_cancel_callback,
            pattern="^(confirm_cancel_trade_|cancel_cancel_trade_)",
        )
    )
    application.add_handler(
        CallbackQueryHandler(handle_support_trade_callback, pattern="^support_trade_")
    )

    # Trade details callback
    application.add_handler(
        CallbackQueryHandler(handle_trade_details_callback, pattern="^trade_details_")
    )

    # Payment review callbacks for CryptoToFiat trades
    application.add_handler(
        CallbackQueryHandler(
            handle_payment_review_callback,
            pattern="^(review_proof_|approve_payment_|reject_payment_)",
        )
    )

    logger.info("Callback handlers registered successfully")
