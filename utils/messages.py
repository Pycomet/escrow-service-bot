from config import *
from database import *
from utils.enums import EmojiEnums, MessageTypeEnums, TradeStatusEnums
from typing import Optional


class Messages:

    # ========== WELCOME & MENU MESSAGES ==========
    @staticmethod
    def welcome(name: str) -> str:
        return f"""
🎪 <b>Welcome to the Telegram Escrow Service {name} </b>
    
My purpose is to create a save trade environment for both seller and buyer subject to my rules.

Your funds are save with me and will be refunded to you if the other party refuses to comply with the rules.
            """
    
    @staticmethod
    def main_menu_welcome() -> str:
        return (
            f"{EmojiEnums.ROBOT.value} <b>Welcome to the Escrow Service Bot!</b>\n\n"
            "What would you like to do?"
        )

    @staticmethod
    def trade_creation_start() -> str:
        return (
            "📝 Let's create a new trade!\n\n"
            "Please select the type of trade you want to create:"
        )
    
    # ========== ERROR MESSAGES ==========
    @staticmethod
    def trade_creation_in_progress() -> str:
        return (
            f"{EmojiEnums.CROSS_MARK.value} You already have a trade creation in progress. "
            "Please complete it or use /cancel to start over."
        )
    
    @staticmethod
    def active_trade_exists(trade_id: str) -> str:
        return (
            f"{EmojiEnums.CROSS_MARK.value} You already have an active trade (#{trade_id}). "
            "Please complete or cancel your current trade before starting a new one."
        )
    
    @staticmethod
    def generic_error() -> str:
        return (
            f"{EmojiEnums.CROSS_MARK.value} An error occurred. Please try again or contact support."
        )
    
    @staticmethod
    def trade_not_found(trade_id: str) -> str:
        return f"{EmojiEnums.CROSS_MARK.value} Trade {trade_id} not found. Please contact support."
    
    @staticmethod
    def access_denied() -> str:
        return f"{EmojiEnums.CROSS_MARK.value} Access denied. You don't have permission for this action."
    
    # ========== SUPPORT MESSAGES ==========
    @staticmethod
    def support_menu() -> str:
        return (
            f"{EmojiEnums.QUESTION.value} <b>Need Help?</b>\n\n"
            "We're here to help! Choose an option below:"
        )
    
    @staticmethod  
    def faq() -> str:
        return (
            f"{EmojiEnums.QUESTION.value} <b>Frequently Asked Questions</b>\n\n"
            "1. <b>How does the escrow service work?</b>\n"
            "The escrow service holds the buyer's payment until the goods/services are delivered and approved.\n\n"
            "2. <b>What happens if there's a dispute?</b>\n"
            "Both parties can submit evidence, and our team will review the case fairly.\n\n"
            "3. <b>How long does a trade take?</b>\n"
            "Most trades are completed within 24-48 hours, depending on delivery time.\n\n"
            "4. <b>What are the fees?</b>\n"
            "Fees are clearly displayed before creating a trade.\n\n"
            "5. <b>Is my payment secure?</b>\n"
            "Yes, all payments are held securely in escrow until the trade is completed.\n\n"
            "6. <b>Are my crypto wallets secure?</b>\n"
            "Yes, all private keys are encrypted and stored securely. We use industry-standard encryption."
        )

    # ========== WALLET MESSAGES ==========
    @staticmethod
    def wallet_creating() -> str:
        return (
            f"{EmojiEnums.HOURGLASS.value} <b>Creating Your Multi-Currency Wallet</b>\n\n"
            "Please wait while we set up your secure wallet...\n\n"
            f"{EmojiEnums.LOCK.value} Generating master mnemonic phrase\n"
            "🪙 Creating addresses for default coins\n"
            "🛡️ Encrypting all private data\n"
            "💾 Saving to secure database"
        )
    
    @staticmethod
    def wallet_created_success(wallet: dict, coin_addresses: list) -> str:
        success_text = (
            f"{EmojiEnums.CHECK_MARK.value} <b>Wallet Created Successfully!</b>\n\n"
            f"💼 <b>Wallet Name:</b> {wallet['wallet_name']}\n"
            f"🆔 <b>Wallet ID:</b> <code>{wallet['_id']}</code>\n\n"
            f"🪙 <b>Created {len(coin_addresses)} coin addresses:</b>\n"
        )
        
        for coin_address in coin_addresses[:6]:  # Show first 6
            coin_symbol = coin_address['coin_symbol']
            address = coin_address['address']
            display_address = f"{address[:10]}...{address[-6:]}"
            success_text += f"• {coin_symbol}: <code>{display_address}</code>\n"
        
        success_text += (
            f"\n{EmojiEnums.LOCK.value} <b>Security Features:</b>\n"
            f"• All private keys encrypted with AES-256\n"
            f"• Master mnemonic securely stored\n"
            f"• One wallet, multiple currencies\n\n"
            f"{EmojiEnums.WARNING.value} <b>Important:</b> Keep your account secure!"
        )
        
        return success_text
    
    @staticmethod
    def wallet_creation_failed() -> str:
        return (
            f"{EmojiEnums.CROSS_MARK.value} <b>Failed to Create Wallet</b>\n\n"
            "An error occurred while creating your wallet. "
            "Please try again or contact support if the problem persists."
        )
    
    @staticmethod
    def wallet_refreshing() -> str:
        return (
            f"{EmojiEnums.REFRESH.value} <b>Refreshing Wallet Balances</b>\n\n"
            "Please wait while we fetch the latest balance information from the blockchain..."
        )
    
    @staticmethod
    def wallet_refreshed_success() -> str:
        return (
            f"{EmojiEnums.CHECK_MARK.value} <b>Balances Refreshed!</b>\n\n"
            "Your wallet balances have been updated with the latest information from the blockchain."
        )
    
    @staticmethod
    def wallet_refresh_partial() -> str:
        return (
            f"{EmojiEnums.WARNING.value} <b>Refresh Partially Complete</b>\n\n"
            "Some balances may not have been updated due to network issues. "
            "You can try refreshing again in a moment."
        )
    
    @staticmethod
    def wallet_not_found() -> str:
        return f"{EmojiEnums.CROSS_MARK.value} Wallet not found or access denied."
    
    @staticmethod
    def wallet_details(wallet: dict, coin_addresses: list) -> str:
        details_text = f"📊 <b>Wallet Details</b>\n\n"
        details_text += f"💼 <b>Name:</b> {wallet['wallet_name']}\n"
        details_text += f"🆔 <b>ID:</b> <code>{wallet['_id']}</code>\n"
        details_text += f"👤 <b>Owner:</b> {wallet['user_id']}\n"
        details_text += f"🕐 <b>Created:</b> {wallet['created_at'][:16]}\n\n"
        
        if coin_addresses:
            details_text += f"💰 <b>Coin Addresses ({len(coin_addresses)}):</b>\n\n"
            for coin_address in coin_addresses:
                coin_symbol = coin_address['coin_symbol']
                address = coin_address['address']
                balance = coin_address.get('balance', '0')
                
                coin_emoji = {
                    'BTC': EmojiEnums.BITCOIN.value,
                    'LTC': EmojiEnums.LITECOIN.value,
                    'DOGE': EmojiEnums.DOGECOIN.value,
                    'ETH': EmojiEnums.ETHEREUM.value,
                    'SOL': EmojiEnums.SOLANA.value,
                    'USDT': EmojiEnums.TETHER.value,
                    'BNB': EmojiEnums.YELLOW_CIRCLE.value,
                    'TRX': EmojiEnums.TRON.value
                }.get(coin_symbol, '🪙')
                
                details_text += f"{coin_emoji} <b>{coin_symbol}</b>\n"
                details_text += f"   💰 Balance: {balance}\n"
                details_text += f"   📍 <code>{address}</code>\n\n"
        
        return details_text

    # ========== TRADE MESSAGES ==========
    @staticmethod
    def trade_created(trade: TradeType) -> str:
        return f"""
📝 <b>New Escrow Trade Opened (ID - {trade['_id']})</b> 📝
--------------------------------------------------
<b>Terms Of Contract:</b> {trade['terms']}

<b>Transaction Amount:</b> {trade['price']} {trade['currency']}
<b>Preferred Payment Method:</b> Bitcoin
<b>Trade Initiated On:</b> {datetime.strftime(trade['created_at'], "%Y-%m-%d %H:%M:%S")}

Ensure that you only share the unique Trade ID with the counterparty. This will allow them to seamlessly join the trade and complete the transaction. All relevant information will be shared upon joining, or they can proceed with the payment through the portal link above.

Trade window only lasts for 60 minutes, contact the buyer right away.
            """

    @staticmethod
    def trade_joined(trade: TradeType, status: str) -> str:
        return f"""
📝 <b>Trade Payment Details - {trade['_id']}</b> 
-----------------------------------
<b>Terms Of Contract:</b> {trade['terms']}

<b>Transaction Amount:</b> {trade['price']} {trade['currency']}
<b>Preferred Payment Method:</b> Bitcoin
<b>Trade Initiated On:</b> {datetime.strftime(trade['created_at'], "%Y-%m-%d %H:%M:%S")}
<b>Payment Status:</b> {status}

<b>Please follow the url below to make payment on our secured portal. Click the button to confirm after you make payment</b>

You can go to payment portal by clicking the button below.
                """

    @staticmethod
    def trade_details(trade: TradeType, status: str) -> str:
        return f"""
📝 <b>Trade Details - {trade['_id']}</b> 
-----------------------------------
<b>Terms Of Contract:</b> {trade['terms']}
<b>Trade State:</b> {'Active' if trade['is_active'] is True else 'Inactive'}

<b>Buyer's ID: </b> {trade['buyer_id'] if 'buyer_id' in trade else "N/A"}
<b>Seller's ID: </b> {trade['seller_id']}

<b>Transaction Amount:</b> {trade['price']} {trade['currency']}
<b>Preferred Payment Method:</b> Bitcoin
<b>Trade Initiated On:</b> {datetime.strftime(trade['created_at'], "%Y-%m-%d %H:%M:%S")}
<b>Payment Status:</b> {status}
            """

    @staticmethod
    def deposit_instructions(amount: float, currency: str, description: str, payment_url: str, trade_id: str) -> str:
        """Generates the message for crypto deposit instructions."""
        return f"""
🔒 <b>Crypto Deposit Required for Trade ID: {trade_id}</b> 🔒
--------------------------------------------------

To proceed with this trade, you (the seller) need to deposit the specified crypto amount into escrow.

<b>Amount to Deposit:</b> {amount} {currency}
<b>Your Trade Description/Terms:</b> {description}


Please use the secure payment link below to make your deposit. This will take you to our payment provider where you can complete the transaction.

➡️ <b><a href="{payment_url}">Make Deposit Now</a></b>

After you have successfully made the deposit, please click the "✅ I've Made Deposit" button which will appear with the deposit link.

If you encounter any issues, please contact support.
        """

    @staticmethod
    def wallet_deposit_instructions(amount: float, currency: str, description: str, receiving_address: str, trade_id: str) -> str:
        """Generates the message for wallet-based crypto deposit instructions (ETH/USDT)."""
        return f"""
🔒 <b>Crypto Deposit Required for Trade ID: {trade_id}</b> 🔒
--------------------------------------------------

To proceed with this trade, you (the seller) need to deposit the specified crypto amount to your escrow wallet address.

<b>Amount to Deposit:</b> {amount} {currency}
<b>Your Trade Description/Terms:</b> {description}

<b>💰 Deposit Address ({currency}):</b>
<code>{receiving_address}</code>

<b>⚠️ Important:</b>
• Send exactly {amount} {currency} to the address above
• Make sure you're sending on the correct network (Ethereum for ETH/USDT)
• Double-check the address before sending
• This address is unique to your wallet - funds sent here belong to you

After you have successfully made the deposit, please click the "✅ I've Made Deposit" button to confirm.

If you encounter any issues, please contact support.
        """

    @staticmethod
    def deposit_confirmed_seller(trade: TradeType) -> str:
        """Message to seller after their crypto deposit is confirmed."""
        return f"""
✅ <b>Deposit Confirmed for Trade ID: {trade['_id']}</b> ✅
--------------------------------------------------

Your deposit of {trade['price']} {trade['currency']} has been successfully confirmed and is now in escrow.

Your trade is now active! You can share the Trade ID with the buyer:

<b>Trade ID:</b> <code>{trade['_id']}</code>

The buyer will need this ID to join the trade and proceed with their part of the transaction (e.g., making their fiat payment).

We will notify you once the buyer joins and completes their payment.
        """

    @staticmethod
    def deposit_confirmed_seller_keyboard(trade: TradeType):
        """Keyboard for seller after deposit is confirmed."""
        # Example: could include a button to view trade details or go to menu
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(f"🔗 Share Trade ID: {trade['_id']}", switch_inline_query=f"Join my escrow trade! ID: {trade['_id']}")],
            [InlineKeyboardButton("📜 View Trade Details", callback_data=f"view_trade_{trade['_id']}")],
            [InlineKeyboardButton("🏡 Main Menu", callback_data="menu")]
        ])

    @staticmethod
    def deposit_not_confirmed(trade_id: str, status: Optional[str]) -> str:
        """Message when crypto deposit is not yet confirmed."""
        status_message = f"Current status: {status}" if status else "We could not detect your deposit yet."
        return f"""
⏳ <b>Deposit Not Yet Confirmed for Trade ID: {trade_id}</b> ⏳
--------------------------------------------------

{status_message}

Please ensure you have completed the transaction through the payment portal.

If you have made the deposit and it's still not confirmed after some time, please try checking again or contact support.
        """

    # ========== TRADE CANCELLATION MESSAGES ==========
    @staticmethod
    def trade_cancel_confirmation(trade_id: str) -> str:
        return (
            f"{EmojiEnums.WARNING.value} <b>Cancel Trade Confirmation</b>\n\n"
            f"Are you sure you want to cancel trade #{trade_id}?\n\n"
            "This action cannot be undone. If funds have been deposited, "
            "they will be refunded to the original sender."
        )
    
    @staticmethod
    def trade_cancel_not_authorized(trade_id: str) -> str:
        return (
            f"{EmojiEnums.CROSS_MARK.value} <b>Not Authorized</b>\n\n"
            f"You are not authorized to cancel trade #{trade_id}. "
            "Only the seller or buyer involved in this trade can cancel it."
        )
    
    @staticmethod
    def trade_cancelled_success(trade_id: str) -> str:
        return (
            f"{EmojiEnums.CHECK_MARK.value} <b>Trade Cancelled</b>\n\n"
            f"Trade #{trade_id} has been successfully cancelled. "
            "Any deposited funds will be refunded."
        )
    
    @staticmethod
    def trade_cancel_failed(trade_id: str) -> str:
        return (
            f"{EmojiEnums.CROSS_MARK.value} <b>Cancellation Failed</b>\n\n"
            f"Failed to cancel trade #{trade_id}. Please try again or contact support."
        )

    # ========== SUPPORT & REPORT MESSAGES ==========
    @staticmethod
    def support_trade_options(trade_id: str) -> str:
        return (
            f"{EmojiEnums.QUESTION.value} <b>Support for Trade #{trade_id}</b>\n\n"
            "How can we help you with this trade?\n\n"
            "Please select an option below:"
        )
    
    @staticmethod
    def support_ticket_created(ticket_id: str) -> str:
        return (
            f"{EmojiEnums.CHECK_MARK.value} <b>Support Ticket Created</b>\n\n"
            f"Ticket ID: #{ticket_id}\n\n"
            "Our support team has been notified and will respond as soon as possible. "
            "You will receive updates about your ticket here."
        )

    # ========== DEPOSIT CHECK MESSAGES ==========
    @staticmethod
    def deposit_check_not_implemented(trade_type: str) -> str:
        return (
            f"{EmojiEnums.CROSS_MARK.value} Deposit checking is not yet implemented for {trade_type} trades."
        )
    
    @staticmethod
    def invalid_deposit_check() -> str:
        return f"{EmojiEnums.CROSS_MARK.value} Invalid deposit check request. Please try again."

    # ========== LOADING MESSAGES ==========
    @staticmethod
    def loading_please_wait() -> str:
        return f"{EmojiEnums.HOURGLASS.value} Please wait..."
    
    @staticmethod
    def processing_request() -> str:
        return f"{EmojiEnums.HOURGLASS.value} Processing your request..."

    # ========== SUCCESS MESSAGES ==========
    @staticmethod
    def operation_successful() -> str:
        return f"{EmojiEnums.CHECK_MARK.value} Operation completed successfully!"
    
    @staticmethod
    def changes_saved() -> str:
        return f"{EmojiEnums.CHECK_MARK.value} Changes saved successfully!"

    # ========== MESSAGE HELPERS ==========
    @staticmethod
    def format_trade_status(status: str) -> str:
        """Format trade status with appropriate emoji"""
        status_emoji_map = {
            TradeStatusEnums.PENDING.value: EmojiEnums.HOURGLASS.value,
            TradeStatusEnums.CONFIRMED.value: EmojiEnums.CHECK_MARK.value,
            TradeStatusEnums.PARTIAL.value: EmojiEnums.WARNING.value,
            TradeStatusEnums.PAID.value: EmojiEnums.MONEY_BAG.value,
            TradeStatusEnums.COMPLETED.value: EmojiEnums.CHECK_MARK.value,
            TradeStatusEnums.CANCELLED.value: EmojiEnums.CROSS_MARK.value,
            TradeStatusEnums.ERROR.value: EmojiEnums.CROSS_MARK.value,
        }
        
        emoji = status_emoji_map.get(status, "")
        return f"{emoji} {status.title()}" if emoji else status.title()
    
    @staticmethod
    def format_currency(amount: float, currency: str) -> str:
        """Format currency with appropriate emoji"""
        currency_emoji_map = {
            'BTC': EmojiEnums.BITCOIN.value,
            'ETH': EmojiEnums.ETHEREUM.value,
            'LTC': EmojiEnums.LITECOIN.value,
            'DOGE': EmojiEnums.DOGECOIN.value,
            'SOL': EmojiEnums.SOLANA.value,
            'USDT': EmojiEnums.TETHER.value,
            'BNB': EmojiEnums.YELLOW_CIRCLE.value,
            'TRX': EmojiEnums.TRON.value,
        }
        
        emoji = currency_emoji_map.get(currency.upper(), "💰")
        return f"{emoji} {amount} {currency.upper()}"