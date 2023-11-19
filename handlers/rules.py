from config import *
from keyboard import *
from functions import *

@bot.message_handler(regexp="^Rules")
def rules(msg):
    """
    List of Rules
    """

    chat, id = get_received_msg(msg)
    bot.delete_message(chat.id, id)

    bot.send_message(
        msg.from_user.id,
        emoji.emojize(
            f"""
:scroll: <b>TELE ESCROW SERVICE RULES</b> :scroll:
----------------------------------------
1.  Trades can only be created by a seller.

2.  Funds deposited by the buyer are only released to seller after the goods received are affirmed by the buyer.

3.  Transaction price and trade currency should be agreed between both parties before trade is created.

4.  If a party is reported, the other party receives their refund and the guilty party banned from this service.
            """,
            
        ),
        parse_mode="html",
    )
