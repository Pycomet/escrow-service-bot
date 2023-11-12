from config import *
from database import User, Trade, Chat, session
from .utils import generate_id
from .user import get_user
from btcpay import BtcPayAPI

client = BtcPayAPI()

def open_new_trade(msg, currency: str = "USD", chat: Chat | None = None) -> Trade:
    """
    Returns a new trade without Agent
    """
    user: User = get_user(msg)

    #Create trade
    trade = Trade(
        id = generate_id(),
        seller = user,
        currency = currency,
        is_active = False,
        is_paid = False,
        invoice_id = "",
        chat = chat,
        created_at = str(datetime.now()),
        updated_at = str(datetime.now()),   
    )
    session.add(trade)
    session.commit()
    return trade


def get_most_recent_trade(user: User) -> Trade | None:
    "Get the most recent trade created by this user"
    # Get trades where the user is the seller
    
    seller_trades = session.query(Trade).filter(Trade.seller_id == str(user.id))

    # Get trades where the user is the buyer
    buyer_trades = session.query(Trade).filter(Trade.buyer_id == str(user.id))

    # Combine both sets of trades
    all_trades = seller_trades.union(buyer_trades)

    if all_trades.count() != 0:
        # Find the trade with the maximum created_at date
        most_recent_trade = all_trades.order_by(Trade.created_at.desc()).first()
        return most_recent_trade

    # If there are no trades, return None or handle as needed
    return None



def add_price(user: User, price: int) -> Trade | None:
    """
    Update trade instance with price of service
    """
    trade = get_most_recent_trade(user)
    if trade is not None:
        trade.price = int(price)
        session.add(trade)
        return trade
    
    # Else return None
    return None


def add_invoice_id(trade: Trade, invoice_id: str):
    """
    Update trade instance with price of service
    """
    trade.invoice_id = invoice_id
    session.add(trade)
    session.commit()


def get_invoice_url(trade: Trade) -> str:
    "Get Payment Url"
    url, invoice_id  = client.create_invoice(trade)
    if url is not None:
        add_invoice_id(trade, str(invoice_id))
        return url
    return None
    

