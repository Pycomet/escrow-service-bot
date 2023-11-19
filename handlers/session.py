# from config import *
# from keyboard import *
# from functions import AgentAction

# client = AgentAction()

# @bot.message_handler(regexp='/createTrade')
# def start_game(msg):
#     """
#     Group handler to get sgroup trade
#     """
#     # Check To Be Agents Alone
    
#     text = msg.text
#     params = text.split(" ")
    
#     price = int(params[1])
#     seller_address = params[2]

#     if msg.chat.type != "private":
#         trade = client.create_trade(msg.from_user.id, price, seller_address)
        
#         bot.send_message(
#             msg.chat.id,
#             f"""
# <b>Trade Details 📝</b> 
# -----------------------
# <b>ID --> </b> <em>{trade.id}</em>
# <b>Preferred method of payment --> {trade.coin}</b>
# <b>Created on --> {trade.created_at}</b>

# Buyer Should Join This Trade On The Bot To Make Their Payment
#             """,
#             parse_mode="HTML",
#             reply_markup=group_menu()
#         )

        
#     else:
#         pass