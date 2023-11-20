from config import *
from keyboard import *
from functions import *

@bot.message_handler(regexp="^Rules")
def rules(msg):
    """
    List of Rules
    """

    user = get_user(msg)
    try:
        message_id = get_msg_id(msg)
        bot.delete_message(user.chat, message_id)
    except:
        pass

    bot.send_message(
        user.id,
        emoji.emojize(
            f"""
:scroll: <b>TELEGRAM ESCROW BOT SERVICE RULES</b> :scroll:
----------------------------------------
1.  Trades can only be created by a seller.

2.  Funds deposited by the buyer are only released to seller after the goods received are affirmed by the buyer.

3.  Transaction price and trade currency should be agreed between both parties before trade is created.

4.  If a party is reported, the other party receives their refund and the guilty party banned from this service.
            """,
            
        ),
        parse_mode="html",
    )
