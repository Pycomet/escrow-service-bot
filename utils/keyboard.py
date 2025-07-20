from typing import Optional

import emoji
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.ext import ContextTypes

from config import *
from utils.enums import (
    CallbackDataEnums,
    CryptoCurrencyEnums,
    EmojiEnums,
    FiatCurrencyEnums,
    TradeTypeEnums,
)


async def main_menu(update=None, context=None):
    """Create the main menu keyboard"""
    keyboard = [
        [
            InlineKeyboardButton(
                f"{EmojiEnums.MONEY_BAG.value} Create Trade",
                callback_data=CallbackDataEnums.CREATE_TRADE.value,
            ),
            InlineKeyboardButton(
                f"{EmojiEnums.HANDSHAKE.value} Join Trade",
                callback_data=CallbackDataEnums.JOIN_TRADE.value,
            ),
        ],
        [
            InlineKeyboardButton(
                f"{EmojiEnums.SCROLL.value} Trade History",
                callback_data=CallbackDataEnums.TRADE_HISTORY.value,
            ),
            InlineKeyboardButton(
                f"{EmojiEnums.LOCK.value} My Wallets",
                callback_data=CallbackDataEnums.MY_WALLETS.value,
            ),
        ],
        [
            InlineKeyboardButton(
                f"{EmojiEnums.RULES.value} Rules",
                callback_data=CallbackDataEnums.RULES.value,
            ),
            InlineKeyboardButton(
                f"{EmojiEnums.COMMUNITY.value} Community",
                callback_data=CallbackDataEnums.COMMUNITY.value,
            ),
        ],
        [
            InlineKeyboardButton(
                f"{EmojiEnums.TARGET.value} Affiliate",
                callback_data=CallbackDataEnums.AFFILIATE.value,
            ),
            InlineKeyboardButton(
                f"{EmojiEnums.QUESTION.value} Support",
                callback_data=CallbackDataEnums.SUPPORT.value,
            ),
        ],
    ]

    # Add admin button if user is admin
    if (
        update
        and hasattr(update, "effective_user")
        and update.effective_user.id == ADMIN_ID
    ):
        keyboard.append(
            [InlineKeyboardButton("🛠️ Admin Panel", callback_data="admin_menu")]
        )

    return InlineKeyboardMarkup(keyboard)


def group_menu():
    "Return Join Or Sell"
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=emoji.emojize("Join A Trade :man:"),
                    url="https://t.me/trusted_escrow_bot?message=start",
                )
            ]
        ]
    )
    return keyboard


def trade_menu():
    "Return Join Or Sell"
    keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton("Open New Trade 📒"), KeyboardButton("Join A Trade 📝")],
            [KeyboardButton("Trade History 📚"), KeyboardButton("Rules 📜")],
            [KeyboardButton("Community 🌐"), KeyboardButton("FAQs ❓")],
        ],
        resize_keyboard=True,
    )
    return keyboard


def seller_menu():
    "Return Seller Options"
    keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton(emoji.emojize("Initiate Trade :ledger:"))],
            [KeyboardButton(emoji.emojize("Delete Trade :closed_book:"))],
            [KeyboardButton(emoji.emojize("Trade History :books:"))],
            [KeyboardButton(emoji.emojize("Rules :scroll:"))],
        ],
        resize_keyboard=True,
    )
    return keyboard


def buyer_menu():
    "Return Buyer Options"
    keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton(emoji.emojize("Join Trade :memo:"))],
            [KeyboardButton(emoji.emojize("Report Trade :open_file_folder:"))],
            [KeyboardButton(emoji.emojize("Trade History :books:"))],
            [KeyboardButton(emoji.emojize("Rules :scroll:"))],
        ],
        resize_keyboard=True,
    )
    return keyboard


def agent_menu(balance):
    "Return Agent Options"
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=emoji.emojize("Deposit  :inbox_tray:"),
                    callback_data="deposit",
                )
            ],
            [
                InlineKeyboardButton(
                    text=emoji.emojize(f"Balance {balance}BTC  :moneybag:"),
                    callback_data="d",
                )
            ],
            [
                InlineKeyboardButton(
                    text=emoji.emojize("Withdraw  :outbox_tray:"),
                    callback_data="withdraw",
                )
            ],
            [
                InlineKeyboardButton(
                    text=emoji.emojize("Help  :bulb:"),
                    callback_data="help",
                )
            ],
            [
                InlineKeyboardButton(
                    text=emoji.emojize("History  :book:"),
                    callback_data="agent_trades",
                )
            ],
            [
                InlineKeyboardButton(
                    text=emoji.emojize(":man: Add Bot To Your Group"),
                    callback_data="affiliate",
                )
            ],
        ]
    )
    return keyboard


