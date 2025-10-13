from datetime import datetime
from typing import Optional

from config import *
from database import *
from utils.enums import EmojiEnums, MessageTypeEnums, TradeStatusEnums


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
        return f"{EmojiEnums.CROSS_MARK.value} An error occurred. Please try again or contact support."

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
            coin_symbol = coin_address["coin_symbol"]
            address = coin_address["address"]
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
                coin_symbol = coin_address["coin_symbol"]
                address = coin_address["address"]
                balance = coin_address.get("balance", "0")

                coin_emoji = {
                    "BTC": EmojiEnums.BITCOIN.value,
                    "LTC": EmojiEnums.LITECOIN.value,
                    "DOGE": EmojiEnums.DOGECOIN.value,
                    "ETH": EmojiEnums.ETHEREUM.value,
                    "SOL": EmojiEnums.SOLANA.value,
                    "USDT": EmojiEnums.TETHER.value,
                    "BNB": EmojiEnums.YELLOW_CIRCLE.value,
                    "TRX": EmojiEnums.TRON.value,
                }.get(coin_symbol, "🪙")

                details_text += f"{coin_emoji} <b>{coin_symbol}</b>\n"
                details_text += f"   💰 Balance: {balance}\n"
                details_text += f"   📍 <code>{address}</code>\n\n"

        return details_text

    # ========== TRADE MESSAGES ==========
    @staticmethod
    def trade_created(trade: TradeType) -> str:
        return f"""
📝 <b>New Escrow Trade Created</b>

🆔 <b>Trade ID:</b> <code>{trade['_id']}</code>
💰 <b>Amount:</b> {trade['price']} {trade['currency']}
📋 <b>Terms:</b> {trade.get('terms', 'No terms specified')}
📅 <b>Created:</b> {datetime.strftime(trade['created_at'], "%Y-%m-%d %H:%M:%S")}

Share your Trade ID with the buyer to let them join this trade.
            """

    @staticmethod
    def trade_joined(trade: TradeType, status: str) -> str:
        return f"""
🤝 <b>Trade Joined Successfully</b>

🆔 <b>Trade ID:</b> <code>{trade['_id']}</code>
💰 <b>Amount:</b> {trade['price']} {trade['currency']}
📋 <b>Terms:</b> {trade.get('terms', 'No terms specified')}
📊 <b>Status:</b> {status}

Follow the payment instructions and confirm when complete.
                """

    @staticmethod
    def trade_details(trade: TradeType, status: str) -> str:
        return f"""
📊 <b>Trade Details</b>

🆔 <b>Trade ID:</b> <code>{trade['_id']}</code>
💰 <b>Amount:</b> {trade['price']} {trade['currency']}
📋 <b>Terms:</b> {trade.get('terms', 'No terms specified')}
📊 <b>Status:</b> {status}
🔄 <b>Active:</b> {'Yes' if trade.get('is_active') else 'No'}

👤 <b>Seller:</b> {trade.get('seller_id', 'N/A')}
👤 <b>Buyer:</b> {trade.get('buyer_id', 'None yet')}
📅 <b>Created:</b> {datetime.strftime(trade['created_at'], "%Y-%m-%d %H:%M:%S")}
            """

    @staticmethod
    def deposit_instructions(
        amount: float, currency: str, description: str, payment_url: str, trade_id: str
    ) -> str:
        """Generates the message for crypto deposit instructions (BTCPay-based)."""
        from functions.trade import TradeClient

        fee_amount, total_deposit_required = TradeClient.calculate_trade_fee(amount)

        return f"""
🔒 <b>Crypto Deposit Required for Trade ID: {trade_id}</b> 🔒
--------------------------------------------------

To proceed with this trade, you (the seller) need to deposit the specified crypto amount into escrow.

<b>📊 Deposit Breakdown:</b>
• Amount to buyer: <b>{amount} {currency}</b>
• Bot service fee: <b>{fee_amount} {currency}</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>💳 Total Deposit Required: {total_deposit_required} {currency}</b>

<b>📋 Trade Terms:</b> {description}

Please use the secure payment link below to make your deposit. This will take you to our payment provider where you can complete the transaction.

➡️ <b><a href="{payment_url}">Make Deposit Now</a></b>

After you have successfully made the deposit, please click the "✅ I've Made Deposit" button which will appear with the deposit link.

If you encounter any issues, please contact support.
        """

    @staticmethod
    def wallet_deposit_instructions(
        amount: float,
        currency: str,
        description: str,
        receiving_address: str,
        trade_id: str,
    ) -> str:
        """Generates the message for wallet-based crypto deposit instructions (ETH/USDT)."""
        from functions.scripts.utils import get_eth_price
        from functions.trade import TradeClient

        # Use new gas-inclusive fee calculation
        fee_data = TradeClient.calculate_trade_fee_with_gas(amount, currency)
        gas_info = TradeClient.get_gas_requirements_for_currency(currency)

        breakdown = fee_data["breakdown"]

        # Get ETH price for USD equivalent and format gas fees properly
        eth_price = get_eth_price()
        gas_fees_usd = ""

        # Format ETH gas fees to avoid scientific notation
        def format_eth_amount(amount):
            """Format small ETH amounts to avoid scientific notation"""
            if amount < 0.0001:
                return f"{amount:.8f}"  # Show 8 decimal places for very small amounts
            elif amount < 0.001:
                return f"{amount:.6f}"  # Show 6 decimal places for small amounts
            else:
                return f"{amount:.4f}"  # Show 4 decimal places for larger amounts

        formatted_gas_fees = format_eth_amount(fee_data["total_gas_fees"])

        if eth_price and fee_data["total_gas_fees"]:
            usd_value = fee_data["total_gas_fees"] * eth_price
            gas_fees_usd = f" (~${usd_value:.2f} USD)"

        if currency == "ETH":
            # ETH trades: all costs combined
            formatted_gas_fees_eth = format_eth_amount(fee_data["total_gas_fees"])
            formatted_total_deposit = format_eth_amount(
                fee_data["total_deposit_required"]
            )

            return f"""
🔒 <b>ETH Deposit Required for Trade ID: {trade_id}</b> 🔒
--------------------------------------------------

<b>💰 Deposit Address (ETH):</b>
<code>{receiving_address}</code>

<b>📊 Deposit Breakdown:</b>
• Amount to buyer: <b>{breakdown['amount_to_buyer']} ETH</b>
• Bot service fee: <b>{breakdown['bot_fee']} ETH</b>
• Gas fees: <b>{formatted_gas_fees_eth} ETH</b>{gas_fees_usd}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>💳 Total Deposit Required: {formatted_total_deposit} ETH</b>

<b>🔥 Gas Fee Info:</b>
{gas_info['explanation']}. Covers all transaction fees for buyer payout and bot fee transfer.

<b>📋 Trade Terms:</b> {description}

<b>⚠️ Important Instructions:</b>
• Send exactly <b>{formatted_total_deposit} ETH</b> to the address above
• Must be sent on Ethereum network
• Gas fees calculated with 20% buffer for price fluctuations
• Double-check address before sending
• This address is unique to your wallet

After you have successfully made the deposit, click "✅ I've Made Deposit" to confirm.
        """

        else:  # USDT and other tokens
            return f"""
🔒 <b>{currency} Deposit Required for Trade ID: {trade_id}</b> 🔒
--------------------------------------------------

<b>💰 Deposit Address ({currency}):</b>
<code>{receiving_address}</code>

<b>📊 {currency} Deposit Breakdown:</b>
• Amount to buyer: <b>{breakdown['amount_to_buyer']} {currency}</b>
• Bot service fee: <b>{breakdown['bot_fee']} {currency}</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>💳 Total {currency} Required: {fee_data['total_deposit_required']} {currency}</b>

<b>⚡ ETH Required for Gas Fees:</b>
• Gas fees: <b>{formatted_gas_fees} ETH</b>{gas_fees_usd}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>💳 Total ETH Required: {formatted_gas_fees} ETH</b>

<b>🔥 Why ETH is Required:</b>
{gas_info['eth_required_reason']}. Gas covers all transaction fees for {currency} transfers and bot payouts.

<b>📋 Trade Terms:</b> {description}

<b>⚠️ Critical Instructions:</b>
• Send <b>{fee_data['total_deposit_required']} {currency}</b> to the address above
• Your wallet MUST also have <b>{formatted_gas_fees} ETH</b> for gas fees
• Both must be sent on Ethereum network
• Gas fees calculated with 20% buffer for price fluctuations
• Insufficient ETH will cause transaction failures
• Double-check address before sending

After making both deposits, click "✅ I've Made Deposit" to confirm.
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
        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        f"🔗 Share Trade ID: {trade['_id']}",
                        switch_inline_query=f"Join my escrow trade! ID: {trade['_id']}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "📜 View Trade Details",
                        callback_data=f"view_trade_{trade['_id']}",
                    )
                ],
                [InlineKeyboardButton("🏡 Main Menu", callback_data="menu")],
            ]
        )

    @staticmethod
    def deposit_not_confirmed(trade_id: str, status: Optional[str]) -> str:
        """Message when crypto deposit is not yet confirmed."""
        status_message = (
            f"Current status: {status}"
            if status
            else "We could not detect your deposit yet."
        )
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
        from utils.enums import TradeTypeEnums

        display_name = TradeTypeEnums.get_display_name(trade_type)
        return f"{EmojiEnums.CROSS_MARK.value} Deposit checking is not yet implemented for {display_name} trades."

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
            "BTC": EmojiEnums.BITCOIN.value,
            "ETH": EmojiEnums.ETHEREUM.value,
            "LTC": EmojiEnums.LITECOIN.value,
            "DOGE": EmojiEnums.DOGECOIN.value,
            "SOL": EmojiEnums.SOLANA.value,
            "USDT": EmojiEnums.TETHER.value,
            "BNB": EmojiEnums.YELLOW_CIRCLE.value,
            "TRX": EmojiEnums.TRON.value,
        }

        emoji = currency_emoji_map.get(currency.upper(), "💰")
        return f"{emoji} {amount} {currency.upper()}"

    # ========== CRYPTOFIAT TRADE MESSAGES ==========
    @staticmethod
    def buyer_trade_details(trade: TradeType) -> str:
        """Detailed trade information for buyer in CryptoToFiat trades"""
        return f"""
