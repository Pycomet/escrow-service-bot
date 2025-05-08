from config import *
from utils import *
from functions import *
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler
import logging


##############TRADE CREATION
async def trade_terms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Terms of trade
    """
    user = UserClient.get_user(update.message)

    question = await context.bot.send_message(
        chat_id=user["_id"],
        text="📝 What are the terms for the escrow contract you are about to create ?",
    )

    context.user_data["next_step"] = trade_price


async def trade_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Receive user input on trade price
    """
    # import pdb; pdb.set_trace()
    terms = update.message.text
    user = UserClient.get_user_by_id(update.message.from_user.id)

    trade = TradeClient.add_terms(user=user, terms=str(terms))

    if trade is None:
        await context.bot.send_message(
            chat_id=user["_id"],
            text="❌ Error creating trade. Please try again.",
        )
        return

    question = await context.bot.send_message(
        chat_id=user["_id"],
        text="💰 What is the price of the trade in your local currency?",
    )

    context.user_data["next_step"] = creating_trade


async def creating_trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Recieve user price input on trade
    """
    price = update.message.text
    user = UserClient.get_user_by_id(update.message.from_user.id)

    trade = TradeClient.add_price(user=user, price=float(price))

    if trade is None:
        await context.bot.send_message(
            chat_id=update.message.chat.id, 
            text="❌ Unable to find your trade. Please start over"
        )
        return

    # Get Payment Url
    # payment_url = TradeClient.get_invoice_url(trade=trade)
    payment_url = "" # Keeping empty as requested - will be implemented later
    trade = TradeClient.get_most_recent_trade(user)

    # Skip the None check since we're using an empty string
    # Create an inline keyboard with a Forward button
    inline_keyboard = [
        [InlineKeyboardButton("Forward", switch_inline_query=""),
         InlineKeyboardButton("Join Trade", url=f"https://t.me/{context.bot.username}?start=join_{trade['_id']}")]
    ]
    keyboard_markup = InlineKeyboardMarkup(inline_keyboard)

    # Send the message with the inline keyboard
    await context.bot.send_message(
        chat_id=update.message.from_user.id,
        text=Messages.trade_created(trade),
        parse_mode="html",
        reply_markup=keyboard_markup,
    )

    # Send instructions
    await context.bot.send_message(
        chat_id=update.message.from_user.id, 
        text=Messages.trade_created(trade)
    )


async def initiate_trade_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /trade command"""
    user_id = update.effective_user.id
    
    # Check if user already has a trade creation in progress
    if context.user_data.get("trade_creation"):
        await update.message.reply_text(
            "❌ You already have a trade creation in progress. "
            "Please complete it or use /cancel to start over.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
            ]])
        )
        return
    
    # Check if user is already involved in an active trade
    active_trade = trades_db.get_active_trade_by_user_id(str(user_id))
    if active_trade:
        await update.message.reply_text(
            f"❌ You already have an active trade (#{active_trade['_id']}). "
            "Please complete or cancel your current trade before starting a new one.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
            ]])
        )
        return
    
    # Start trade creation process - now ask for trade type first
    keyboard = await trade_type_menu()
    await update.message.reply_text(
        "📝 Let's create a new trade!\n\n"
        "Please select the type of trade you want to create:",
        reply_markup=keyboard
    )
    
    # Set state to wait for trade type selection
    context.user_data["trade_creation"] = {"step": "select_trade_type"}


