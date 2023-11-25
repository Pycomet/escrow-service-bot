from config import *

class User(Base):
    """
    SqlAlchemy ORM for Users
    """
    __tablename__ = "users"

    id = Column(String(20), primary_key=True)
    name = Column(String(20))
    wallet = Column(String(50))
    chat = Column(String(20))
    verified = Column(Boolean())
    created_at = Column(DateTime())

    def __repr__(self):
        return f"{self.name}(id={self.id})"



class Chat(Base):
    """
    SqlAlchemy ORM for Chats
    """
    __tablename__ = "chats"

    id = Column(String(20), primary_key=True)
    name = Column(String(20))
    admin_id = Column(String(20), ForeignKey("users.id"))
    admin = relationship("User", uselist=False, primaryjoin="Chat.admin_id == User.id")
    created_at = Column(DateTime())

    def __repr__(self):
        return f"{self.name} Chat(id={self.id})"
    

class Trade(Base):
    """
    SqlAlchemy ORM For Trades
    """
    __tablename__ = "trades"

    id = Column(String(20), primary_key=True)
    seller_id = Column(String(20), ForeignKey("users.id"))
    seller = relationship("User", uselist=False, primaryjoin="Trade.seller_id == User.id")

    buyer_id = Column(String(20), ForeignKey("users.id"))
    buyer = relationship("User", uselist=False, primaryjoin="Trade.buyer_id == User.id")
    terms = Column(String(300))

    price = Column(Integer())
    currency = Column(String(20))
    invoice_id = Column(String(50))
    is_active = Column(Boolean()) #If the trade is deactivated by dispute or admin
    is_paid = Column(Boolean())

    chat_id = Column(String(20), ForeignKey("chats.id"))
    chat = relationship("Chat", uselist=False, primaryjoin="Chat.id == Trade.chat_id")
    dispute = relationship("Dispute", cascade="all, delete-orphan")

    created_at = Column(DateTime())
    updated_at = Column(DateTime())


    def __repr__(self):
        return "<Trade created by %s>" % (self.seller.name)

    def is_dispute(self):
        "Dispute Status"
        if self.dispute == []:
            return "No Dispute"
        else:
            return "%s Last Dispute Created %s " % (self.dispute[-1].id, self.dispute[-1].created_at)


class Dispute(Base):
    """
    SqlAlchemy ORM For Disputes
    """
    __tablename__ = "disputes"

    id = Column(String(20), primary_key=True)
    user_id = Column(String(20), ForeignKey("users.id"))
    user  = relationship("User", uselist=False, primaryjoin="Dispute.user_id == User.id")

    trade_id = Column(String(20), ForeignKey("trades.id"))
    trade = relationship("Trade", uselist=False, primaryjoin="Dispute.trade_id == Trade.id")
    complaint = Column(String(50))
    is_resolved = Column(Boolean())
    created_at = Column(DateTime())

    def __repr__(self):
        return "<Dispute created by %s>" % (self.user.name)

    def is_seller(self):
        return self.user is self.trade.seller

    def is_buyer(self):
        return self.user is self.trade.buyer


Session = sessionmaker(bind=engine, autoflush=False)
# session = Session()
# session.close()

try:
    with Session() as session:
        # Your database operations
        session.close()
except PendingRollbackError:
    session.rollback()
    print("Rolling back due to PendingRollbackError.")
except Exception as e:
    session.rollback()
    print(f"Error: {e}")
    # Handle the error or re-raise if needed
    raise e