💰 <b>Crypto → Fiat Trade Details</b>

🆔 <b>Trade ID:</b> <code>{trade['_id']}</code>
💎 <b>You're buying:</b> {trade['price']} {trade['currency']}
📅 <b>Created:</b> {trade.get('created_at', 'Unknown')}
✅ <b>Status:</b> Seller has deposited crypto - Ready for buyer

📋 <b>Payment Instructions from Seller:</b>
<i>{trade.get('terms', 'No specific terms provided')}</i>

<b>🔄 How this trade works:</b>
1. You join as the buyer
2. You make the fiat payment to the seller as per their instructions
3. You submit proof of payment (screenshot/receipt)
4. Seller verifies your payment and releases the crypto
5. You receive {trade['price']} {trade['currency']} in your wallet

<b>⚠️ Important:</b> The seller's crypto ({trade['price']} {trade['currency']}) is already secured in escrow. Only make the fiat payment after joining this trade.
        """

    @staticmethod
    def buyer_joined_success(trade: TradeType) -> str:
        """Success message when buyer joins CryptoToFiat trade"""
        return f"""
{EmojiEnums.CHECK_MARK.value} <b>Successfully Joined Trade #{trade['_id']}!</b>

💰 <b>You're buying:</b> {trade['price']} {trade['currency']}

