from config import *


def main_menu(msg):
    "Return Main Menu Keyboard"

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    a = types.InlineKeyboardButton(text="Get Started ➡️", callback_data="start_trade")
    b = types.InlineKeyboardButton(text="Terms & Rules 📚", callback_data="rules")
    c = types.InlineKeyboardButton(text=emoji.emojize("Join A Trade :man:", ), url="https://t.me/tele_escrowbot?message=start")

    if msg.chat.type == "private":
        keyboard.add(a,b)
    else:
        keyboard.add(c,b)
    
    return keyboard

def group_menu():
    "Return Join Or Sell"
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    a = types.InlineKeyboardButton(text=emoji.emojize("Join A Trade :man:", ), url="https://t.me/tele_escrowbot?message=start")
    keyboard.add(a)
    return keyboard



def trade_menu():
    "Return Join Or Sell"
    keyboard = types.ReplyKeyboardMarkup(row_width=2)
    a = types.KeyboardButton("Open New Trade 📒")
    b = types.KeyboardButton("Join A Trade 📝")
    c = types.KeyboardButton("Trade History 📚")
    d = types.KeyboardButton("Rules 📜")
    e = types.KeyboardButton("Community 🌐")
    f = types.KeyboardButton("FAQs ❓")

    keyboard.add(a,b,c,d,e,f)
    return keyboard


def seller_menu():
    "Return Seller Options"

    keyboard = types.ReplyKeyboardMarkup(row_width=2)
    a = types.KeyboardButton(emoji.emojize("Initiate Trade :ledger:", ))
    b = types.KeyboardButton(emoji.emojize("Delete Trade :closed_book:", ))
    c = types.KeyboardButton(emoji.emojize("Trade History :books:", ))
    d = types.KeyboardButton(emoji.emojize("Rules :scroll:", ))

    keyboard.add(a,b,c,d)
    return keyboard


def buyer_menu():
    "Return Buyer Options"

    keyboard = types.ReplyKeyboardMarkup(row_width=2)
    a = types.KeyboardButton(emoji.emojize("Join Trade :memo:", ))
    b = types.KeyboardButton(emoji.emojize("Report Trade :open_file_folder:", ))
    c = types.KeyboardButton(emoji.emojize("Trade History :books:", ))
    d = types.KeyboardButton(emoji.emojize("Rules :scroll:", ))

    keyboard.add(a,b,c,d)
    return keyboard

def agent_menu(balance):
    "Return Agent Options"
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    a = types.InlineKeyboardButton(text=emoji.emojize("Deposit  :inbox_tray:", ), callback_data="deposit")
    b = types.InlineKeyboardButton(text=emoji.emojize(f"Balance {balance}BTC  :moneybag:", ), callback_data="d")
    c = types.InlineKeyboardButton(text=emoji.emojize("Withdraw  :outbox_tray:", ), callback_data="withdraw")
    d = types.InlineKeyboardButton(text=emoji.emojize("Help  :bulb:", ), callback_data="help")
    e = types.InlineKeyboardButton(text=emoji.emojize("History  :book:", ), callback_data="agent_trades")
    f = types.InlineKeyboardButton(text=emoji.emojize(":man: Add Bot To Your Group", ), callback_data="affiliate")

    keyboard.add(a,b,c,d,e,f)
    return keyboard

def local_currency_menu():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    a = types.InlineKeyboardButton(text=emoji.emojize("🇺🇸 US Dollars (USD)", ), callback_data="dollar")
    # b = types.InlineKeyboardButton(text=emoji.emojize(":euro: Euros (EUR)", ), callback_data="euro")    
    keyboard.add(a)
    return keyboard



def give_verdict():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    a = types.InlineKeyboardButton(text="Approve Transaction 👍", callback_data="verdict")
    b = types.InlineKeyboardButton(text="Write Complaint 🚫", callback_data="2")
    
    keyboard.add(a,b)
    return keyboard

def confirm(payment_url: str):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    a = types.InlineKeyboardButton(text="💸 Make Payment", url=payment_url),
    # a = types.InlineKeyboardButton(text=emoji.emojize("🔄 Refresh Status", ), callback_data="payment_confirmation")
    b = types.InlineKeyboardButton(text="💰 Confirm Payment", callback_data="payment_confirmation")
    keyboard.add(a,b)
    return keyboard

def confirm_goods():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    a = types.InlineKeyboardButton(text=emoji.emojize("Received :white_check_mark:", ), callback_data="goods_received")
    b = types.InlineKeyboardButton(text=emoji.emojize("Not Received :x:", ), callback_data="goods_not_received")
    keyboard.add(a, b)
    return keyboard

def refunds():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    a = types.InlineKeyboardButton(text=emoji.emojize(":man: To Buyer", ), callback_data="refund_to_buyer")
    b = types.InlineKeyboardButton(text=emoji.emojize(":man: To Seller", ), callback_data="pay_to_seller")
    c = types.InlineKeyboardButton(text=emoji.emojize(" :closed_lock_with_key: Close Trade", ), callback_data="close_trade")
    keyboard.add(a, b, c)
    return keyboard


def select_trade():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    a = types.InlineKeyboardButton(text=emoji.emojize("View Trades IDs", ), callback_data="all_trades")
    b = types.InlineKeyboardButton(text=emoji.emojize("Delete A Trade", ), callback_data="delete_trade")
    c = types.InlineKeyboardButton(text="Preview Trade", callback_data="view_trade")
    keyboard.add(a, b,c)
    return keyboard



def review_menu():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    a = types.InlineKeyboardButton(text=emoji.emojize("🌟 Leave Your Review"), callback_data="review")
    keyboard.add(a)
    return keyboard


    a = types.InlineKeyboardButton(text="Approve Transaction 👍", callback_data="approve_transaction")
    b = types.InlineKeyboardButton(text="Write Complaint 🚫", callback_data="write_complaint")
    review_keyboard = types.InlineKeyboardMarkup(row_width=1).add(a,b)