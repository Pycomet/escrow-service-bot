from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref

Base = declarative_base()
engine = create_engine(
    "postgresql://escrow_bot_database_user:XN0jOaJ0q64gE4mvixEOeFLmzHqmi1C4@dpg-cl113ais1bgc73dj3m30-a.oregon-postgres.render.com/escrow_bot_database",
    echo=False)
#connect_args={'check_same_thread': False},


class User(Base):
    """
    SqlAlchemy ORM for Users
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    chat = Column(String(20))
    verified = Column(Boolean())

    def __repr__(self):
        return "<User(id='%s')>" % (self.id)



class Trade(Base):
    """
    SqlAlchemy ORM Trade Model
    """
    __tablename__ = 'trades'
    id = Column(String(16), primary_key=True)
    seller = Column(String(20))
    buyer = Column(Integer)
    price = Column(Integer)

    address =  Column(String(50))
    invoice = Column(String(50))

    currency = Column(String(32))
    coin = Column(String(32))
    wallet = Column(String(50))

    payment_status = Column(Boolean)
    created_at = Column(String(32))
    updated_at = Column(String(32))
    is_open = Column(Boolean)
    agent_id = Column(String(50))

    # receive_address_id = Column(String(50))

    dispute = relationship("Dispute", cascade="all, delete-orphan")

    def __repr__(self):
        return "<Trade(id='%s')>" % (self.id)

    def is_dispute(self):
        "Dispute Status"
        if self.dispute == []:
            return "No Dispute"
        else:
            return "%s Created on %s " % (self.dispute[-1].id, self.dispute[-1].created_on)


class Dispute(Base):
    """
    SQLAlchemy ORM Dispute Model
    """
    __tablename__ = "disputes"

    id = Column(String, unique=True, primary_key=True)
    user = Column(Integer)
    complaint = Column(String(162))
    created_on = Column(String(32))
    trade_id = Column(ForeignKey("trades.id", ondelete="CASCADE"))

    trade = relationship("Trade", uselist=False)

    
    def __repr__(self):
        return "<Dispute(id='%s')>" % (self.id)

    def is_seller(self):
        if self.user == self.trade[0].seller:
            return True
        else:
            return False

    def is_buyer(self):
        if self.user == self.trade[0].buyer:
            return True
        else:
            return False


class Agent(Base):
    """
    House User Accounts With Wallets
    """
    __tablename__ = "agent"

    id = Column(Integer, primary_key=True)
    mnemonic = Column(String(200))
    xpub = Column(String(200))
    btc_address =  Column(String(50))
    eth_address =  Column(String(50))
    trade = Column(String(50))
    token = Column(String(100))
    store = Column(String(50))
    affiliate = relationship("Affiliate", back_populates="agent")

    def __repr__(self):
        return f"<Agent(id='{self.id}')"


class Affiliate(Base):
    """
    SQLAlchemy ORM Affiliate Records Table
    """
    __tablename__ = "affiliates"

    id = Column(String, primary_key=True)
    agent_id = Column(Integer, ForeignKey('agent.id'))
    agent = relationship("Agent", back_populates="affiliate")

    def __repr__(self):
        return "<Group (id='%s')>" % (self.id)

    @classmethod
    def check_affiliate(cls, id):
        info = session.query(Affiliate).filter_by(id=id).first()
        if not info:
            return None
        else:
            return info




# Base.metadata.drop_all(bind=engine)
# Base.metadata.create_all(bind=engine)

# Base.metadata.create_all(bind=engine)

Session = sessionmaker(bind=engine, autoflush=False)

session = Session()

# import pdb; pdb.set_trace()

session.close()

