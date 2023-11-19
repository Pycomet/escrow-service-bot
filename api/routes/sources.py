from database import session, User, Trade, Dispute, Chat

users = session.query(User).all()

trades = session.query(Trade).all()

disputes = session.query(Dispute).all()

chats = session.query(Chat).all()