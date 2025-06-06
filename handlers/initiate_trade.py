from config import *
from utils import *
from functions import *
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler
import logging

from utils.keyboard import trade_type_menu
from utils.enums import TradeTypeEnums, CallbackDataEnums, EmojiEnums
from handlers.trade_flows import TradeFlowHandler
from utils.messages import Messages
from functions.trade import TradeClient
from functions.user import UserClient

# Import flow classes and their specific state constants
from handlers.trade_flows.fiat import CryptoFiatFlow, AWAITING_AMOUNT, AWAITING_CURRENCY, AWAITING_DESCRIPTION
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
            f"{EmojiEnums.CROSS_MARK.value} You already have a trade creation in progress. "
            "Please complete it or use /cancel to start over.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(f"{EmojiEnums.BACK_ARROW.value} Back to Menu", callback_data=CallbackDataEnums.MENU.value)
            ]])
        )
        return
    
    user_obj = UserClient.get_user(update.message)
    if user_obj:
        active_trade = TradeClient.get_most_recent_trade(user_obj)
        if active_trade and active_trade.get('is_active', False):
            await update.message.reply_text(
                f"{EmojiEnums.CROSS_MARK.value} You already have an active trade (#{active_trade['_id']}). "
                "Please complete or cancel your current trade before starting a new one.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(f"{EmojiEnums.BACK_ARROW.value} Back to Menu", callback_data=CallbackDataEnums.MENU.value)
                ]])
            )
            return
    else:
        logging.warning(f"User not found for ID {user_id} in initiate_trade_handler")

    keyboard = await trade_type_menu()
    await update.message.reply_text(
        "📝 Let's create a new trade!\n\n"
        "Please select the type of trade you want to create:",
        reply_markup=keyboard
    )
    
    context.user_data["trade_creation"] = {"step": "select_trade_type"}

async def handle_trade_type_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the trade type selection callback"""
    query = update.callback_query
    await query.answer()
    
    if not context.user_data.get("trade_creation", {}).get("step") == "select_trade_type":
        await query.message.edit_text(
            f"{EmojiEnums.CROSS_MARK.value} Something went wrong. Please start over with /trade",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(f"{EmojiEnums.BACK_ARROW.value} Back to Menu", callback_data=CallbackDataEnums.MENU.value)
            ]])
        )
        return
    
    trade_type_value = query.data.replace("trade_type_", "")
    
    valid_enum_values = [e.value for e in TradeTypeEnums]
    if trade_type_value == "Disabled":
        await query.message.edit_text(
            f"{EmojiEnums.CROSS_MARK.value} This feature is currently not available, will be back active soon!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(f"{EmojiEnums.BACK_ARROW.value} Back to Menu", callback_data=CallbackDataEnums.MENU.value)
            ]])
        )
        return
    elif trade_type_value not in valid_enum_values:
        await query.message.edit_text(
            f"{EmojiEnums.CROSS_MARK.value} Invalid trade type selected. Please start over with /trade",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(f"{EmojiEnums.BACK_ARROW.value} Back to Menu", callback_data=CallbackDataEnums.MENU.value)
            ]])
        )
        context.user_data.pop("trade_creation", None)
        return
        
    context.user_data["trade_creation"]["trade_type"] = trade_type_value
    context.user_data["trade_creation"]["step"] = "flow_initiated"

    logging.info(f"Trade type {trade_type_value} selected. Initiating flow setup.")
    
    success = await TradeFlowHandler.initiate_flow_setup(update, context, trade_type_value)
    
    if not success:
        logging.error(f"Trade flow setup failed for type: {trade_type_value}")
        try:
            await query.edit_message_text(
                f"{EmojiEnums.CROSS_MARK.value} Failed to start trade setup. Please try again or contact support.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(f"{EmojiEnums.BACK_ARROW.value} Back to Menu", callback_data=CallbackDataEnums.MENU.value)
                ]])
            )
        except Exception as e:
            logging.error(f"Error editing message after flow setup failure: {e}")
        context.user_data.pop("trade_creation", None)

async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the current trade creation process"""
    if "trade_creation" in context.user_data:
        context.user_data.pop("trade_creation")
        message_text = f"{EmojiEnums.CHECK_MARK.value} Trade creation process has been cancelled."
    else:
        message_text = "ℹ️ You don't have any active trade creation process to cancel."

    reply_markup=InlineKeyboardMarkup([[
        InlineKeyboardButton("🆕 Start New Trade", callback_data="create_trade"),
        InlineKeyboardButton("🏡 Main Menu", callback_data=CallbackDataEnums.MENU.value)
    ]])

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(message_text, reply_markup=reply_markup)
    elif update.message:
        await update.message.reply_text(message_text, reply_markup=reply_markup)

