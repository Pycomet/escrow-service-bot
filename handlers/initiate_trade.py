import logging

from telegram import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from config import *
from config import db
from functions import *
from functions.trade import TradeClient
from functions.user import UserClient
from handlers.trade_flows import TradeFlowHandler

# Import flow classes and their specific state constants
from handlers.trade_flows.fiat import (
    AWAITING_AMOUNT,
    AWAITING_BROKER_CHOICE,
    AWAITING_BROKER_SELECTION,
    AWAITING_CURRENCY,
    AWAITING_DESCRIPTION,
    CryptoFiatFlow,
)
from utils import *
from utils.enums import CallbackDataEnums, EmojiEnums, TradeTypeEnums
from utils.keyboard import trade_type_menu
from utils.messages import Messages

# from handlers.trade_flows.crypto import CryptoCryptoFlow # etc.
# from handlers.trade_flows.product import CryptoProductFlow
# from handlers.trade_flows.market import MarketShopFlow

logger = logging.getLogger(__name__)


##############TRADE CREATION
async def initiate_trade_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /trade command"""
    user_id = update.effective_user.id

    if context.user_data.get("trade_creation"):
        await update.message.reply_text(
            f"⚠️ <b>Trade Creation In Progress</b>\n\n"
            f"You already have a trade creation process active.\n\n"
            f"Options:\n"
            f"• Continue with current creation\n"
            f"• Use /cancel to abort and start over\n"
            f"• Use /status to see current state",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "❌ Cancel Current Process", callback_data="cancel_creation"
                        ),
                        InlineKeyboardButton(
                            f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                            callback_data=CallbackDataEnums.MENU.value,
                        ),
                    ]
                ]
            ),
        )
        return

    user_obj = UserClient.get_user(update.message)
    if user_obj:
        active_trade = TradeClient.get_most_recent_trade(user_obj)

        # Enhanced debug logging
        if active_trade:
            logging.info(
                f"DEBUG: User {user_id} most recent trade found: {active_trade.get('_id')}"
            )
            logging.info(f"DEBUG: Trade is_active: {active_trade.get('is_active')}")
            logging.info(
                f"DEBUG: Trade is_cancelled: {active_trade.get('is_cancelled')}"
            )
            logging.info(
                f"DEBUG: Trade is_completed: {active_trade.get('is_completed')}"
            )
            logging.info(f"DEBUG: Trade status: {active_trade.get('status')}")
            logging.info(f"DEBUG: Full trade data: {active_trade}")
        else:
            logging.info(f"DEBUG: User {user_id} has no recent trades")

        if active_trade and active_trade.get("is_active", False):
            # Get all active trades for this user
            all_active_trades = TradeClient.get_active_trades_for_user(str(user_id))
            trade_count = len(all_active_trades)

            # Log detailed debug info (not shown to user)
            logging.info(f"DEBUG: User {user_id} has {trade_count} active trade(s)")
            logging.info(f"DEBUG: Most recent trade: {active_trade.get('_id')}")
            logging.info(f"DEBUG: Trade is_active: {active_trade.get('is_active')}")
            logging.info(f"DEBUG: Trade status: {active_trade.get('status')}")

            # Show concise user-friendly message
            await update.message.reply_text(
                f"⚠️ <b>Active Trade Exists</b>\n\n"
                f"You currently have <b>{trade_count}</b> active trade(s).\n\n"
                f"Please complete or cancel your existing trade(s) before creating a new one.\n\n"
                f"<b>What you can do:</b>\n"
                f"• View all your active trades\n"
                f"• Complete ongoing trades\n"
                f"• Cancel trades if no longer needed",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "📊 View My Trades",
                                callback_data="my_trades",
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
            return
    else:
        logging.warning(f"User not found for ID {user_id} in initiate_trade_handler")

    keyboard = await trade_type_menu()
    await update.message.reply_text(
        "📝 Let's create a new trade!\n\n"
        "Please select the type of trade you want to create:",
        reply_markup=keyboard,
    )

    context.user_data["trade_creation"] = {"step": "select_trade_type"}


async def handle_trade_type_selection(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handle the trade type selection callback"""
    query = update.callback_query
    await query.answer()

    if (
        not context.user_data.get("trade_creation", {}).get("step")
        == "select_trade_type"
    ):
        await query.message.edit_text(
            f"{EmojiEnums.CROSS_MARK.value} Something went wrong. Please start over with /trade",
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

    trade_type_value = query.data.replace("trade_type_", "")

    valid_enum_values = [e.value for e in TradeTypeEnums]
    if trade_type_value == "Disabled":
        await query.message.edit_text(
            f"{EmojiEnums.CROSS_MARK.value} This feature is currently not available, will be back active soon!",
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
    elif trade_type_value not in valid_enum_values:
        await query.message.edit_text(
            f"{EmojiEnums.CROSS_MARK.value} Invalid trade type selected. Please start over with /trade",
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
        context.user_data.pop("trade_creation", None)
        return

    context.user_data["trade_creation"]["trade_type"] = trade_type_value
    context.user_data["trade_creation"]["step"] = "flow_initiated"

    logging.info(f"Trade type {trade_type_value} selected. Initiating flow setup.")

    success = await TradeFlowHandler.initiate_flow_setup(
        update, context, trade_type_value
    )

    if not success:
        logging.error(f"Trade flow setup failed for type: {trade_type_value}")
        try:
            await query.edit_message_text(
                f"{EmojiEnums.CROSS_MARK.value} Failed to start trade setup. Please try again or contact support.",
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
        except Exception as e:
            logging.error(f"Error editing message after flow setup failure: {e}")
        context.user_data.pop("trade_creation", None)


async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the current trade creation process or handle active trades"""
    user_id = str(update.effective_user.id)

    # Add debug logging for cancel_creation callbacks
    if update.callback_query and update.callback_query.data == "cancel_creation":
        logging.info(
            f"CANCEL_DEBUG: cancel_creation callback received for user {user_id}"
        )

    # Get the message object correctly for both callback queries and regular messages
    message = update.callback_query.message if update.callback_query else update.message
    user_obj = UserClient.get_user(message)

    # Check for trade creation process
    has_trade_creation = "trade_creation" in context.user_data
    logging.info(
        f"DEBUG CANCEL: User {user_id} has_trade_creation: {has_trade_creation}"
    )

    # Check for active database trades
    active_trade = None
    if user_obj:
        active_trade = TradeClient.get_most_recent_trade(user_obj)
        if active_trade:
            logging.info(
                f"DEBUG CANCEL: User {user_id} most recent trade: {active_trade.get('_id')}"
            )
            logging.info(
                f"DEBUG CANCEL: Trade is_active: {active_trade.get('is_active')}"
            )
            logging.info(
                f"DEBUG CANCEL: Trade is_cancelled: {active_trade.get('is_cancelled')}"
            )
            logging.info(
                f"DEBUG CANCEL: Trade is_completed: {active_trade.get('is_completed')}"
            )

            if not active_trade.get("is_active", False):
                logging.info(
                    f"DEBUG CANCEL: Trade {active_trade.get('_id')} is not active, setting to None"
                )
                active_trade = None  # Not actually active
        else:
            logging.info(f"DEBUG CANCEL: User {user_id} has no recent trades")
    else:
        logging.info(f"DEBUG CANCEL: User object not found for {user_id}")

    if has_trade_creation and active_trade:
        # Both exist - offer options
        context.user_data.pop("trade_creation")
        message_text = (
            f"🔄 <b>Multiple Trade States Found</b>\n\n"
            f"✅ Cancelled trade creation process\n"
            f"⚠️ You also have an active trade: #{active_trade['_id']}\n\n"
            f"Choose what you'd like to do:"
        )
        reply_markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🗑️ Cancel Active Trade",
                        callback_data=f"cancel_trade_{active_trade['_id']}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "📊 View Trade Details",
                        callback_data=f"view_trade_{active_trade['_id']}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🆕 Start New Trade", callback_data="create_trade"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🏡 Main Menu", callback_data=CallbackDataEnums.MENU.value
                    )
                ],
            ]
        )

    elif has_trade_creation:
        # Only trade creation process
        context.user_data.pop("trade_creation")
        message_text = (
            f"{EmojiEnums.CHECK_MARK.value} Trade creation process has been cancelled."
        )
        reply_markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🆕 Start New Trade", callback_data="create_trade"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🏡 Main Menu", callback_data=CallbackDataEnums.MENU.value
                    )
                ],
            ]
        )

    elif active_trade:
        # Only active database trade
        message_text = (
            f"📊 <b>Active Trade Found</b>\n\n"
            f"You have an active trade: #{active_trade['_id']}\n"
            f"Amount: {active_trade.get('price', 'Unknown')} {active_trade.get('currency', '')}\n"
            f"Type: {active_trade.get('trade_type', 'Unknown')}\n"
            f"Status: {active_trade.get('status', 'active')}\n"
            f"Is Active: {active_trade.get('is_active', False)}\n"
            f"Is Cancelled: {active_trade.get('is_cancelled', False)}\n"
            f"Is Completed: {active_trade.get('is_completed', False)}\n\n"
            f"No trade creation process to cancel.\n\n"
            f"Choose what you'd like to do:"
        )
        reply_markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🗑️ Cancel This Trade",
                        callback_data=f"cancel_trade_{active_trade['_id']}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "📊 View Full Details",
                        callback_data=f"view_trade_{active_trade['_id']}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🏡 Main Menu", callback_data=CallbackDataEnums.MENU.value
                    )
                ],
            ]
        )

    else:
        # Nothing to cancel
        message_text = (
            f"ℹ️ <b>Nothing to Cancel</b>\n\n"
            f"You don't have any:\n"
            f"• Active trade creation process\n"
            f"• Active trades in the database\n\n"
            f"You're all clear!"
        )
        reply_markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🆕 Start New Trade", callback_data="create_trade"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🏡 Main Menu", callback_data=CallbackDataEnums.MENU.value
                    )
                ],
            ]
        )

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            message_text, parse_mode="HTML", reply_markup=reply_markup
        )
    elif update.message:
        await update.message.reply_text(
            message_text, parse_mode="HTML", reply_markup=reply_markup
        )


async def dispatch_to_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Dispatches incoming messages or callback queries to the appropriate
    method in the active trade flow based on context.
    """
    # Add debug logging for admin callbacks
    if (
        update.callback_query
        and update.callback_query.data
        and update.callback_query.data.startswith("admin_")
    ):
        logging.info(
            f"dispatch_to_flow: Admin callback detected: {update.callback_query.data}, skipping"
        )
        return

    # Handle seller rejection reason input for CryptoFiatFlow
    if (
        update.message
        and update.message.text
        and not update.message.text.startswith("/")
    ):
        if context.user_data.get("rejecting_payment"):
            await CryptoFiatFlow.handle_rejection_reason(update, context)
            return

    if not context.user_data or "trade_creation" not in context.user_data:
        # If not in a trade creation flow, or if called for a message not meant for it,
        # simply return and let other handlers (if any) process it.
        # This also means it won't interfere with commands.
        return

    trade_creation_data = context.user_data.get("trade_creation")
    if not trade_creation_data:  # Should be caught by the above, but as a safeguard
        return

    active_flow_name = trade_creation_data.get("active_flow_module")
    current_flow_step = trade_creation_data.get("current_flow_step")

    # If flow is not yet fully initiated (e.g. just after type selection but before flow sets its own step)
    if (
        not active_flow_name
        or not current_flow_step
        or trade_creation_data.get("step") != "flow_initiated"
    ):
        # This check ensures it only acts when a flow is truly active and managing steps.
        # It avoids interfering if 'step' is 'select_trade_type' for example.
        return

    target_flow_class = None
    if active_flow_name == CryptoFiatFlow.FLOW_NAME:
        target_flow_class = CryptoFiatFlow
    # Add elif for other flows when they are implemented
    # elif active_flow_name == CryptoCryptoFlow.FLOW_NAME:
    #     target_flow_class = CryptoCryptoFlow

    if not target_flow_class:
        logging.error(
            f"dispatch_to_flow: Unknown active_flow_module name: {active_flow_name}"
        )
        return

    # Message Handling
    if (
        update.message
        and update.message.text
        and not update.message.text.startswith("/")
    ):
        if active_flow_name == CryptoFiatFlow.FLOW_NAME:
            if current_flow_step == AWAITING_AMOUNT:
                await target_flow_class.handle_amount_input(update, context)
            elif current_flow_step == AWAITING_DESCRIPTION:
                await target_flow_class.handle_description_input(update, context)
            else:
                # Optionally, inform the user if they send text at an unexpected step
                # await update.message.reply_text("I'm expecting you to use a button or follow other instructions.")
                logging.debug(
                    f"Fiat flow: Unhandled message for step {current_flow_step}. Text: {update.message.text}"
                )
        # Add elif for other flows' message steps

    # Callback Query Handling
    elif update.callback_query:
        query = update.callback_query
        # Specific flow related callbacks (not generic ones like cancel, menu, etc.)
        if query.data.startswith("currency_"):
            if (
                active_flow_name == CryptoFiatFlow.FLOW_NAME
                and current_flow_step == AWAITING_CURRENCY
            ):
                await target_flow_class.handle_currency_selection(query, context)
            else:
                await query.answer("This currency choice is not active right now.")
                logging.warning(
                    f"Flow dispatch: Unhandled currency_ callback for flow {active_flow_name}, step {current_flow_step}"
                )
        elif query.data in ["broker_yes", "broker_no"]:
            if (
                active_flow_name == CryptoFiatFlow.FLOW_NAME
                and current_flow_step == AWAITING_BROKER_CHOICE
            ):
                await target_flow_class.handle_broker_choice(query, context)
            else:
                await query.answer("This broker choice is not active right now.")
                logging.warning(
                    f"Flow dispatch: Unhandled broker choice callback for flow {active_flow_name}, step {current_flow_step}"
                )
        elif query.data.startswith("select_broker_"):
            if (
                active_flow_name == CryptoFiatFlow.FLOW_NAME
                and current_flow_step == AWAITING_BROKER_SELECTION
            ):
                await target_flow_class.handle_broker_selection(query, context)
            else:
                await query.answer("This broker selection is not active right now.")
                logging.warning(
                    f"Flow dispatch: Unhandled broker selection callback for flow {active_flow_name}, step {current_flow_step}"
                )
        # Add elif for other flows and their specific callback prefixes
        else:
            # This 'else' means the callback wasn't handled by specific patterns above
            # It might be a generic callback that slipped through or an unexpected one for the current flow state
            # It's important not to broadly answer all unhandled callbacks here without care,
            # as other more specific handlers (registered with higher priority or different patterns) should catch them.
            logging.debug(
                f"Flow dispatch: Callback '{query.data}' not explicitly handled for flow {active_flow_name}, step {current_flow_step}"
            )
            # If absolutely sure it's an unhandled relevant callback for this dispatcher:
            # await query.answer("This option isn't available at this step.")


async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current user status - trades, creation process, etc."""
    user_id = str(update.effective_user.id)
    user_obj = UserClient.get_user(update.message)

    # Check trade creation process
    trade_creation = context.user_data.get("trade_creation")

    # Check active trades - get all instead of just one
    active_trades = []
    if user_obj:
        active_trades = TradeClient.get_active_trades_for_user(user_id)

    # Build status message
    status_parts = [f"📊 <b>Your Current Status</b>\n"]

    # Trade creation status
    if trade_creation:
        step = trade_creation.get("step", "unknown")
        trade_type = trade_creation.get("trade_type", "Unknown")
        flow_step = trade_creation.get("current_flow_step", "N/A")

        status_parts.extend(
            [
                f"🔄 <b>Trade Creation:</b> ✅ In Progress",
                f"   • Type: {trade_type}",
                f"   • Step: {step}",
                f"   • Flow: {flow_step}\n",
            ]
        )
    else:
        status_parts.append(f"🔄 <b>Trade Creation:</b> ❌ None\n")

    # Active trades status - show up to 3 trades with details
    if active_trades:
        num_trades = len(active_trades)
        status_parts.append(
            f"💰 <b>Active Trades:</b> ✅ {num_trades} trade{'s' if num_trades != 1 else ''}\n"
        )

        # Show details for up to 3 trades
        for i, trade in enumerate(active_trades[:3], 1):
            trade_id = trade["_id"]
            amount = trade.get("price", "Unknown")
            currency = trade.get("currency", "")
            trade_type = trade.get("trade_type", "Unknown")
            status = trade.get("status", "active")
            seller_id = str(trade.get("seller_id", ""))
            buyer_id = str(trade.get("buyer_id", ""))

            role = (
                "Seller"
                if seller_id == user_id
                else ("Buyer" if buyer_id == user_id else "Unknown")
            )

            status_parts.extend(
                [
                    f"\n<b>Trade #{i}:</b>",
                    f"   • ID: #{trade_id[:8]}...",
                    f"   • Amount: {amount} {currency}",
                    f"   • Type: {trade_type}",
                    f"   • Your Role: {role}",
                    f"   • Status: {status}",
                ]
            )

            # Add broker info if present
            if trade.get("broker_enabled"):
                broker_id = trade.get("broker_id", "")
                status_parts.append(
                    f"   • Broker: {'Yes' if broker_id else 'Enabled but not assigned'}"
                )

        # If more than 3 trades, show count
        if num_trades > 3:
            status_parts.append(
                f"\n<i>...and {num_trades - 3} more trade{'s' if num_trades - 3 != 1 else ''}</i>"
            )
        status_parts.append("")  # Add empty line
    else:
        status_parts.append(f"💰 <b>Active Trades:</b> ❌ None\n")

    # Recommendations and buttons
    if trade_creation and active_trades:
        status_parts.extend(
            [
                f"⚠️ <b>Issue Detected:</b>",
                f"You have both a creation process AND active trade(s).",
                f"Consider completing or cancelling the creation process first.",
            ]
        )
        buttons = [
            [
                InlineKeyboardButton(
                    "❌ Cancel Creation Process", callback_data="cancel_creation"
                )
            ],
            [InlineKeyboardButton("📋 View My Trades", callback_data="my_trades")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")],
        ]
    elif trade_creation:
        status_parts.append(
            f"💡 <b>Tip:</b> Continue your trade creation or use /cancel to abort."
        )
        buttons = [
            [
                InlineKeyboardButton(
                    "❌ Cancel Creation", callback_data="cancel_creation"
                )
            ],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")],
        ]
    elif active_trades:
        if len(active_trades) == 1:
            status_parts.append(
                f"💡 <b>Tip:</b> Use /mytrades to view and manage your active trade."
            )
        else:
            status_parts.append(
                f"💡 <b>Tip:</b> Use /mytrades to view and manage all your active trades."
            )
        buttons = [
            [InlineKeyboardButton("📋 View My Trades", callback_data="my_trades")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")],
        ]
    else:
        status_parts.append(f"✅ <b>All Clear:</b> Ready to create a new trade!")
        buttons = [
            [InlineKeyboardButton("🆕 Create New Trade", callback_data="create_trade")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")],
        ]

    status_message = "\n".join(status_parts)

    await update.message.reply_text(
        status_message, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(buttons)
    )


async def debug_user_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Debug command for admins to check user state"""
    from config import ADMIN_ID

    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text(
            "❌ This command is only available to administrators."
        )
        return

    # Get target user ID from command args
    if context.args and len(context.args) > 0:
        try:
            target_user_id = str(context.args[0])
        except:
            await update.message.reply_text("❌ Invalid user ID format.")
            return
    else:
        await update.message.reply_text(
            "Usage: /debug <user_id>\n" "Example: /debug 123456789"
        )
        return

    # Get user object
    user_obj = UserClient.get_user_by_id(target_user_id)
    if not user_obj:
        await update.message.reply_text(
            f"❌ User {target_user_id} not found in database."
        )
        return

    # Check context data (this won't work across sessions, but useful for current session debugging)
    debug_parts = [
        f"🔍 <b>Debug Report for User {target_user_id}</b>\n",
        f"👤 <b>User Info:</b>",
        f"   • Name: {user_obj.get('name', 'Unknown')}",
        f"   • Verified: {user_obj.get('verified', False)}",
        f"   • Created: {user_obj.get('created_at', 'Unknown')}\n",
    ]

    # Check for active trades
    active_trade = TradeClient.get_most_recent_trade(user_obj)
    if active_trade:
        is_really_active = active_trade.get("is_active", False)
        debug_parts.extend(
            [
                f"💰 <b>Most Recent Trade:</b>",
                f"   • ID: {active_trade['_id']}",
                f"   • Active Flag: {is_really_active}",
                f"   • Status: {active_trade.get('status', 'unknown')}",
                f"   • Amount: {active_trade.get('price', 'Unknown')} {active_trade.get('currency', '')}",
                f"   • Type: {active_trade.get('trade_type', 'Unknown')}",
                f"   • Seller: {active_trade.get('seller_id', 'Unknown')}",
                f"   • Buyer: {active_trade.get('buyer_id', 'None')}",
                f"   • Created: {active_trade.get('created_at', 'Unknown')}\n",
            ]
        )

        if active_trade.get("broker_enabled"):
            debug_parts.extend(
                [
                    f"🤝 <b>Broker Info:</b>",
                    f"   • Enabled: {active_trade.get('broker_enabled', False)}",
                    f"   • ID: {active_trade.get('broker_id', 'None')}",
                    f"   • Commission: {active_trade.get('broker_commission', 0)}%\n",
                ]
            )
    else:
        debug_parts.append(f"💰 <b>Recent Trade:</b> None found\n")

    # Check all user's active trades
    all_active = list(
        db.trades.find(
            {
                "$or": [
                    {"seller_id": target_user_id, "is_active": True},
                    {"buyer_id": target_user_id, "is_active": True},
                ]
            }
        )
    )

    debug_parts.extend(
        [
            f"📊 <b>All Active Trades:</b> {len(all_active)}",
        ]
    )

    for i, trade in enumerate(all_active[:3]):  # Show max 3
        role = "Seller" if trade.get("seller_id") == target_user_id else "Buyer"
        debug_parts.append(
            f"   {i+1}. #{trade['_id']} ({role}) - {trade.get('status', 'unknown')}"
        )

    if len(all_active) > 3:
        debug_parts.append(f"   ... and {len(all_active) - 3} more")

    debug_parts.append("")

    # Recommendations
    if len(all_active) > 1:
        debug_parts.extend(
            [
                f"⚠️ <b>Issue:</b> User has {len(all_active)} active trades",
                f"This may cause the 'existing trade' error.",
            ]
        )
    elif len(all_active) == 0:
        debug_parts.append(
            f"✅ <b>Status:</b> No active trades found - user should be able to create new trades"
        )
    else:
        debug_parts.append(f"ℹ️ <b>Status:</b> User has 1 active trade - normal state")

    debug_message = "\n".join(debug_parts)

    await update.message.reply_text(
        debug_message,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🗑️ Force Clear Active Trades",
                        callback_data=f"admin_clear_trades_{target_user_id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "📊 Full Trade History",
                        callback_data=f"admin_trade_history_{target_user_id}",
                    )
                ],
                [InlineKeyboardButton("🔙 Close Debug", callback_data="menu")],
            ]
        ),
    )


