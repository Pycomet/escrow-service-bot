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
    payment_url = "" # TODO: Change this entirely to web3 solution
    trade = TradeClient.get_most_recent_trade(user)

    if payment_url is None:
        await context.bot.send_message(
            chat_id=update.message.chat.id, 
            text="❌ Unable to get payment url. Please try again"
        )
        return

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
    # forward_instruction = "Tap and hold on the message above, then choose 'Forward' to send it to your friends."
    await context.bot.send_message(
        chat_id=update.message.from_user.id, 
        text=Messages.trade_created(trade)
    )


async def initiate_trade_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /trade command"""
    user_id = update.effective_user.id
    
    # Check if user is already involved in an active trade
    active_trade = get_active_trade_by_user_id(user_id)
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
    trade = create_trade(
        seller_id=update.effective_user.id,
        amount=trade_data["amount"],
        currency=trade_data["currency"],
        description=description
    )
    
    if trade:
        # Clear trade creation data
        context.user_data.pop("trade_creation", None)
        
        # Show success message with trade details
        await update.message.reply_text(
            f"✅ Trade created successfully!\n\n"
            f"📋 <b>Trade Details</b>\n"
            f"ID: <code>{trade['_id']}</code>\n"
            f"Amount: {trade['amount']} {trade['currency']}\n"
            f"Description: {trade['description']}\n\n"
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


def register_handlers(application):
    """Register handlers for the initiate trade module"""
    application.add_handler(CommandHandler("trade", initiate_trade_handler))
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE,
        handle_trade_amount
    ))
    application.add_handler(CallbackQueryHandler(handle_trade_currency, pattern="^currency_"))
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE,
        handle_trade_description
    ))

# Register handlers
application.add_handler(MessageHandler(filters.Regex("^Open New Trade"), open_trade))
