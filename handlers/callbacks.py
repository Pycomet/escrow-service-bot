from config import *
from handlers.initiate_trade import *
from handlers.rules import *
from handlers import *
from utils import *
from functions import *
from bot import *
# from affiliate import *
# from agent import *

from handlers.verdict import *
from handlers.history import *
from handlers.delete_trade import *
from handlers.review import *

# Callback Handlers
@bot.callback_query_handler(func=lambda call: True)
def callback_answer(call):
    """
    Button Response
    """

    if call.data == "start_trade":
        start_trade_menu(call)
        bot.delete_message(call.message.chat.id, call.message.message_id)

    elif call.data == "rules":
        rules(call)

    elif call.data == "affiliate":
        start_affiliate(call)
        bot.delete_message(call.message.chat.id, call.message.message_id)


    #AGENT ACTIONS
    elif call.data == "deposit":
        pull_agent_address(call)

    elif call.data == "withdraw":
        question = bot.send_message(
            call.from_user.id,
            emoji.emojize(":point_right: Paste the address and amount to make payments into (Bitcoin Wallets Only) - E.g '14Ug4KS3cwvReFqqEmBbb5wJTuGKmtrHJr-0.0034'", ),
        )
        
        bot.register_next_step_handler(question, pay_withdrawal)

    elif call.data == "help":
        bot.send_message(
            call.from_user.id,
            emoji.emojize(
                f"""
    <b>Please contact @Telescrowbotsupport if you run into any technical difficulty</b>
                """,
                
            ),
            parse_mode='HTML',
    )

    elif call.data == "agent_trades":
        pull_agent_trades(call)


    #CURRENCY OPTIONS
    elif call.data == "dollar":
        #create trade
        open_new_trade(call, "USD")

        trade_terms(call)
        bot.delete_message(call.message.chat.id, call.message.message_id)




    # PAYMENT VALIDATION
    elif call.data == "payment_confirmation":
        validate_pay(call)
        # bot.delete_message(call.message.chat.id, call.message.message_id)



    ###VERDICT DECISION MAKING

    elif call.data == "refund_to_buyer":
        refund_to_buyer(call.from_user)
        bot.delete_message(call.message.chat.id, call.message.message_id)
    
    elif call.data == "pay_to_seller":
        refund_to_seller(call.from_user)
        bot.delete_message(call.message.chat.id, call.message.message_id)

    elif call.data == "close_trade":
        close_dispute_trade(call.from_user)
        bot.delete_message(call.message.chat.id, call.message.message_id)



    # TRADE MANAGER RESPONSE

    elif call.data == "all_trades":
        send_all_trades(call)
        bot.delete_message(call.message.chat.id, call.message.message_id)

    elif call.data == "view_trade":
        send_trade(call)
        bot.delete_message(call.message.chat.id, call.message.message_id)

    elif call.data == "delete_trade":
        question = bot.send_message(
            call.from_user.id,
            emoji.emojize(
                ":warning: What is the ID of the trade ? ",
                
            )
        )
        bot.register_next_step_handler(question, trade_delete)
        bot.delete_message(call.message.chat.id, call.message.message_id)




    elif call.data == "review":
        review(call)


    else:
        pass

