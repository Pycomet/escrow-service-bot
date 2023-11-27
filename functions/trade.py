from config import *
from database import User, Trade, Chat
from .utils import generate_id
from .user import get_user
from payments import BtcPayAPI

client = BtcPayAPI()


async def open_new_trade(msg, currency: str = "USD", chat: Chat | None = None) -> Trade:
    """
    Returns a new trade without Agent
    """
    user: User = await get_user(msg)

    with app.app_context():
        # Create trade
        trade = Trade(
            id=generate_id(),
            seller=user,
            currency=currency,
            is_active=False,
            is_paid=False,
            invoice_id="",
            chat=chat,
            created_at=str(datetime.now()),
            updated_at=str(datetime.now()),
        )

        db.session.add(trade)
        db.session.commit()
    return trade


def get_most_recent_trade(user: User) -> Trade | None:
    "Get the most recent trade created by this user"
    # Get trades where the user is the seller
    with app.app_context():
        most_recent_trade = (
            db.session.query(Trade)
            .filter(
                (cast(Trade.seller_id, String) == str(user.id))
                | (cast(Trade.buyer_id, String) == str(user.id))
            )
            .order_by(Trade.created_at.desc())
            .options(joinedload(Trade.dispute))
            .one_or_none()
        )

        # If there are no trades, return None or handle as needed
        return most_recent_trade


def get_trade(id: str) -> Trade or None:
    with app.app_context():
        trade: Trade = Trade.query.filter(cast(Trade.id, String) == id).one_or_none()
        if trade is not None:
            return trade
        return None


def get_trade_by_invoice_id(id: str) -> Trade or None:
    with app.app_context():
        trade: Trade = Trade.query.filter(
            cast(Trade.invoice_id, String) == id
        ).one_or_none()
        if trade is not None:
            return trade
        return None


def add_price(user: User, price: int) -> Trade | None:
    """
    Update trade instance with price of service
    """
    trade = get_most_recent_trade(user)
    if trade is not None:
        trade.price = int(price)
        db.session.commit()
        return trade

    # Else return None
    return None


def add_terms(user: User, terms: str) -> Trade | None:
    """
    Update terms of contract
    """
    trade = get_most_recent_trade(user)
    if trade is not None:
        trade.terms = str(terms)
        db.session.commit()
        return trade

    # Else return None
    return None


def add_invoice_id(trade: Trade, invoice_id: str):
    """
    Update trade instance with price of service
    """
    trade.invoice_id = invoice_id
    trade.updated_at = str(datetime.now())
    db.session.commit()


def add_buyer(trade, buyer_id: str):
    "Add Buyer To Trade"
    trade.buyer_id = buyer_id
    trade.updated_at = str(datetime.now())
    trade.is_active = True
    db.session.commit()


def get_invoice_status(trade: Trade) -> str or None:
    "Get Payment Url"
    status = client.get_invoice_status(trade.invoice_id)
    if status is not None:
        return status
    return None


def get_invoice_url(trade: Trade) -> str:
    "Get Payment Url"
    url, invoice_id = client.create_invoice(trade)
    if url is not None:
        add_invoice_id(trade, str(invoice_id))
        return url
    return None


def check_trade(user: User, trade_id: str):
    "Return trade info"
    with app.app_context():
        trade = Trade.query.filter(cast(Trade.id, String) == trade_id).one_or_none()

        if trade == None:
            return "Not Found"

        elif trade.buyer_id != None:
            return "Both parties already exists"

        elif str(trade.seller.id) == str(user.id):
            return "Not Permitted"

        else:
            add_buyer(trade=trade, buyer_id=user.id)
            return trade


def get_trades(user_id: str):
    "Retrun list of trades the user is in"
    with app.app_context():

        user_trades = (
            db.session.query(Trade)
            .filter(
                or_(
                    cast(Trade.seller_id, String) == str(user_id),
                    cast(Trade.buyer_id, String) == str(user_id),
                )
            )
            .all()
        )

        sells = [trade for trade in user_trades if str(trade.seller_id) == str(user_id)]
        buys = [trade for trade in user_trades if str(trade.buyer_id) == str(user_id)]

        return sells, buys


def get_trades_report(sells: list, buys: list):
    "Return aggregated data of trades"
    purchases = len(buys)
    sales = len(sells)

    active_buys = [i for i in buys if i.is_active == True]
    active_sells = [i for i in sells if i.is_active == True]
    active = len(active_buys) + len(active_sells)

    trades = purchases + sales

    r_buys = [i for i in buys if i.dispute is not []]
    r_sells = [i for i in sells if i.dispute is not []]
    reports = len(r_buys) + len(r_sells)

    return purchases, sales, trades, active, reports


def delete_trade(trade_id: str):
    "Delete Trade"
    with app.app_context():
        trade = Trade.query.filter(cast(Trade.id, String) == trade_id).delete()

        if trade == None:
            return "Not Found!"
        else:
            db.session.commit()
            return "Complete!"


def seller_delete_trade(user_id, trade_id):
    "Delete Trade"
    with app.app_context():
        trade = Trade.query.filter_by(cast(id, String) == trade_id).one_or_none()

        if trade is None:
            return "Trade Not Found"

        elif trade.is_active == True:
            return "You are not authorized to close an active trade, the close the deal first."

        elif trade.seller_id == str(user_id) and trade.is_active == False:
            delete_trade(trade.id)
            return "Trade Deleted Successfully"

        else:
            return "You are not authorized to take this action. Please contact support!"


# WEBHOOK FUNCTIONS TO HANDLE TRANSACTION RESPONSE FROM BTCPAY SERVER #
def handle_invoice_paid(invoice_id: str) -> bool:
    "Handle Invoice Paid/ Settled"
    trade = get_trade_by_invoice_id(invoice_id)
    if trade is not None:
        trade.is_paid = True
        db.session.commit()
        return True
    return False


def handle_invoice_expired(invoice_id: str) -> bool:
    "Handles Invoice Payment Url Being Expired"
    trade = get_trade_by_invoice_id(invoice_id)
    if trade is not None:
        trade.is_paid = False
        trade.is_active = False
        db.session.commit()
        return True
    return False
