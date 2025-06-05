from config import *
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from typing import Optional
import emoji

async def main_menu(update=None, context=None):
    """Create the main menu keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("💰 Create Trade", callback_data="create_trade"),
            InlineKeyboardButton("🤝 Join Trade", callback_data="join_trade")
        ],
        [
            InlineKeyboardButton("📜 Trade History", callback_data="trade_history"),
            InlineKeyboardButton("🔐 My Wallets", callback_data="my_wallets")
        ],
        [
            InlineKeyboardButton("📋 Rules", callback_data="rules"),
            InlineKeyboardButton("👥 Community", callback_data="community")
        ],
        [
            InlineKeyboardButton("🎯 Affiliate", callback_data="affiliate"),
            InlineKeyboardButton("❓ Support", callback_data="support")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def group_menu():
    "Return Join Or Sell"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            text=emoji.emojize("Join A Trade :man:"),
            url="https://t.me/trusted_escrow_bot?message=start",
        )]
    ])
    return keyboard


def trade_menu():
    "Return Join Or Sell"
    keyboard = ReplyKeyboardMarkup([
        [KeyboardButton("Open New Trade 📒"), KeyboardButton("Join A Trade 📝")],
        [KeyboardButton("Trade History 📚"), KeyboardButton("Rules 📜")],
        [KeyboardButton("Community 🌐"), KeyboardButton("FAQs ❓")]
    ], resize_keyboard=True)
    return keyboard


def seller_menu():
    "Return Seller Options"
    keyboard = ReplyKeyboardMarkup([
        [KeyboardButton(emoji.emojize("Initiate Trade :ledger:"))],
        [KeyboardButton(emoji.emojize("Delete Trade :closed_book:"))],
        [KeyboardButton(emoji.emojize("Trade History :books:"))],
        [KeyboardButton(emoji.emojize("Rules :scroll:"))]
    ], resize_keyboard=True)
    return keyboard


def buyer_menu():
    "Return Buyer Options"
    keyboard = ReplyKeyboardMarkup([
        [KeyboardButton(emoji.emojize("Join Trade :memo:"))],
        [KeyboardButton(emoji.emojize("Report Trade :open_file_folder:"))],
        [KeyboardButton(emoji.emojize("Trade History :books:"))],
        [KeyboardButton(emoji.emojize("Rules :scroll:"))]
    ], resize_keyboard=True)
    return keyboard


def agent_menu(balance):
    "Return Agent Options"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            text=emoji.emojize("Deposit  :inbox_tray:"),
            callback_data="deposit",
        )],
        [InlineKeyboardButton(
            text=emoji.emojize(f"Balance {balance}BTC  :moneybag:"),
            callback_data="d",
        )],
        [InlineKeyboardButton(
            text=emoji.emojize("Withdraw  :outbox_tray:"),
            callback_data="withdraw",
        )],
        [InlineKeyboardButton(
            text=emoji.emojize("Help  :bulb:"),
            callback_data="help",
        )],
        [InlineKeyboardButton(
            text=emoji.emojize("History  :book:"),
            callback_data="agent_trades",
        )],
        [InlineKeyboardButton(
            text=emoji.emojize(":man: Add Bot To Your Group"),
            callback_data="affiliate",
        )]
    ])
    return keyboard

def give_verdict():
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="Approve Transaction 👍", callback_data="verdict")],
        [InlineKeyboardButton(text="Write Complaint 🚫", callback_data="2")]
    ])
    return keyboard


def confirm(payment_url: str):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="💸 Make Payment", url=payment_url)],
        [InlineKeyboardButton(text="💰 Confirm Payment", callback_data="payment_confirmation")]
    ])
    return keyboard

def confirm_goods():
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            text=emoji.emojize("Received :white_check_mark:"),
            callback_data="goods_received",
        )],
        [InlineKeyboardButton(
            text=emoji.emojize("Not Received :x:"),
            callback_data="goods_not_received",
        )]
    ])
    return keyboard


def refunds():
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            text=emoji.emojize(":man: To Buyer"),
            callback_data="refund_to_buyer",
        )],
        [InlineKeyboardButton(
            text=emoji.emojize(":man: To Seller"),
            callback_data="pay_to_seller",
        )],
        [InlineKeyboardButton(
            text=emoji.emojize(" :closed_lock_with_key: Close Trade"),
            callback_data="close_trade",
        )]
    ])
    return keyboard


def select_trade():
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            text=emoji.emojize("View Trades IDs"),
            callback_data="all_trades",
        )],
        [InlineKeyboardButton(
            text=emoji.emojize("Delete A Trade"),
            callback_data="delete_trade",
        )],
        [InlineKeyboardButton(text="Preview Trade", callback_data="view_trade")]
    ])
    return keyboard


def review_menu():
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            text=emoji.emojize("🌟 Leave Your Review"), 
            callback_data="review"
        )]
    ])
    return keyboard


def currency_menu(type: Optional[str]):
    """Return currency selection menu"""

    if type == "crypto":
        currencies = [
            ("₮ USDT", "currency_USDT"),
            ("₿ BTC", "currency_BTC"),
            ("Ξ ETH", "currency_ETH"),
            ("◎ SOL", "currency_SOL"),
            ("🟡 BNB", "currency_BNB"),
            ("Ł LTC", "currency_LTC"),
            ("Ð DOGE", "currency_DOGE"),
            ("ⓣ TRX", "currency_TRX")
        ]
    else:
        currencies = [
            ("🇺🇸 USD", "currency_USD"),
            ("🇪🇺 EUR", "currency_EUR"),
            ("🇬🇧 GBP", "currency_GBP"),
            ("🇯🇵 JPY", "currency_JPY")
        ]

    # Build buttons (2 per row)
    buttons = [
        [InlineKeyboardButton(text, callback_data=data) for text, data in currencies[i:i+2]]
        for i in range(0, len(currencies), 2)
    ]

    # Add the cancel button at the end
    buttons.append([InlineKeyboardButton("🔙 Cancel", callback_data="menu")])

    return InlineKeyboardMarkup(buttons)


async def trade_type_menu():
    """Return trade type selection menu"""
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💰 Crypto → Fiat", callback_data="trade_type_CryptoToFiat"),
            InlineKeyboardButton("💱 Crypto → Crypto", callback_data="trade_type_CryptoToCrypto")
        ],
        [
            InlineKeyboardButton("🛒 Crypto → Product", callback_data="trade_type_CryptoToProduct"),
            InlineKeyboardButton("🔒 Market Shop ", callback_data="trade_type_MarketShop")
        ],
        [InlineKeyboardButton("🔙 Cancel", callback_data="menu")]
    ])
    return keyboard


# Wallet-related menu functions
def wallet_menu():
    """Return wallet management menu"""
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 View Balances", callback_data="wallet_balances"),
            InlineKeyboardButton("➕ Create Wallet", callback_data="wallet_create")
        ],
        [
            InlineKeyboardButton("📜 Transaction History", callback_data="wallet_transactions"),
            InlineKeyboardButton("💸 Send Crypto", callback_data="wallet_send")
        ],
        [
            InlineKeyboardButton("🔄 Refresh Balances", callback_data="wallet_refresh"),
            InlineKeyboardButton("⚙️ Wallet Settings", callback_data="wallet_settings")
        ],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]
    ])
    return keyboard

def create_wallet_menu():
    """Return wallet creation menu with supported networks"""
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("₿ Bitcoin (BTC)", callback_data="create_wallet_BTC"),
            InlineKeyboardButton("Ξ Ethereum (ETH)", callback_data="create_wallet_ETH")
        ],
        [
            InlineKeyboardButton("◎ Solana (SOL)", callback_data="create_wallet_SOL"),
            InlineKeyboardButton("Ł Litecoin (LTC)", callback_data="create_wallet_LTC")
        ],
        [
            InlineKeyboardButton("Ð Dogecoin (DOGE)", callback_data="create_wallet_DOGE")
        ],
        [InlineKeyboardButton("🔙 Back to Wallets", callback_data="my_wallets")]
    ])
    return keyboard

def wallet_details_menu(wallet_id: str):
    """Return wallet details menu"""
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔄 Refresh Balance", callback_data=f"refresh_wallet_{wallet_id}"),
            InlineKeyboardButton("📜 Transactions", callback_data=f"wallet_txs_{wallet_id}")
        ],
        [
            InlineKeyboardButton("💸 Send", callback_data=f"send_from_{wallet_id}"),
            InlineKeyboardButton("📋 Receive", callback_data=f"receive_to_{wallet_id}")
        ],
        [
            InlineKeyboardButton("⚙️ Settings", callback_data=f"wallet_settings_{wallet_id}"),
            InlineKeyboardButton("🔙 Back to Wallets", callback_data="my_wallets")
        ]
    ])
    return keyboard

