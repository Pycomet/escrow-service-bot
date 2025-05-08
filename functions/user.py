from config import *
from database import *
from .utils import *


def get_msg_id(msg) -> int:
    "Returns the message id"
    try:
        return msg.message_id
    except:
        return msg.id


class UserClient:
    "Class To Hold All User Related Functions/Transaction With Database"

    @staticmethod
    def get_user(msg) -> UserType:
        "Returns or creates a new user"
        id = str(msg.from_user.id)

        try:
            chat = msg.chat
        except:
            chat = msg.message.chat

        # Query for the user
        user: UserType = db.users.find_one({"_id": str(id)})

        if user:
            return user

        # If user not found, create a new user
        new_user: UserType = {
            "_id": id,
            "name": msg.from_user.first_name,
            "wallet": "",
            "chat": str(chat.id),
            "verified": False,
            "disabled": False,
            "created_at": datetime.now(),
        }
        print(new_user)

        db.users.insert_one(new_user)
        return new_user

    @staticmethod
    def get_user_by_id(id: str) -> UserType | None:
        "Returns or creates a new user"
        # Query for the user
        user: UserType = db.users.find_one({"_id": str(id)})

        if user:
            return user
        else:
            return None

    @staticmethod
    def set_wallet(user_id: str, address: str):
        # import pdb; pdb.set_trace()
        user = UserClient.get_user_by_id(user_id)
        if user is not None:
            db.users.update_one({"_id": user_id}, {"$set": {"wallet": address}})
            return user
        return None
