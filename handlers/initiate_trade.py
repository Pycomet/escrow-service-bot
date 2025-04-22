from config import *
from utils import *
from functions import *
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler


async def open_trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    This opens a new trade with seller actions
    """
    keyboard = local_currency_menu()

    await context.bot.delete_message(chat_id=update.message.chat.id, message_id=update.message.message_id)

    user = UserClient.get_user_by_id(update.message.from_user.id)

    await context.bot.send_message(
        chat_id=user["_id"],
        text="💰 To create a new trade today, select which is your local currency of choice... ",
        reply_markup=keyboard,
    )


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
        [InlineKeyboardButton("Forward", switch_inline_query="")]
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
    
    # Start trade creation process
    await update.message.reply_text(
        "📝 Let's create a new trade!\n\n"
        "Please enter the amount for this trade:",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Cancel", callback_data="menu")
        ]])
    )
    
    # Set state to wait for amount
    context.user_data["trade_creation"] = {"step": "amount"}


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
        
        # Show currency selection
        await update.message.reply_text(
            "💱 Please select the currency for this trade:",
            reply_markup=currency_menu()
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
    
    await query.edit_message_text(
        "📝 Please enter a description for this trade:\n\n"
        "Include details about what you're selling and any specific terms or conditions.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Cancel", callback_data="menu")
        ]])
    )


async def handle_trade_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the trade description input"""
    if not context.user_data.get("trade_creation", {}).get("step") == "description":
        return
    
    description = update.message.text
    
    # Get trade creation data
    trade_data = context.user_data["trade_creation"]
    
    # Create the trade
    trade = trades_db.open_new_trade(
        update.message,
        currency=trade_data["currency"]
    )
    
    if trade:
        # Update the trade with the amount and description
        trades_db.add_price(UserClient.get_user_by_id(update.effective_user.id), trade_data["amount"])
        trades_db.add_terms(UserClient.get_user_by_id(update.effective_user.id), description)
        
        # Clear trade creation data
        context.user_data.pop("trade_creation", None)
        
        # Show success message with trade details
        await update.message.reply_text(
            f"✅ Trade created successfully!\n\n"
            f"📋 <b>Trade Details</b>\n"
            f"ID: <code>{trade['_id']}</code>\n"
            f"Amount: {trade_data['amount']} {trade_data['currency']}\n"
            f"Description: {description}\n\n"
            f"Share this trade ID with the buyer to complete the transaction.",
            parse_mode="html",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
            ]])
        )
    else:
        await update.message.reply_text(
            "❌ Failed to create trade. Please try again later.",
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
    
    # Use custom filter to only handle messages when the user is in the amount step
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE & 
        (lambda update: update.effective_user and
         application.user_data.get(update.effective_user.id, {}).get("trade_creation", {}).get("step") == "amount"),
        handle_trade_amount
    ))
    
    # Handle currency selection via callback query
    application.add_handler(CallbackQueryHandler(handle_trade_currency, pattern="^currency_"))
    
    # Use custom filter to only handle messages when the user is in the description step
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE &
        (lambda update: update.effective_user and
         application.user_data.get(update.effective_user.id, {}).get("trade_creation", {}).get("step") == "description"),
        handle_trade_description
    ))

# Register handlers
application.add_handler(MessageHandler(filters.Regex("^Open New Trade"), open_trade))