<b>📋 Next Steps:</b>
1. Make the fiat payment exactly as described in the seller's terms
2. Take a screenshot or photo of your payment confirmation
3. Click 'Submit Payment Proof' below to upload your proof
4. Wait for seller verification (usually within a few hours)
5. Receive your crypto once payment is verified!

<b>⚠️ Payment Instructions:</b>
<i>{trade.get('terms', 'No specific terms provided')}</i>

<b>🔒 Security:</b> The seller's crypto is safely held in escrow. You will only receive it after they verify your payment.
        """

    @staticmethod
    def payment_proof_submitted(trade_id: str) -> str:
        """Message when buyer submits payment proof"""
        return f"""
{EmojiEnums.CHECK_MARK.value} <b>Payment Proof Submitted!</b>

Trade ID: <code>{trade_id}</code>

Your payment proof has been successfully submitted and the seller has been notified.

<b>What happens next:</b>
• The seller will review your payment proof
• If approved, they will release the crypto to you
• You'll be notified of the decision

<b>Estimated review time:</b> Usually within a few hours

Thank you for using our escrow service!
        """

    @staticmethod
    def seller_proof_notification(trade: TradeType) -> str:
        """Notification to seller when buyer submits proof"""
        return f"""
📤 <b>Payment Proof Submitted</b>

Trade ID: <code>{trade['_id']}</code>
The buyer has submitted proof of fiat payment.

Please review and verify the payment proof.
        """

    @staticmethod
    def payment_approved_buyer(trade: TradeType) -> str:
        """Message to buyer when payment is approved"""
        return f"""
🎉 <b>Payment Approved - Crypto Released!</b>

Trade ID: <code>{trade['_id']}</code>

Great news! The seller has approved your payment proof.

💰 <b>You have received:</b> {trade['price']} {trade['currency']}

The crypto has been released from escrow and is now in your wallet.

Thank you for using our escrow service! 🚀
        """

    @staticmethod
    def payment_approved_seller(trade: TradeType) -> str:
        """Message to seller when they approve payment"""
        return f"""
✅ <b>Payment Approved & Crypto Released!</b>

Trade ID: <code>{trade['_id']}</code>

You have successfully approved the buyer's payment.

💰 <b>Released:</b> {trade['price']} {trade['currency']}

The crypto has been released from escrow to the buyer.
The buyer has been notified.

Trade completed successfully! 🎉
        """

    @staticmethod
    def payment_rejected_buyer(trade_id: str, reason: str) -> str:
        """Message to buyer when payment proof is rejected"""
        return f"""
❌ <b>Payment Proof Rejected</b>

Trade ID: <code>{trade_id}</code>

Unfortunately, the seller has rejected your payment proof.

<b>Reason:</b> <i>{reason}</i>

<b>What you can do:</b>
• Review the seller's payment instructions again
• Make the correct payment if needed
• Submit new payment proof
• Contact support if you believe this is an error

The trade is still active - you can submit new proof.
        """

    @staticmethod
    def payment_rejected_seller(trade_id: str, reason: str) -> str:
        """Message to seller when they reject payment proof"""
        return f"""
❌ <b>Payment Proof Rejected</b>

Trade ID: <code>{trade_id}</code>

You have rejected the buyer's payment proof.

<b>Reason provided:</b> <i>{reason}</i>

The buyer has been notified and can submit new proof.
You will be notified if they submit additional proof.
        """