async def handle_trade_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the trade amount input"""
    # Only handle if this user is in the amount step
    if not context.user_data.get("trade_creation", {}).get("step") == "amount":
        return
    
    try:
        amount = float(update.message.text)
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        # Store amount and move to next step
        context.user_data["trade_creation"]["amount"] = amount
        context.user_data["trade_creation"]["step"] = "currency"
        
        # Get trade type to customize currency options
        trade_type = context.user_data["trade_creation"].get("trade_type", "")
 
        if trade_type == TradeTypeEnums.CRYPTO_FIAT.value:
            prompt = "💱 Please select the crypto currency of the asset you're trying to sell:"
            keyboard = currency_menu("crypto")

        elif trade_type == TradeTypeEnums.CRYPTO_CRYPTO.value:
            prompt = "💱 Please select the base currency for this crypto exchange:"
            keyboard = currency_menu("fiat")

        elif trade_type == TradeTypeEnums.CRYPTO_PRODUCT.value:
            prompt = "💱 Please select the currency for pricing your product:"
            keyboard = currency_menu("fiat")

        elif trade_type == TradeTypeEnums.MARKET_SHOP.value:
            prompt = "💱 Here are the list of available trades in the market right now:"
            keyboard = None # Ideally meant to be the list of available trades

        else:
            prompt = "💱 Please select the currency for this trade:"
            keyboard = currency_menu("fiat")
        
        
        await update.message.reply_text(
            prompt,
            reply_markup=keyboard                                                                                                                                                                                       
        )
        
    except ValueError:
        await update.message.reply_text(
            "❌ Please enter a valid positive number.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Cancel", callback_data="menu")
            ]])
        )


async def handle_trade_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the trade currency selection"""
    query = update.callback_query
    await query.answer()
    
    if not context.user_data.get("trade_creation", {}).get("step") == "currency":
        return
    
    currency = query.data.replace("currency_", "")
    
    # Store currency and move to next step
    context.user_data["trade_creation"]["currency"] = currency
    context.user_data["trade_creation"]["step"] = "description"
    
    # Get the trade type to customize the prompt
    trade_type = context.user_data["trade_creation"].get("trade_type", "")
    
    if trade_type == "CryptoToFiat":
        prompt = (
            "📝 <b>Details for your Crypto to Fiat Trade</b>\n\n"
            f"Selected currency: {currency}\n\n"
            "Please provide the following details:\n"
            "• Which cryptocurrency you're selling\n"
            "• Your preferred payment method (bank transfer, cash, etc.)\n"
            "• Any additional terms or conditions"
        )
    elif trade_type == "CryptoToCrypto":
        prompt = (
            "📝 <b>Details for your Crypto to Crypto Trade</b>\n\n"
            f"Selected currency: {currency}\n\n"
            "Please provide the following details:\n"
            "• Which cryptocurrency you're offering\n"
            "• Which cryptocurrency you want in return\n"
            "• Exchange rate details\n"
            "• Any additional terms or requirements"
        )
    elif trade_type == "CryptoToProduct":
        prompt = (
            "📝 <b>Details for your Crypto to Product Trade</b>\n\n"
            f"Selected currency: {currency}\n\n"
            "Please provide the following details:\n"
            "• Product name and description\n"
            "• Condition (new, used, etc.)\n"
            "• Delivery or pickup details\n"
            "• Which cryptocurrency you accept\n"
            "• Any warranty or return policy"
        )
    elif trade_type == "MarketShop":
        prompt = (
            "📝 <b>Details for your Market Shop</b>\n\n"
            f"Selected currency: {currency}\n\n"
            "Please provide the following details:\n"
            "• Shop name\n"
            "• Types of products available\n"
            "• Pricing and cryptocurrency acceptance\n"
            "• Shipping/delivery information\n"
            "• Any shop policies or rules"
        )
    else:
        prompt = (
            "📝 Please enter a description for this trade:\n\n"
            "Include details about what you're selling and any specific terms or conditions."
        )
    
    await query.edit_message_text(
        prompt,
        parse_mode="html",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Cancel", callback_data="menu")
        ]])
    )


