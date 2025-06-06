from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from telegram.ext import ContextTypes
from database.types import UserType
from functions.trade import TradeClient
from functions.user import UserClient
from utils.messages import Messages
from utils.keyboard import currency_menu
from utils.enums import TradeTypeEnums
import logging
from functions.wallet import WalletManager

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

        TradeClient.add_terms(terms=description, trade_id=trade['_id'])
        TradeClient.add_price(price=trade_data['amount'], trade_id=trade['_id'])
        
        payment_url = TradeClient.get_invoice_url(trade)
        
        if not payment_url:
            await message.reply_text(
                "❌ Failed to generate payment URL for crypto deposit. Please try again or contact admin.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]])
            )
            # Potentially close or mark the trade as failed if invoice generation is critical
            return False
        
        context.user_data['trade_creation']['current_flow_step'] = AWAITING_DEPOSIT_CONFIRMATION
        
        # Check if this is a wallet-based trade (ETH/USDT)
        is_wallet_currency = trade_data['currency'] in ['ETH', 'USDT']
        
        if is_wallet_currency:
            # Use wallet-based deposit instructions with address
            await message.reply_text(
                Messages.wallet_deposit_instructions(trade_data['amount'], trade_data['currency'], description, payment_url, trade['_id']),
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ I've Made Deposit", callback_data=f"check_deposit_{trade['_id']}")],
                    [InlineKeyboardButton("❌ Cancel Trade", callback_data=f"cancel_trade_{trade['_id']}")]
                ])
            )
        else:
            # Use traditional BTCPay deposit instructions with payment URL
            await message.reply_text(
                Messages.deposit_instructions(trade_data['amount'], trade_data['currency'], description, payment_url, trade['_id']),
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💰 Make Deposit", url=payment_url)],
                    [InlineKeyboardButton("✅ I've Made Deposit", callback_data=f"check_deposit_{trade['_id']}")],
                    [InlineKeyboardButton("❌ Cancel Trade", callback_data=f"cancel_trade_{trade['_id']}")]
                ])
            )
        # Trade creation part of this flow is done, further steps are deposit confirmation
        # The 'trade_creation' dict might be cleared after this, or kept until deposit is confirmed.
        # For now, we keep it until deposit is confirmed.
        return True

    @staticmethod # Renamed from handle_deposit
    async def handle_deposit_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Handles the deposit confirmation for a Crypto-to-Fiat trade."""
        logger.info("=== DEPOSIT CHECK START ===")
        
        query = update.callback_query
        if query:
            logger.info(f"Callback query received: {query.data}")
            await query.answer()
            # Extract trade_id from callback_data if present (e.g., "check_deposit_TRADEID")
            if query.data and query.data.startswith("check_deposit_"):
                trade_id = query.data.split("_", 2)[-1] # Get the part after "check_deposit_"
                logger.info(f"Extracted trade_id from callback: {trade_id}")
            else: # Fallback or if trade_id is expected from context
                trade_id = context.user_data.get('trade_creation', {}).get('trade_id') or \
                           context.user_data.get('active_trade_id_for_deposit_check')
                logger.info(f"Got trade_id from context: {trade_id}")
            
            # Get user from callback query directly
            user_id = str(query.from_user.id)
            chat_id = query.message.chat_id
            logger.info(f"User ID: {user_id}, Chat ID: {chat_id}")

        else: # Should not happen if called by CallbackQueryHandler
            logger.warning("handle_deposit_check called without callback_query.")
            return False

        if not trade_id:
            logger.error("No trade_id found")
            await context.bot.send_message(chat_id, "❌ Could not identify the trade for deposit check. Please try again.")
            return False

        # Fetch the trade using trade_id
        trade = TradeClient.get_trade(trade_id)
        if not trade:
            logger.error(f"Trade {trade_id} not found in database")
            await context.bot.send_message(chat_id, f"❌ Trade {trade_id} not found. Please contact support.")
            return False

        logger.info(f"Trade found: {trade}")
        
        # Ensure the user initiating the check is part of the trade (e.g., seller)
        seller_id = str(trade.get('seller_id'))
        logger.info(f"Checking authorization - User: {user_id}, Seller: {seller_id}")
        
        if user_id != seller_id:
            logger.error(f"Authorization failed - User {user_id} is not seller {seller_id}")
            await context.bot.send_message(chat_id, f"❌ You are not authorized to check this deposit. User: {user_id}, Seller: {seller_id}")
            return False

        logger.info("Authorization passed")

        # Check if this is a wallet-based trade (ETH/USDT)
        is_wallet_trade = trade.get('is_wallet_trade', False) or trade.get('currency') in ['ETH', 'USDT']
        logger.info(f"Is wallet trade: {is_wallet_trade}, Currency: {trade.get('currency')}, is_wallet_trade flag: {trade.get('is_wallet_trade')}")
        
        if is_wallet_trade:
            # Blockchain checking logic - check actual wallet balance
            wallet_manager = WalletManager()
            expected_amount = float(trade.get('price', 0))
            currency = trade.get('currency')
            receiving_address = trade.get('receiving_address')
            
            logger.info(f"Checking wallet balance - Address: {receiving_address}, Expected: {expected_amount} {currency}")
            
            if receiving_address and expected_amount > 0:
                try:
                    # Get the current balance for this address and currency
                    current_balance = wallet_manager.get_balance(receiving_address, currency)
                    logger.info(f"Current balance: {current_balance} {currency}")
                    
                    # Check if the balance meets or exceeds the expected amount
                    if current_balance >= expected_amount:
                        status = "confirmed"
                        logger.info(f"Wallet trade - balance sufficient, status: {status}")
                    elif current_balance > 0:
                        status = "partial"
                        logger.info(f"Wallet trade - partial payment received, status: {status}")
                    else:
                        status = "pending"
                        logger.info(f"Wallet trade - no payment received, status: {status}")
                        
                except Exception as e:
                    logger.error(f"Error checking wallet balance: {e}")
                    status = "error"
                    logger.info(f"Wallet trade - error checking balance, status: {status}")
            else:
                status = "error"
                logger.error(f"Missing wallet info - address: {receiving_address}, amount: {expected_amount}")
                logger.info(f"Wallet trade - missing info, status: {status}")
                
        else:
            # BTCPay invoice checking
            status = TradeClient.get_invoice_status(trade)
            logger.info(f"BTCPay trade - invoice status: {status}")
        
        logger.info(f"Final status check - Status: {status}")
        
        if status and status.lower() in ["paid", "completed", "confirmed", "approved"]:
            logger.info("Deposit confirmed - proceeding with success flow")
            # Trade deposit confirmed
            context.user_data.pop("trade_creation", None) # Clean up trade creation state
            context.user_data.pop("active_trade_id_for_deposit_check", None)

            # Send a new message instead of editing the existing one
            logger.info("Sending deposit confirmation message")
            await context.bot.send_message(
                chat_id,
                Messages.deposit_confirmed_seller(trade), # Message for seller
                parse_mode="HTML",
                reply_markup=Messages.deposit_confirmed_seller_keyboard(trade) # Keyboard for seller
            )
            
            # After deposit confirmed in CryptoFiatFlow
            if status == "confirmed":
                # CryptoToFiat-specific actions:
                # - Notify buyer about fiat payment requirement
                # - Set up fiat payment monitoring
                # - Create fiat payment instructions
                pass
            
            logger.info("=== DEPOSIT CHECK END (SUCCESS) ===")
            return True
        else:
            logger.info("Deposit not confirmed - proceeding with pending flow")
            # Send a new message for status update
            status_message = f"⏳ Checking deposit status for trade {trade_id}...\n\n"
            
            if is_wallet_trade:
                status_message += f"💰 Expected deposit: {trade['price']} {trade['currency']}\n"
                status_message += f"📍 Deposit address: {trade.get('receiving_address', 'Address not found')}\n"
                status_message += f"💳 Current balance: {current_balance if 'current_balance' in locals() else 'Checking...'} {currency}\n\n"
                
                if status == "partial":
                    status_message += "⚠️ <b>Partial payment detected!</b> Please send the remaining amount.\n\n"
                elif status == "error":
                    status_message += "❌ <b>Error checking balance.</b> Please contact support.\n\n"
                else:
                    status_message += "⏳ <b>No payment detected yet.</b> Please ensure you send the exact amount to the address above.\n\n"
                    
                status_message += "We're monitoring the blockchain for your deposit. This updates automatically every few seconds."
                logger.info("Prepared wallet trade status message")
            else:
                status_message += f"Current status: {status or 'Unknown'}\n\n"
                status_message += "Please ensure you have completed the transaction through the payment portal."
                logger.info("Prepared BTCPay trade status message")
            
            logger.info(f"STATUS MESSAGE CONTENT: {status_message}")
            logger.info("Sending status update message")
            await context.bot.send_message(
                chat_id,
                status_message,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Check Again", callback_data=f"check_deposit_{trade_id}")],
                    [InlineKeyboardButton("❌ Cancel Trade", callback_data=f"cancel_trade_{trade_id}")],
                    [InlineKeyboardButton("❓ Support", callback_data=f"support_trade_{trade_id}")]
                ])
            )
            logger.info("=== DEPOSIT CHECK END (PENDING) ===")
            return False

    # Removed handle_flow method
