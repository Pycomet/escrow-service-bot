from datetime import time
from config import *
from keyboard import *
from functions import *

agent_client = AgentAction()

@bot.message_handler(commands=['agent'])
def start_agent(msg):
    """
    Starting the escrow service bot
    """
    is_agent, agent = agent_client.check_agent(msg.from_user.id)
    

    if is_agent:
        btc_balance, eth_balance = agent_client.get_balance(agent)
        keyboard = agent_menu(btc_balance)
        # import pdb; pdb.set_trace()

        bot.send_message(
            agent.id,
            emoji.emojize(
                f"Hello Agent {msg.from_user.first_name}",
                
            ),
            reply_markup = keyboard
        )

    else:
        bot.reply_to(
            msg,
            "You are not an Agent!"
        )



def pull_agent_address(msg):
    "Returns Agent's Addresses"
    _ , agent = agent_client.check_agent(msg.from_user.id)

    bot.send_message(
        msg.from_user.id,
        f"""
<em>BTC Wallet </em> <b>{agent.btc_address}</b>
        """,
        parse_mode="html",
    )


def pull_agent_trades(msg):
    trades = agent_client.get_trades(msg.from_user.id)


    bot.send_message(
        msg.from_user.id,
        f"""
    You have a record count of {len(trades)} trades. Keep it up!
        """,
        parse_mode="html",
    )



def pay_withdrawal(msg):
    
    try:
        params = msg.text.split("-")
        payment_adress = params[0]
        amount = params[1]
        
        payout_price = float(amount) - 0.00015
        
        _ , agent = agent_client.check_agent(msg.from_user.id)
        
        result = agent_client.pay_btc(
            agent,
            payout_price,
            payment_adress
        )
        if result is not None:
            bot.send_message(
                msg.from_user.id,
                f"""
            Payment on it's way!
            Txid -> <b>{result}</b>
                """,
                parse_mode="html",
            )
            
        else:
            bot.send_message(
                msg.from_user.id,
                f"""
            Payment failed
            Txid -> <b>{result}</b>
                """,
                parse_mode="html",
            )

        
        
    except Exception as e:
        bot.reply_to(
            msg,
            "You sent an invalid address & amount format!"
        )