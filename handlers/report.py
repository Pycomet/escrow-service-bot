from config import *
from keyboard import *
from functions import *

@bot.message_handler(regexp="^Report")
def report_request(msg):
    """
    Sends a report to the Admin regarding a particular trade
    """
    chat, id = get_received_msg(msg)
    bot.delete_message(chat.id, id)
    
    question = bot.send_message(
        msg.from_user.id,
        emoji.emojize(
            "What is the ID of the trade you wish to report :grey_question:",
            
        )
    )
    
    
    bot.register_next_step_handler(question, report_trade)

def report_trade(msg):
    """
    Send reports to admin for cross checking
    """
    trade = get_trade(msg.text)

    if trade != "Not Found":

        user = msg.from_user
        dispute = create_dispute(user, trade)

        question = bot.send_message(
            msg.from_user.id,
            emoji.emojize(
                f"What is your complaint on <b>Trade -> {msg.text}</b> :grey_question:",
                
            ),
            parse_mode="html",
        )
        

        bot.register_next_step_handler(question, trade_complaint)

    else:
        bot.send_message(
            msg.from_user.id,
            emoji.emojize(
                ":warning: Trade Not Found!",
                
            )
        )
    

def trade_complaint(msg):
    """
    User complaint on Trade
    """

    dispute = get_dispute(msg.from_user.id)

    add_complaint(
        dispute = dispute,
        text = msg.text,
    )

    trade = dispute.trade

    users = [trade.seller, trade.buyer, ADMIN_ID]  

    for user in users:

        bot.send_message(
            user,
            emoji.emojize(
                f":ticket: <b>New Dispute Ticket Created -- {dispute.id}</b>",
                
            ),
            parse_mode="html",
        )


    bot.reply_to(
        msg,
        emoji.emojize(
            ":ticket: Your complaint has been mailed to the administrator. Please await further instructions regarding this trade",
            
        )
    )