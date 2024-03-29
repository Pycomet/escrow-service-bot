from config import *
from utils import *
from functions import *


@bot.message_handler(regexp="^Open New Trade")
def open_trade(msg):
    """
    This opens a new trade with seller actions
    """
    keyboard = local_currency_menu()

    chat, id = get_received_msg(msg)
    bot.delete_message(chat.id, id)

    user = UserClient.get_user_by_id(msg.from_user.id)

    bot.send_message(
        user["_id"],
        "💰 To create a new trade today, select which is your local currency of choice... ",
        reply_markup=keyboard,
    )


##############TRADE CREATION
def trade_terms(msg):
    """
    Terms of trade
    """
    user = UserClient.get_user(msg)

    question = bot.send_message(
        user["_id"],
        "📝 What are the terms for the escrow contract you are about to create ?",
    )

    bot.register_next_step_handler(question, trade_price)


def trade_price(msg):
    """
    Receive user input on trade price
    """
    # import pdb; pdb.set_trace()
    terms = msg.text
    user = UserClient.get_user_by_id(msg.from_user.id)

    trade = TradeClient.add_terms(user=user, terms=str(terms))

    if trade is None:
        bot.send_message(msg.chat.id, "❌ Unable to find your trade. Please start over")
    else:

        question = bot.send_message(
            user["_id"],
            "💰 How much are you expecting to be paid in your local currency? ",
        )

        bot.register_next_step_handler(question, creating_trade)


def creating_trade(msg):
    """
    Recieve user price input on trade
    """
    price = msg.text
    user = UserClient.get_user_by_id(msg.from_user.id)

    trade = TradeClient.add_price(user=user, price=float(price))

    if trade is None:
        bot.send_message(msg.chat.id, "❌ Unable to find your trade. Please start over")

    else:
        # Get Payment Url
        # payment_url = TradeClient.get_invoice_url(trade=trade)
        trade = TradeClient.get_most_recent_trade(user)

        if payment_url is None:
            bot.send_message(
                msg.chat.id, "❌ Unable to get payment url. Please try again"
            )

        else:

            # Create an inline keyboard with a Forward button
            inline_keyboard = [
                [types.InlineKeyboardButton("Forward", switch_inline_query="")]
            ]
            keyboard_markup = types.InlineKeyboardMarkup(inline_keyboard)

            # Send the message with the inline keyboard
            bot.send_message(
                msg.from_user.id,
                text=Messages.trade_created(trade),
                parse_mode="html",
                reply_markup=keyboard_markup,
            )

            # # Send instructions
            # forward_instruction = "Tap and hold on the message above, then choose 'Forward' to send it to your friends."
            # bot.send_message(msg.from_user.id, text=forward_instruction)
