from config import *
from utils import *
from functions import *


def start_affiliate(msg):
    """
    This is the handler to start affiliate options
    """
    user = get_user(msg=msg)

    #  WRTIE A PROCESS TO CHECK ADMIN AND SEND REQUEST TO PROCESS WITH USER
    username = msg.from_user.username
    if user.id != ADMIN_ID or user.verified == False:
        bot.send_message(
            user.id,
            emoji.emojize(
                """
    :robot: Awaiting authorization from support. Contact @Telescrowbotsupport to pass screening process
                """,
            ),
        )

        bot.send_message(
            ADMIN_ID,
            f"""
    User ID - {user.id} just attempted adding this bot to a group
            """,
            parse_mode="HTML",
        )

    else:

        question = bot.send_message(
            user.id,
            emoji.emojize(
                """
    :robot: To use escrow service on your group, I would need the following information.
                
    Please reply with the your Group Username :grey_question: (example -> @GetGroupIDRobot)
                """,
            ),
        )

        bot.register_next_step_handler(question, add_addresses)


def add_addresses(msg):

    group_id = msg.text
    chat = bot.get_chat(group_id)
    chat = chat.wait()

    if not chat.id:
        return bot.send_message(msg.from_user.id, "Invalid Group ID")

    agent = AgentAction().create_agent(msg.from_user.id)
    # import pdb; pdb.set_t     race()
    affiliate = create_affiliate(agent, str(chat.id))
    print(affiliate)
    if affiliate != "Already Exists":
        bot.send_message(
            msg.from_user.id,
            emoji.emojize(
                ":+1: Congrats!! You can now add TeleEscrow Service(@tele_escrowbot) to your public group and receive your affiliate charge for trade performed by your members, selecting their roles on the group. Good Luck!!",
            ),
        )

    else:

        bot.send_message(
            msg.from_user.id,
            emoji.emojize(
                ":construction: This Group Is Already Registered",
            ),
        )
