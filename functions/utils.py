from config import *


def get_received_msg(msg):
    "Delete This Message"
    message_id = msg.message_id
    chat = msg.chat
    return chat, message_id


def generate_id():
    "Return unique id"
    u_id = ""

    lower_case = string.ascii_lowercase
    upper_case = string.ascii_uppercase
    digits = string.digits

    option = lower_case + upper_case + digits

    for i in range(10):
        u_id += str(random.choice(option))

    return u_id