def register_handlers(application):
    """Register handlers for the initiate trade module"""
    from telegram.ext import (
        CallbackQueryHandler,
        CommandHandler,
        MessageHandler,
        filters,
    )

    # Command handlers
    application.add_handler(CommandHandler("trade", initiate_trade_handler))
    application.add_handler(CommandHandler("cancel", cancel_handler))
    application.add_handler(CommandHandler("status", status_handler))
    application.add_handler(CommandHandler("debug", debug_user_handler))

    # Callback query handlers for trade type selection
    application.add_handler(
        CallbackQueryHandler(handle_trade_type_selection, pattern=r"^trade_type_")
    )

    # Cancel creation callback
    application.add_handler(
        CallbackQueryHandler(cancel_handler, pattern="^cancel_creation$")
    )

    # Callback query handlers for trade flow-related callbacks
    # These need to be routed to dispatch_to_flow, not just text messages
    application.add_handler(
        CallbackQueryHandler(dispatch_to_flow, pattern=r"^currency_")
    )

    # NOTE: broker_yes, broker_no, and select_broker_ callbacks are handled
    # by callbacks.py handle_broker_callbacks - removed duplicate registrations

    # Message handler for trade flow dispatch (lowest priority)
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, dispatch_to_flow
        ),
        group=5,  # Lower priority - only handles trade creation flows
    )