async def dispatch_to_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Dispatches incoming messages or callback queries to the appropriate
    method in the active trade flow based on context.
    """
    if not context.user_data or "trade_creation" not in context.user_data:
        # If not in a trade creation flow, or if called for a message not meant for it,
        # simply return and let other handlers (if any) process it.
        # This also means it won't interfere with commands.
        return

    trade_creation_data = context.user_data.get("trade_creation")
    if not trade_creation_data: # Should be caught by the above, but as a safeguard
        return

    active_flow_name = trade_creation_data.get("active_flow_module")
    current_flow_step = trade_creation_data.get("current_flow_step")

    # If flow is not yet fully initiated (e.g. just after type selection but before flow sets its own step)
    if not active_flow_name or not current_flow_step or trade_creation_data.get("step") != "flow_initiated":
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
        logging.error(f"dispatch_to_flow: Unknown active_flow_module name: {active_flow_name}")
        return

    # Message Handling
    if update.message and update.message.text and not update.message.text.startswith('/'):
        if active_flow_name == CryptoFiatFlow.FLOW_NAME:
            if current_flow_step == AWAITING_AMOUNT:
                await target_flow_class.handle_amount_input(update, context)
            elif current_flow_step == AWAITING_DESCRIPTION:
                await target_flow_class.handle_description_input(update, context)
            else:
                # Optionally, inform the user if they send text at an unexpected step
                # await update.message.reply_text("I'm expecting you to use a button or follow other instructions.")
                logging.debug(f"Fiat flow: Unhandled message for step {current_flow_step}. Text: {update.message.text}")
        # Add elif for other flows' message steps

    # Callback Query Handling
    elif update.callback_query:
        query = update.callback_query
        # Specific flow related callbacks (not generic ones like cancel, menu, etc.)
        if query.data.startswith("currency_"):
            if active_flow_name == CryptoFiatFlow.FLOW_NAME and current_flow_step == AWAITING_CURRENCY:
                await target_flow_class.handle_currency_selection(query, context)
            else:
                await query.answer("This currency choice is not active right now.")
                logging.warning(f"Flow dispatch: Unhandled currency_ callback for flow {active_flow_name}, step {current_flow_step}")
        # Add elif for other flows and their specific callback prefixes
        else:
            # This 'else' means the callback wasn't handled by specific patterns above
            # It might be a generic callback that slipped through or an unexpected one for the current flow state
            # It's important not to broadly answer all unhandled callbacks here without care,
            # as other more specific handlers (registered with higher priority or different patterns) should catch them.
            logging.debug(f"Flow dispatch: Callback '{query.data}' not explicitly handled for flow {active_flow_name}, step {current_flow_step}")
            # If absolutely sure it's an unhandled relevant callback for this dispatcher:
            # await query.answer("This option isn't available at this step.")

def register_handlers(application):
    """Register handlers for the initiate trade module"""
    application.add_handler(CommandHandler("trade", initiate_trade_handler))
    application.add_handler(CommandHandler("cancel", cancel_handler))
    application.add_handler(CallbackQueryHandler(cancel_handler, pattern="^cancel_creation$"))

    application.add_handler(CallbackQueryHandler(handle_trade_type_selection, pattern="^trade_type_"))
    
    # Temporarily disabled - conflicts with specific flow handlers
    # application.add_handler(CallbackQueryHandler(handle_check_deposit_callback, pattern=r"^check_deposit(?:_\w+)?$"))

    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, 
        dispatch_to_flow
    ), group=1)

    application.add_handler(CallbackQueryHandler(dispatch_to_flow, pattern="^.*$", block=False), group=1)
