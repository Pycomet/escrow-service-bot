from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from database.types import UserType
from functions.trade import TradeClient
from functions.user import UserClient
from utils.messages import Messages
import logging

logger = logging.getLogger(__name__)

class CryptoFiatFlow:
    @staticmethod
    async def handle_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the Crypto to Fiat trade flow"""
        current_step = context.user_data.get("trade_creation", {}).get("step")
        
        if current_step == "description":
            return await CryptoFiatFlow.handle_description(update, context)
        elif current_step == "deposit":
            return await CryptoFiatFlow.handle_deposit(update, context)
        else:
            logger.warning(f"Unexpected step in CryptoFiatFlow: {current_step}")
            return False

    @staticmethod
    async def handle_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the trade description and move to deposit step"""
        description = update.message.text
        trade_data = context.user_data["trade_creation"]
        
        # Get user from database
        user = UserClient.get_user(update.message)
        
        # Create the trade
        trade = TradeClient.open_new_trade(
            update.message,
            currency=trade_data["currency"],
            trade_type="CryptoToFiat"
        )
        
        if not trade:
            await update.message.reply_text(
                "❌ Failed to create trade. Please try again.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
                ]])
            )
            return False
        
        # Update trade with description and amount using database user object
        TradeClient.add_terms(user, description)
        TradeClient.add_price(user, trade_data["amount"])
        
        # Get payment URL for crypto deposit
        payment_url = TradeClient.get_invoice_url(trade)
        
        if not payment_url:
            await update.message.reply_text(
                "❌ Failed to generate payment URL. Please try again.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
                ]])
            )
            return False
        
        # Update step to deposit
        context.user_data["trade_creation"]["step"] = "deposit"
        
        # Send deposit instructions
        await update.message.reply_text(
            f"🔒 To create this Crypto to Fiat trade, you need to deposit the crypto first.\n\n"
            f"Amount: {trade_data['amount']} {trade_data['currency']}\n"
            f"Description: {description}\n\n"
            f"Please click the button below to make your deposit:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💰 Make Deposit", url=payment_url)],
                [InlineKeyboardButton("✅ I've Made the Deposit", callback_data="check_deposit")],
                [InlineKeyboardButton("❌ Cancel", callback_data="menu")]
            ])
        )
        return True

    @staticmethod
    async def handle_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the deposit confirmation"""
        # Get user from database instead of using effective_user
        user = UserClient.get_user(update.message or update.callback_query.message)
        trade = TradeClient.get_most_recent_trade(user)
        
        if not trade:
            await (update.message or update.callback_query.message).reply_text(
                "❌ Could not find your trade. Please start over.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
                ]])
            )
            return False
        
        # Check payment status
        status = TradeClient.get_invoice_status(trade)
        
        if status and status.lower() in ["paid", "completed", "confirmed"]:
            # Clear trade creation data
            context.user_data.pop("trade_creation", None)
            
            # Create forward text for sharing
            forward_text = (
                f"🔒 New Crypto to Fiat Trade\n"
                f"ID: {trade['_id']}\n"
                f"Amount: {trade['price']} {trade['currency']}\n"
                f"Status: Crypto Deposited ✅"
            )
            
            # Send success message
            await (update.message or update.callback_query.message).reply_text(
                f"✅ Deposit confirmed! Your trade is now active.\n\n"
                f"Share this trade ID with the buyer: <code>{trade['_id']}</code>\n\n"
                f"The buyer will need to pay {trade['price']} {trade['currency']} "
                f"to complete this trade.",
                parse_mode="html",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📤 Forward to Contact", switch_inline_query=forward_text)],
                    [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]
                ])
            )
            return True
        else:
            await (update.message or update.callback_query.message).reply_text(
                "❌ Deposit not yet confirmed. Please try again after making the deposit.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💰 Check Again", callback_data="check_deposit")],
                    [InlineKeyboardButton("❌ Cancel", callback_data="menu")]
                ])
            )
            return False
