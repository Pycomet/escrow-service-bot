from config import *
from utils import *
from functions import *
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler
import logging

logger = logging.getLogger(__name__)

async def send_message_or_edit(message, text, reply_markup, is_callback=False, parse_mode=None):
    """Helper function to either send a new message or edit existing one"""
    try:
        if is_callback:
            return await message.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
        else:
            return await message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception as e:
        logger.error(f"Error in send_message_or_edit: {e}")
        raise

async def join_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /join command"""
    try:
        is_callback = bool(update.callback_query)
        message = update.callback_query.message if is_callback else update.message
        
        if is_callback:
            await update.callback_query.answer()
        
        await send_message_or_edit(
            message,
            "🔍 Please enter the Trade ID you want to join:",
            InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
            ]]),
            is_callback
        )
        
        # Set state to wait for trade ID
        context.user_data["state"] = "waiting_for_trade_id"
        logger.info(f"Set state to waiting_for_trade_id for user {update.effective_user.id}")
    except Exception as e:
        logger.error(f"Error in join handler: {e}")
        try:
            message = update.callback_query.message if update.callback_query else update.message
            if message:
                await send_message_or_edit(
                    message,
                    "❌ An error occurred. Please try again later.",
                    InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
                    ]]),
                    bool(update.callback_query)
                )
        except Exception as e2:
            logger.error(f"Error sending error message: {e2}")


async def handle_trade_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the trade ID input"""
    try:
        if context.user_data.get("state") != "waiting_for_trade_id":
            logger.info(f"Ignoring message - state is not waiting_for_trade_id: {context.user_data.get('state')}")
            return
        
        trade_id = update.message.text.strip()
        user_id = update.effective_user.id
        logger.info(f"Processing trade ID {trade_id} for user {user_id}")
        
        # Clear state
        context.user_data.pop("state", None)
        
        # Get trade details
        trade = trades_db.get_trade(trade_id)
        if not trade:
            await update.message.reply_text(
                "❌ Trade not found. Please check the ID and try again.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
                ]])
            )
            return
        
        # Check if trade is available for joining
        status = str(trade.get('status', '')).lower()
        if status != "pending":
            await update.message.reply_text(
                f"❌ This trade is no longer available for joining (Status: {status}).",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
                ]])
            )
            return
        
        # Check if user is already involved in the trade
        seller_id = str(trade.get('seller_id', ''))
        buyer_id = str(trade.get('buyer_id', ''))
        if str(user_id) in [seller_id, buyer_id]:
            await update.message.reply_text(
                "❌ You are already involved in this trade.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
                ]])
            )
            return
        
        # Store trade ID in context for later use
        context.user_data["join_trade_id"] = trade_id
        
        # Show trade details and confirmation
        amount = str(trade.get('amount', '0'))
        currency = str(trade.get('currency', 'Unknown'))
        created_at = str(trade.get('created_at', 'Unknown'))
        description = str(trade.get('description', ''))
        
        details = (
            f"📋 <b>Trade Details</b>\n\n"
            f"ID: <code>{trade_id}</code>\n"
            f"Amount: {amount} {currency}\n"
            f"Created: {created_at}\n"
        )
        
        if description:
            details += f"\nDescription: {description}\n"
        
        details += "\nWould you like to join this trade as a buyer?"
        
        await update.message.reply_text(
            details,
            parse_mode="html",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Yes, Join Trade", callback_data=f"confirm_join_{trade_id}")],
                [InlineKeyboardButton("❌ No, Cancel", callback_data="menu")]
            ])
        )
    except Exception as e:
        logger.error(f"Error in handle_trade_id: {e}")
        await update.message.reply_text(
            "❌ An error occurred while processing the trade ID. Please try again later.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
            ]])
        )


async def handle_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle join-related callback queries"""
    try:
        query = update.callback_query
        await query.answer()
        
        data = query.data
        logger.info(f"Processing join callback with data: {data}")
        
        if data.startswith("confirm_join_"):
            trade_id = data.replace("confirm_join_", "")
            user_id = query.from_user.id
            
            # Join the trade
            success = trades_db.join_trade(trade_id, user_id)
            if success:
                # Get updated trade info
                trade = trades_db.get_trade(trade_id)
                
                # Notify seller if trade exists
                if trade and trade.get('seller_id'):
                    try:
                        await context.bot.send_message(
                            chat_id=trade['seller_id'],
                            text=f"✅ A new buyer has joined your trade #{trade_id}.",
                            parse_mode="html"
                        )
                    except Exception as e:
                        logger.error(f"Failed to notify seller: {e}")
                
                # Confirm to buyer
                await query.message.edit_text(
                    f"✅ You have successfully joined trade #{trade_id}.\n\n"
                    "Please proceed with the payment to complete the trade.",
                    parse_mode="html",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("💳 Make Payment", callback_data=f"pay_{trade_id}"),
                        InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
                    ]])
                )
            else:
                await query.message.edit_text(
                    "❌ Failed to join trade. The trade may no longer be available.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
                    ]])
                )
    except Exception as e:
        logger.error(f"Error in handle_join_callback: {e}")
        try:
            if query and query.message:
                await query.message.edit_text(
                    "❌ An error occurred while joining the trade. Please try again later.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
                    ]])
                )
        except Exception as e2:
            logger.error(f"Error sending error message: {e2}")


def register_handlers(application):
    """Register handlers for the join module"""
    application.add_handler(CommandHandler("join", join_handler))
    # Handle text messages for trade ID input
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE,
        handle_trade_id
    ))
    # Handle join-related callbacks
    application.add_handler(CallbackQueryHandler(handle_join_callback, pattern="^confirm_join_"))