def give_verdict():
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="Approve Transaction 👍", callback_data="verdict"
                )
            ],
            [InlineKeyboardButton(text="Write Complaint 🚫", callback_data="2")],
        ]
    )
    return keyboard


def confirm(payment_url: str):
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(text="💸 Make Payment", url=payment_url)],
            [
                InlineKeyboardButton(
                    text="💰 Confirm Payment", callback_data="payment_confirmation"
                )
            ],
        ]
    )
    return keyboard


def confirm_goods():
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=emoji.emojize("Received :white_check_mark:"),
                    callback_data="goods_received",
                )
            ],
            [
                InlineKeyboardButton(
                    text=emoji.emojize("Not Received :x:"),
                    callback_data="goods_not_received",
                )
            ],
        ]
    )
    return keyboard


def refunds():
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=emoji.emojize(":man: To Buyer"),
                    callback_data="refund_to_buyer",
                )
            ],
            [
                InlineKeyboardButton(
                    text=emoji.emojize(":man: To Seller"),
                    callback_data="pay_to_seller",
                )
            ],
            [
                InlineKeyboardButton(
                    text=emoji.emojize(" :closed_lock_with_key: Close Trade"),
                    callback_data="close_trade",
                )
            ],
        ]
    )
    return keyboard


def select_trade():
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=emoji.emojize("View Trades IDs"),
                    callback_data="all_trades",
                )
            ],
            [
                InlineKeyboardButton(
                    text=emoji.emojize("Delete A Trade"),
                    callback_data="delete_trade",
                )
            ],
            [InlineKeyboardButton(text="Preview Trade", callback_data="view_trade")],
        ]
    )
    return keyboard


def review_menu():
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=emoji.emojize("🌟 Leave Your Review"), callback_data="review"
                )
            ]
        ]
    )
    return keyboard


def currency_menu(type: Optional[str]):
    """Return currency selection menu using enums"""
    if type == "crypto":
        currencies = [
            (
                f"{EmojiEnums.TETHER.value} {CryptoCurrencyEnums.USDT.value}",
                f"{CallbackDataEnums.CURRENCY_PREFIX.value}{CryptoCurrencyEnums.USDT.value}",
            ),
            # (
            #     f"{EmojiEnums.BITCOIN.value} {CryptoCurrencyEnums.BTC.value}",
            #     f"{CallbackDataEnums.CURRENCY_PREFIX.value}{CryptoCurrencyEnums.BTC.value}",
            # ),
            (
                f"{EmojiEnums.ETHEREUM.value} {CryptoCurrencyEnums.ETH.value}",
                f"{CallbackDataEnums.CURRENCY_PREFIX.value}{CryptoCurrencyEnums.ETH.value}",
            ),
            # (
            #     f"{EmojiEnums.SOLANA.value} {CryptoCurrencyEnums.SOL.value}",
            #     f"{CallbackDataEnums.CURRENCY_PREFIX.value}{CryptoCurrencyEnums.SOL.value}",
            # ),
            # (
            #     f"{EmojiEnums.YELLOW_CIRCLE.value} {CryptoCurrencyEnums.BNB.value}",
            #     f"{CallbackDataEnums.CURRENCY_PREFIX.value}{CryptoCurrencyEnums.BNB.value}",
            # ),
            # (
            #     f"{EmojiEnums.LITECOIN.value} {CryptoCurrencyEnums.LTC.value}",
            #     f"{CallbackDataEnums.CURRENCY_PREFIX.value}{CryptoCurrencyEnums.LTC.value}",
            # ),
            # (
            #     f"{EmojiEnums.DOGECOIN.value} {CryptoCurrencyEnums.DOGE.value}",
            #     f"{CallbackDataEnums.CURRENCY_PREFIX.value}{CryptoCurrencyEnums.DOGE.value}",
            # ),
            # (
            #     f"{EmojiEnums.TRON.value} {CryptoCurrencyEnums.TRX.value}",
            #     f"{CallbackDataEnums.CURRENCY_PREFIX.value}{CryptoCurrencyEnums.TRX.value}",
            # ),
        ]
    else:
        currencies = [
            (
                f"🇺🇸 {FiatCurrencyEnums.USD.value}",
                f"{CallbackDataEnums.CURRENCY_PREFIX.value}{FiatCurrencyEnums.USD.value}",
            ),
            (
                f"🇪🇺 {FiatCurrencyEnums.EUR.value}",
                f"{CallbackDataEnums.CURRENCY_PREFIX.value}{FiatCurrencyEnums.EUR.value}",
            ),
            (
                f"🇬🇧 {FiatCurrencyEnums.GBP.value}",
                f"{CallbackDataEnums.CURRENCY_PREFIX.value}{FiatCurrencyEnums.GBP.value}",
            ),
            (
                f"🇯🇵 {FiatCurrencyEnums.JPY.value}",
                f"{CallbackDataEnums.CURRENCY_PREFIX.value}{FiatCurrencyEnums.JPY.value}",
            ),
        ]

    # Build buttons (2 per row)
    buttons = [
        [
            InlineKeyboardButton(text, callback_data=data)
            for text, data in currencies[i : i + 2]
        ]
        for i in range(0, len(currencies), 2)
    ]

    # Add the cancel button at the end
    buttons.append(
        [
            InlineKeyboardButton(
                f"{EmojiEnums.BACK_ARROW.value} Cancel",
                callback_data=CallbackDataEnums.MENU.value,
            )
        ]
    )

    return InlineKeyboardMarkup(buttons)


