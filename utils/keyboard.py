from config import *
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
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
            InlineKeyboardButton("📋 Rules", callback_data="rules")
        ],
        [
            InlineKeyboardButton("👥 Community", callback_data="community"),
            InlineKeyboardButton("🎯 Affiliate", callback_data="affiliate")
        ],
        [InlineKeyboardButton("❓ Support", callback_data="support")]
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


def local_currency_menu():
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            text=emoji.emojize("🇺🇸 US Dollars (USD)"),
            callback_data="dollar",
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

