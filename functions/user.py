from config import *
from database import User
from .utils import *
from prisma.models import User


async def get_user(msg) -> User:
    "Returns or creates a new user"
    await prisma.connect()
    id = str(msg.from_user.id)

    try:
        chat = msg.chat
    except:
        chat = msg.message.chat


    # Query for the user
    user = await prisma.user.find_first(where={"id": str(id)})

    if user:
        await prisma.disconnect()
        return user

    # If user not found, create a new user
    new_user = await prisma.user.create(
            {
                "id": str(id),
                "name": msg.from_user.first_name,
                "wallet": "",
                "chats": {"connect": {"id": str(chat.id), "name": chat.title or chat.first_name, "admin_id": str(id)}},
                "verified": True,
                "created_at": datetime.now()
            }
        )
    print(new_user)

    bot.send_message(
        ADMIN_ID,
        f"New user registered to escrow bot - @{new_user.name}",
    )
    await prisma.disconnect()
    return new_user




def get_msg_id(msg) -> int:
    "Returns the message id"
    try:
        return msg.message_id
    except:
        return msg.id


async def get_user_by_id(id: str) -> User:
    "Returns or creates a new user"
    # Query for the user
    user = await prisma.user.find_first(where={"id": str(id)})

    if user:
        return user
    else:
        return None