async def trade_type_menu():
    """Return trade type selection menu using enums"""
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    f"{EmojiEnums.MONEY_BAG.value} Crypto → Fiat",
                    callback_data=f"{CallbackDataEnums.TRADE_TYPE_PREFIX.value}{TradeTypeEnums.CRYPTO_FIAT.value}",
                ),
                InlineKeyboardButton(
                    "💱 Crypto → Crypto",
                    callback_data=f"{CallbackDataEnums.TRADE_TYPE_PREFIX.value}{TradeTypeEnums.CRYPTO_CRYPTO.value}",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🛒 Crypto → Product",
                    callback_data=f"{CallbackDataEnums.TRADE_TYPE_PREFIX.value}{TradeTypeEnums.CRYPTO_PRODUCT.value}",
                ),
                InlineKeyboardButton(
                    "🔒 Market Shop ",
                    callback_data=f"{CallbackDataEnums.TRADE_TYPE_PREFIX.value}{TradeTypeEnums.MARKET_SHOP.value}",
                ),
            ],
            [
                InlineKeyboardButton(
                    f"{EmojiEnums.BACK_ARROW.value} Cancel",
                    callback_data=CallbackDataEnums.MENU.value,
                )
            ],
        ]
    )
    return keyboard


# Wallet-related menu functions
def wallet_menu():
    """Return wallet management menu"""
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📊 View Balances",
                    callback_data=CallbackDataEnums.WALLET_BALANCES.value,
                ),
                InlineKeyboardButton(
                    "➕ Create Wallet",
                    callback_data=CallbackDataEnums.WALLET_CREATE.value,
                ),
            ],
            [
                InlineKeyboardButton(
                    "📜 Transaction History",
                    callback_data=CallbackDataEnums.WALLET_TRANSACTIONS.value,
                ),
                InlineKeyboardButton(
                    f"{EmojiEnums.REFRESH.value} Refresh Balances",
                    callback_data=CallbackDataEnums.WALLET_REFRESH.value,
                ),
            ],
            [
                InlineKeyboardButton(
                    f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                    callback_data=CallbackDataEnums.MENU.value,
                )
            ],
        ]
    )
    return keyboard


