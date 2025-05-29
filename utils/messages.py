from config import *
from database import *


class Messages:

    @staticmethod
    def welcome(name: str) -> str:
        return f"""
🎪 <b>Welcome to the Telegram Escrow Service {name} </b>
    
My purpose is to create a save trade environment for both seller and buyer subject to my rules.

Your funds are save with me and will be refunded to you if the other party refuses to comply with the rules.
            """
    

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