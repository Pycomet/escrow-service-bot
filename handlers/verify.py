from config import *
from functions import *

@bot.message_handler(commands=['newagent'])
def verify(msg):
    """
    Verifying an Agent account
    """
    
    if msg.from_user.id == ADMIN_ID:
        bot.reply_to(
            msg,
            "You are not authorized to use this command."
        )
        
    else:
        

        question = bot.send_message(
            msg.from_user.id,
            emoji.emojize(
                f"""
    :point_right: Paste in the User's ID?
                """,
                use_aliases = True
            )
        )
        
        bot.register_next_step_handler(question, add_agent)
        
        
        
def add_agent(msg):
    """
    Create new agent
    """
    agent = AgentAction().create_agent(msg.text)
    
    if agent is not None:
        bot.send_message(
            msg.from_user.id,
            "<b>New Agent {agent.id} Created!</b>",
            parse_mode="HTML"
        )
    else:
        bot.send_message(
            msg.from_user.id,
            "Invalid Agent ID"
        )