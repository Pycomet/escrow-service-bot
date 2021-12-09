from config import *
from handlers.history import *
from handlers.initiate_trade import *
from handlers.rules import rules
from keyboard import *
from functions import *
from bot import *
from affiliate import *
from agent import *

from handlers.verdict import *

# Callback Handlers
@bot.callback_query_handler(func=lambda call: True)
def callback_answer(call):
    """
    Button Response
    """

    # FIRST OPTIONS
    if call.data == "seller":
        start_seller(call)
        bot.delete_message(call.message.chat.id, call.message.message_id)

    elif call.data == "buyer":
        start_buyer(call)
        bot.delete_message(call.message.chat.id, call.message.message_id)

    elif call.data == "affiliate":
        start_affiliate(call)
        bot.delete_message(call.message.chat.id, call.message.message_id)


    #AGENT ACTIONS
    elif call.data == "deposit":
        pull_agent_address(call)

    elif call.data == "withdraw":
        question = bot.send_message(
            call.from_user.id,
            emoji.emojize(":point_right: Paste the address and amount to make payments into (Bitcoin Wallets Only) - E.g '14Ug4KS3cwvReFqqEmBbb5wJTuGKmtrHJr-0.0034'", use_aliases=True),
        )
        question = question.wait()
        bot.register_next_step_handler(question, pay_withdrawal)

    elif call.data == "help":
        bot.send_message(
            call.from_user.id,
            emoji.emojize(
                f"""
    <b>Please contact @Telescrowbotsupport if you run into any technical difficulty</b>
                """,
                use_aliases=True
            ),
            parse_mode='HTML',
    )

    elif call.data == "agent_trades":
        pull_agent_trades(call)


    #CURRENCY OPTIONS
    elif call.data == "dollar":
        #create trade
        open_new_trade(call, "USD")
        select_coin(call.from_user)
        bot.delete_message(call.message.chat.id, call.message.message_id)

    elif call.data == "euro":
        #create trade
        open_new_trade(call, "EUR")
        select_coin(call.from_user)
        bot.delete_message(call.message.chat.id, call.message.message_id)



    #COIN OPTIONS
    elif call.data == "btc":
        add_coin(
            user=call.from_user,
            coin="BTC")
        trade_price(call.from_user)
        bot.delete_message(call.message.chat.id, call.message.message_id)
    
    elif call.data == "eth":
        add_coin(
            user=call.from_user,
            coin="ETH")
        trade_price(call.from_user)
        bot.delete_message(call.message.chat.id, call.message.message_id)


    # PAYMENT VALIDATION
    elif call.data == "payment_confirmation":
        validate_pay(call)
        # bot.delete_message(call.message.chat.id, call.message.message_id)




    elif call.data == "goods_received":
        ### Pay The Seller
        trade = get_recent_trade(call.from_user)
        status, _ = pay_funds_to_seller(trade)

        print(status)
        ##SEND TO SELLER
        bot.send_message(
            int(trade.seller),
            emoji.emojize(
                ":star: <b>TRANSACTION COMPLETE AND TRADE CLOSE!!. Your payment is on it's way!</b>",
                use_aliases=True
            ),
            parse_mode=telegram.ParseMode.HTML
        )

        ##SEND TO BUYER
        bot.send_message(
            trade.buyer,
            emoji.emojize(
                ":star: <b>TRANSACTION COMPLETE AND TRADE CLOSE!!</b>",
                use_aliases=True
            ),
            parse_mode=telegram.ParseMode.HTML,
        )
        bot.delete_message(call.message.chat.id, call.message.message_id)





    elif call.data == "goods_not_received":
        #### Open Dispute
        bot.send_message(
            call.from_user.id,
            "Please contact the seller to send you the goods right away. If seller refuses, report the trade from the menu",
        )
        bot.delete_message(call.message.chat.id, call.message.message_id)


    elif call.data == "verdict":
        #Pass Verdict
        question = bot.send_message(
            call.from_user.id,
            "What is your final decision to the trade? "
        )
        question = question.wait()
        bot.register_next_step_handler(question, pass_verdict)
        bot.delete_message(call.message.chat.id, call.message.message_id)




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




    elif call.data == "view_all_trades":
        send_all_trades(call)
        bot.delete_message(call.message.chat.id, call.message.message_id)


    elif call.data == "delete_trade":
        question = bot.send_message(
            call.from_user.id,
            emoji.emojize(
                ":warning: What is the ID of the trade ? ",
                use_aliases=True
            )
        )
        question = question.wait()
        bot.register_next_step_handler(question, user_trade_delete)
        bot.delete_message(call.message.chat.id, call.message.message_id)

    else:
        pass

