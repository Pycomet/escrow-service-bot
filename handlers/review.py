from config import *
from utils import *
from functions import *


@bot.message_handler(commands=["review"])
def review(msg):
    """
    Write review
    """

    question = bot.send_message(
        msg.from_user.id,
        """
<b>Could you please share your thoughts on my bot's performance and usability? </b>
            
Any feedback or suggestions for improvement would be greatly appreciated!
        """,
        parse_mode="html",
    )

    bot.register_next_step_handler(question, get_review)


def get_review(msg):
    """
    Get review
    """

    bot.send_message(
        "@trusted_escrow_bot_reviews",
        f"""
<b>New review from {msg.from_user.first_name}:</b>

{msg.text}
        """,
        parse_mode="html",
    )

    bot.send_message(
        msg.from_user.id,
        "Thank you for your review! Your review would be made visible to the entire community on our review channel.",
        parse_mode="html",
    )