async def handle_trade_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the trade description input"""
    if not context.user_data.get("trade_creation", {}).get("step") == "description":
        logging.warning("handle_trade_description called but step is not 'description'")
        return
    
    # Get trade type and route to appropriate flow
    trade_data = context.user_data["trade_creation"]
    trade_type = trade_data.get("trade_type", "")
    
    logging.info(f"Routing to trade flow handler for type: {trade_type}")
    
    # Import here to avoid circular imports
    from handlers.trade_flows import TradeFlowHandler
    
    # Route to specific trade flow
    success = await TradeFlowHandler.route_trade_flow(update, context, trade_type)
    
    if not success:
        logging.error("Trade flow handler failed")
        await update.message.reply_text(
            "❌ Failed to process trade. Please try again.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
            ]])
        )


async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the current operation and clear user data"""
    if "trade_creation" in context.user_data:
        context.user_data.pop("trade_creation")
        await update.message.reply_text(
            "✅ Trade creation cancelled.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
            ]])
        )
    else:
        await update.message.reply_text(
            "Nothing to cancel.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
            ]])
        )


def register_handlers(application):
    """Register handlers for the initiate trade module"""
    application.add_handler(CommandHandler("trade", initiate_trade_handler))
    application.add_handler(CommandHandler("cancel", cancel_handler))
    
    # Handle currency selection via callback query
    application.add_handler(CallbackQueryHandler(handle_trade_currency, pattern="^currency_"))
    
    # Handle trade type selection via callback query
    application.add_handler(CallbackQueryHandler(handle_trade_type_selection, pattern="^trade_type_"))
    
    # Handle deposit check callback
    application.add_handler(CallbackQueryHandler(handle_check_deposit_callback, pattern="^check_deposit$"))
    
    # Create a combined handler for all trade creation steps
    async def trade_creation_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Early return if this is not a private chat or is a command
        if not update.effective_user or not update.message or update.message.text.startswith('/'):
            return
            
        # Get the current step in the trade creation process
        current_step = context.user_data.get("trade_creation", {}).get("step")
        logging.info(f"Processing message in trade creation. Current step: {current_step}, Text: {update.message.text}")
        
        # Route to the appropriate handler based on the step
        if current_step == "select_trade_type":
            logging.info("Handling trade type selection step")
            # Ignore text messages at this step, selection handled by callback query
            return
        elif current_step == "amount":
            logging.info("Handling amount step")
            await handle_trade_amount(update, context)
        elif current_step == "description":
            logging.info("Handling description step")
            await handle_trade_description(update, context)
        else:
            logging.info(f"Message received but no matching step found. Current step: {current_step}")
    
    # Register the combined handler for all text messages in private chats
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE,
        trade_creation_handler
    ))


async def handle_trade_type_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the trade type selection callback"""
    query = update.callback_query
    await query.answer()
    
    # Verify we're in the correct step
    if not context.user_data.get("trade_creation", {}).get("step") == "select_trade_type":
        await query.message.edit_text(
            "❌ Something went wrong. Please start over with /trade",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
            ]])
        )
        return
    
    trade_type = query.data.replace("trade_type_", "")
    
    if trade_type == "Disabled":
        await query.message.edit_text(
            "❌ This feature is currently not available, will be back active soon!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
            ]])
        )
        return

    elif trade_type not in [e.value for e in TradeTypeEnums]:
        await query.message.edit_text(
            "❌ Invalid trade type selected. Please start over with /trade",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
            ]])
        )
        return
    


    
    # Store trade type and update state
    context.user_data["trade_creation"]["trade_type"] = trade_type
    context.user_data["trade_creation"]["step"] = "amount"
    
    # Ask for trade amount
    await query.message.edit_text(
        f"💰 You've selected a {trade_type} trade.\n\n"
        "Please enter the amount for this trade:",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Cancel", callback_data="menu")
        ]])
    )


async def handle_check_deposit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the check deposit callback"""
    query = update.callback_query
    await query.answer()
    
    # Get trade type and route to appropriate flow
    trade_data = context.user_data.get("trade_creation", {})
    trade_type = trade_data.get("trade_type", "")
    
    if trade_type == TradeTypeEnums.CRYPTO_FIAT.value:
        from handlers.trade_flows.fiat import CryptoFiatFlow
        await CryptoFiatFlow.handle_deposit(update, context)
    else:
        await query.edit_message_text(
            "❌ Invalid trade type for deposit check.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
            ]])
        )
