from config import *
from database import User, session
from .utils import *

def get_user(msg) -> User:
    "Returns or creates a new user"
    chat = msg.message.chat.id
    id = str(msg.from_user.id)
    
    user: User = session.query(User).filter(cast(User.id, String) == str(id)).first()
    if user:
        return user
    else:
        user = User(id=id, name=msg.from_user.first_name, wallet="", chat=chat, verified=True, created_at=datetime.now())
        session.add(user)
        session.commit()
        return user



def get_user_by_id(id: str) -> User:
    "Returns or creates a new user"
    user: User = session.query(User).filter(cast(User.id, String) == str(id)).first()
    if user:
        return user
    else:
        return None
