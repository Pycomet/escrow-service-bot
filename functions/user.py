from config import *
from database import User, session
from .utils import *

def get_user(msg) -> User:
    "Returns or creates a new user"
    id = str(msg.from_user.id)

    try:
        chat = msg.chat
    except:
        chat = msg.message.chat

    user: User = session.query(User).filter(cast(User.id, String) == str(id)).first()
    if user:
        return user
    else:
        try:
            user = User(id=id, name=msg.from_user.first_name, wallet="", chat=chat.id, verified=True, created_at=datetime.now())

            bot.send_message(str(ADMIN_ID), f"New user registered to escrow bot - @{msg.from_user.username}")
            session.add(user)
            session.commit()
            session.close()
            return user

        except Exception as e:
            session.rollback()
            print(f"Error in get_user: {e}")
            # Handle the error or re-raise if needed
            raise e
        finally:
            session.close()


def get_msg_id(msg) -> int:
    "Returns the message id"
    try:
        return msg.message_id
    except:
        return msg.id


def get_user_by_id(id: str) -> User:
    "Returns or creates a new user"
    user: User = session.query(User).filter(cast(User.id, String) == str(id)).first()
    if user:
        return user
    else:
        return None
