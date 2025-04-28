from config import *
from utils import *
from functions import *
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler
import logging

logger = logging.getLogger(__name__)

async def review_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /review command"""
    user_id = update.effective_user.id
    
    # Get user's completed trades
    completed_trades = get_completed_trades_by_user_id(user_id)
    if not completed_trades:
        await update.message.reply_text(
            "❌ You don't have any completed trades to review yet.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
            ]])
        )
        return
    
    # Create keyboard with trade options
    keyboard = []
    for trade in completed_trades[:5]:  # Limit to 5 most recent trades
        keyboard.append([
            InlineKeyboardButton(
                f"Trade #{trade['_id']} - {trade['amount']} {trade['currency']}",
                callback_data=f"review_trade_{trade['_id']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")])
    
    message = "📝 Select a trade to review:"
    if update.callback_query:
        await update.callback_query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def handle_review_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle review-related callback queries"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "review":
        # Handle the review button from webhook notifications
        user_id = query.from_user.id
        # Get the trade from the message text
        message_text = query.message.text
        import re
        trade_id_match = re.search(r"Trade.*?\(([^)]+)\)", message_text)
        if trade_id_match:
            trade_id = trade_id_match.group(1)
            trade = get_trade_by_id(trade_id)
            if trade:
                # Store trade ID in context for later use
                context.user_data["review_trade_id"] = trade_id
                await show_rating_keyboard(query)
                return
        
        # If we couldn't get the trade ID from the message or trade not found,
        # show the review menu with all completed trades
        await review_handler(update, context)
        return
    
    if data.startswith("review_trade_"):
        trade_id = data.replace("review_trade_", "")
        trade = get_trade_by_id(trade_id)
        
        if not trade:
            await query.edit_message_text(
                "❌ Trade not found. Please try again.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
                ]])
            )
            return
        
        # Store trade ID in context for later use
        context.user_data["review_trade_id"] = trade_id
        await show_rating_keyboard(query)
    
    elif data.startswith("rate_"):
        rating = int(data.replace("rate_", ""))
        trade_id = context.user_data.get("review_trade_id")
        
        if not trade_id:
            await query.edit_message_text(
                "❌ Error: Trade not found. Please try again.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
                ]])
            )
            return
        
        # Save review to database
        save_review(trade_id, query.from_user.id, rating)
        
        # Clear context
        context.user_data.pop("review_trade_id", None)
        
        await query.edit_message_text(
            f"✅ Thank you for your review! You rated this trade {rating} stars.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
            ]])
        )


async def show_rating_keyboard(query):
    """Show the rating keyboard for a trade"""
    await query.edit_message_text(
        "Please rate your experience with this trade (1-5 stars):\n\n"
        "⭐️ - Poor\n"
        "⭐️⭐️ - Fair\n"
        "⭐️⭐️⭐️ - Good\n"
        "⭐️⭐️⭐️⭐️ - Very Good\n"
        "⭐️⭐️⭐️⭐️⭐️ - Excellent",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⭐️", callback_data="rate_1")],
            [InlineKeyboardButton("⭐️⭐️", callback_data="rate_2")],
            [InlineKeyboardButton("⭐️⭐️⭐️", callback_data="rate_3")],
            [InlineKeyboardButton("⭐️⭐️⭐️⭐️", callback_data="rate_4")],
            [InlineKeyboardButton("⭐️⭐️⭐️⭐️⭐️", callback_data="rate_5")],
            [InlineKeyboardButton("🔙 Cancel", callback_data="menu")]
        ])
    )


def register_handlers(application):
    """Register handlers for the review module"""
    application.add_handler(CommandHandler("review", review_handler))
    application.add_handler(CallbackQueryHandler(handle_review_callback, pattern="^(review|review_trade_|rate_[1-5])"))