def create_wallet_menu():
    """Return wallet creation menu with supported networks"""
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    f"{EmojiEnums.BITCOIN.value} Bitcoin (BTC)",
                    callback_data="create_wallet_BTC",
                ),
                InlineKeyboardButton(
                    f"{EmojiEnums.ETHEREUM.value} Ethereum (ETH)",
                    callback_data="create_wallet_ETH",
                ),
            ],
            [
                InlineKeyboardButton(
                    f"{EmojiEnums.SOLANA.value} Solana (SOL)",
                    callback_data="create_wallet_SOL",
                ),
                InlineKeyboardButton(
                    f"{EmojiEnums.LITECOIN.value} Litecoin (LTC)",
                    callback_data="create_wallet_LTC",
                ),
            ],
            [
                InlineKeyboardButton(
                    f"{EmojiEnums.DOGECOIN.value} Dogecoin (DOGE)",
                    callback_data="create_wallet_DOGE",
                )
            ],
            [
                InlineKeyboardButton(
                    f"{EmojiEnums.BACK_ARROW.value} Back to Wallets",
                    callback_data=CallbackDataEnums.MY_WALLETS.value,
                )
            ],
        ]
    )
    return keyboard


def wallet_details_menu(wallet_id: str):
    """Return wallet details menu"""
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    f"{EmojiEnums.REFRESH.value} Refresh Balance",
                    callback_data=f"refresh_wallet_{wallet_id}",
                ),
                InlineKeyboardButton(
                    "📜 Transactions", callback_data=f"wallet_txs_{wallet_id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    f"{EmojiEnums.RECEIVE.value} Receive",
                    callback_data=f"receive_to_{wallet_id}",
                ),
                InlineKeyboardButton(
                    f"{EmojiEnums.BACK_ARROW.value} Back to Wallets",
                    callback_data=CallbackDataEnums.MY_WALLETS.value,
                ),
            ],
        ]
    )
    return keyboard


def confirmation_menu(action: str, item_id: str = None):
    """Generic confirmation menu"""
    confirm_data = f"confirm_{action}_{item_id}" if item_id else f"confirm_{action}"
    cancel_data = f"cancel_{action}_{item_id}" if item_id else f"cancel_{action}"

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    f"{EmojiEnums.CHECK_MARK.value} Yes, Confirm",
                    callback_data=confirm_data,
                ),
                InlineKeyboardButton(
                    f"{EmojiEnums.CROSS_MARK.value} Cancel", callback_data=cancel_data
                ),
            ]
        ]
    )
    return keyboard


def back_to_menu():
    """Simple back to menu button"""
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                    callback_data=CallbackDataEnums.MENU.value,
                )
            ]
        ]
    )
    return keyboard


def deposit_confirmation_menu(trade_id: str):
    """Keyboard for deposit confirmation"""
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    f"{EmojiEnums.CHECK_MARK.value} I've Made Deposit",
                    callback_data=f"deposit_made_{trade_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    f"{EmojiEnums.CROSS_MARK.value} Cancel Trade",
                    callback_data=f"cancel_trade_{trade_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    f"{EmojiEnums.QUESTION.value} Support",
                    callback_data=f"support_trade_{trade_id}",
                )
            ],
        ]
    )
    return keyboard


def trade_actions_menu(trade_id: str, user_role: str):
    """Dynamic trade actions menu based on user role"""
    keyboard = []

    if user_role == "seller":
        keyboard.append(
            [
                InlineKeyboardButton(
                    "📋 Trade Details", callback_data=f"trade_details_{trade_id}"
                ),
                InlineKeyboardButton(
                    "🔄 Refresh Status", callback_data=f"refresh_trade_{trade_id}"
                ),
            ]
        )
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"{EmojiEnums.CROSS_MARK.value} Cancel Trade",
                    callback_data=f"cancel_trade_{trade_id}",
                ),
                InlineKeyboardButton(
                    f"{EmojiEnums.QUESTION.value} Support",
                    callback_data=f"support_trade_{trade_id}",
                ),
            ]
        )
    elif user_role == "buyer":
        keyboard.append(
            [
                InlineKeyboardButton(
                    "📋 Trade Details", callback_data=f"trade_details_{trade_id}"
                ),
                InlineKeyboardButton(
                    "💰 Make Payment", callback_data=f"make_payment_{trade_id}"
                ),
            ]
        )
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"{EmojiEnums.CHECK_MARK.value} Goods Received",
                    callback_data=f"goods_received_{trade_id}",
                ),
                InlineKeyboardButton(
                    f"{EmojiEnums.QUESTION.value} Support",
                    callback_data=f"support_trade_{trade_id}",
                ),
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                callback_data=CallbackDataEnums.MENU.value,
            )
        ]
    )

    return InlineKeyboardMarkup(keyboard)
