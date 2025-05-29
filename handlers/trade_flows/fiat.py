from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from telegram.ext import ContextTypes
from database.types import UserType
from functions.trade import TradeClient
from functions.user import UserClient
from utils.messages import Messages
from utils.keyboard import currency_menu
from utils.enums import TradeTypeEnums
import logging

logger = logging.getLogger(__name__)

# State constants for this flow
AWAITING_AMOUNT = "fiat_awaiting_amount"
AWAITING_CURRENCY = "fiat_awaiting_currency"
AWAITING_DESCRIPTION = "fiat_awaiting_description"
AWAITING_DEPOSIT_CONFIRMATION = "fiat_awaiting_deposit_confirmation" # After deposit instructions are sent

class CryptoFiatFlow:
    FLOW_NAME = TradeTypeEnums.CRYPTO_FIAT.value # "CryptoToFiat"

    @staticmethod
    async def start_initial_setup(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """
        Starts the setup for a Crypto-to-Fiat trade.
        Called after the user selects "CryptoToFiat" as the trade type.
        The initial query is the one from selecting the trade type.
        """
        context.user_data['trade_creation']['current_flow_step'] = AWAITING_AMOUNT
        context.user_data['trade_creation']['active_flow_module'] = CryptoFiatFlow.FLOW_NAME
        
        await query.message.edit_text(
            f" Kicking off a <b>{CryptoFiatFlow.FLOW_NAME}</b> trade!\n\n"
            f"First, please tell me the <b>exact amount of cryptocurrency</b> you want to sell. "
            f"For example: <code>0.05</code> for BTC, or <code>150.75</code> for USDT.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Cancel Setup", callback_data="cancel_creation")]
            ])
        )
        return True

    @staticmethod
    async def handle_amount_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Handles the amount input from the user."""
        message = update.message
        try:
            amount = float(message.text)
            if amount <= 0:
                raise ValueError("Amount must be positive")
            
            context.user_data['trade_creation']['amount'] = amount
            context.user_data['trade_creation']['current_flow_step'] = AWAITING_CURRENCY
            
            # Ask for crypto currency
            prompt = "💱 Please select the crypto currency of the asset you're selling:"
            keyboard = currency_menu("crypto") # currency_menu from utils.keyboard
            
            await message.reply_text(prompt, reply_markup=keyboard)
            return True
        except ValueError:
            await message.reply_text(
                "❌ Invalid amount. Please enter a positive number (e.g., 100.50 or 0.1).",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Cancel Setup", callback_data="cancel_creation")]
                ])
            )
            return False # Indicate failure to proceed

    @staticmethod
    async def handle_currency_selection(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Handles the currency selection callback."""
        await query.answer()
        currency = query.data.replace("currency_", "")
        
        context.user_data['trade_creation']['currency'] = currency
        context.user_data['trade_creation']['current_flow_step'] = AWAITING_DESCRIPTION
        
        await query.message.edit_text(
            f" Got it, you're selling <b>{currency}</b>.\n\n"
            f"Now, please provide the <b>full terms of your trade</b>. This is crucial for the buyer.\n"
            f"Be sure to include:\n"
            f"1. <b>Fiat Currency & Amount:</b> The exact fiat amount you expect (e.g., 1200 USD, 950 EUR).\n"
            f"2. <b>Bank/Payment Details:</b> How the buyer should pay you the fiat money (e.g., Bank Name, Account Number, Account Holder Name, SWIFT/BIC if international, or specific instructions for other payment methods like Wise, Revolut, etc.).\n"
            f"3. <b>Other Conditions:</b> Any other important terms, like who pays transaction fees, timelines, or specific instructions for the buyer.\n\n"
            f"<i>Example: \"Selling for 500 EUR. Payment via SEPA bank transfer to John Doe, IBAN DE89370400440532013000, BIC COBADEFFXXX. Buyer covers any bank fees. Will release crypto once fiat is confirmed.\"</i>\n\n"
            f"Please type out all these details clearly in your next message.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Cancel Setup", callback_data="cancel_creation")]
            ])
        )
        return True

    @staticmethod
    async def handle_description_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Handles the trade description input and moves to deposit step."""
        message = update.message
        description = message.text
        trade_data = context.user_data['trade_creation']
        
        user = UserClient.get_user(message)
        if not user:
            await message.reply_text("Error: Could not identify user. Please try /start.")
            return False

        # Ensure required data is present
        required_keys = ['amount', 'currency']
        for key in required_keys:
            if key not in trade_data:
                logger.error(f"Missing key '{key}' in trade_data for CryptoFiatFlow description handling.")
                await message.reply_text(f"❌ Error: Missing trade {key}. Please start over using /trade.")
                context.user_data.pop("trade_creation", None)
                return False
        
        trade = TradeClient.open_new_trade(
            message, # Pass the message object for user extraction by UserClient if needed
            currency=trade_data['currency'], 
            trade_type=CryptoFiatFlow.FLOW_NAME
        )
        
        if not trade:
            await message.reply_text(
                "❌ Failed to create trade in the database. Please try again.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]])
            )
            return False
        
        # Store trade_id in context for potential use in deposit check callback
        context.user_data['trade_creation']['trade_id'] = trade['_id']

        TradeClient.add_terms(user, description, trade['_id']) # Assume add_terms takes trade_id
        TradeClient.add_price(user, trade_data['amount'], trade['_id']) # Assume add_price takes trade_id
        
        payment_url = TradeClient.get_invoice_url(trade)
        
        if not payment_url:
            await message.reply_text(
                "❌ Failed to generate payment URL for crypto deposit. Please try again or contact admin.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]])
            )
            # Potentially close or mark the trade as failed if invoice generation is critical
            return False
        
        context.user_data['trade_creation']['current_flow_step'] = AWAITING_DEPOSIT_CONFIRMATION
        
        await message.reply_text(
            Messages.deposit_instructions(trade_data['amount'], trade_data['currency'], description, payment_url, trade['_id']),
            parse_mode="HTML", # Assuming Messages.deposit_instructions returns HTML
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💰 Make Deposit", url=payment_url)],
                # Pass trade_id in callback for specific check
                [InlineKeyboardButton("✅ I've Made Deposit", callback_data=f"check_deposit_{trade['_id']}")] ,
                [InlineKeyboardButton("❌ Cancel Trade", callback_data=f"cancel_trade_{trade['_id']}")] # Or a generic cancel
            ])
        )
        # Trade creation part of this flow is done, further steps are deposit confirmation
        # The 'trade_creation' dict might be cleared after this, or kept until deposit is confirmed.
        # For now, we keep it until deposit is confirmed.
        return True

    @staticmethod # Renamed from handle_deposit
    async def handle_deposit_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Handles the deposit confirmation for a Crypto-to-Fiat trade."""
        query = update.callback_query
        if query:
            await query.answer()
            message_interface = query.message # To send/edit messages
            # Extract trade_id from callback_data if present (e.g., "check_deposit_TRADEID")
            if query.data and query.data.startswith("check_deposit_"):
                trade_id = query.data.split("_", 2)[-1] # Get the part after "check_deposit_"
            else: # Fallback or if trade_id is expected from context
                trade_id = context.user_data.get('trade_creation', {}).get('trade_id') or \
                           context.user_data.get('active_trade_id_for_deposit_check')

        else: # Should not happen if called by CallbackQueryHandler
            logger.warning("handle_deposit_check called without callback_query.")
            # Try to get trade_id from context if update is not a query (less ideal)
            trade_id = context.user_data.get('trade_creation', {}).get('trade_id')
            message_interface = update.message


        if not trade_id:
            await message_interface.reply_text("❌ Could not identify the trade for deposit check. Please try again.")
            return False

        # Fetch the trade using trade_id
        trade = TradeClient.get_trade(trade_id) # Assuming TradeClient.get_trade(trade_id) exists
        if not trade:
            await message_interface.reply_text(f"❌ Trade {trade_id} not found. Please contact support.")
            return False

        user = UserClient.get_user(message_interface) # Get user from message/query
        if not user:
             await message_interface.reply_text("Error: Could not identify user. Please try /start.")
             return False
        
        # Ensure the user initiating the check is part of the trade (e.g., seller)
        if str(user['_id']) != str(trade.get('seller_id')):
            await message_interface.reply_text("❌ You are not authorized to check this deposit.")
            return False

        status = TradeClient.get_invoice_status(trade) # Assumes trade object is sufficient
        
        if status and status.lower() in ["paid", "completed", "confirmed", "approved"]: # Added "approved"
            # Trade deposit confirmed
            # TradeClient.mark_trade_as_paid(trade_id) # Example: if there's a specific function for this
            
            context.user_data.pop("trade_creation", None) # Clean up trade creation state
            context.user_data.pop("active_trade_id_for_deposit_check", None)

            await message_interface.edit_message_text( # Use edit_message_text if from callback
                Messages.deposit_confirmed_seller(trade), # Message for seller
                parse_mode="HTML",
                reply_markup=Messages.deposit_confirmed_seller_keyboard(trade) # Keyboard for seller
            )
            
            # Also inform the (potential) buyer if the system design requires it at this stage
            # This part depends on how buyers join or are notified.
            # For now, seller is confirmed. Buyer joins using trade_id.
            return True
        else:
            await message_interface.reply_text( # Can't edit if it was a button click that opened a new message
                Messages.deposit_not_confirmed(trade_id, status),
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Check Again", callback_data=f"check_deposit_{trade_id}")],
                    [InlineKeyboardButton("❌ Cancel Trade", callback_data=f"cancel_trade_{trade_id}")],
                    [InlineKeyboardButton("❓ Support", callback_data=f"support_trade_{trade_id}")]
                ])
            )
            return False

    # Removed handle_flow method
