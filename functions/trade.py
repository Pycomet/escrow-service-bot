from config import *
from database import *
from functions import *
from .utils import generate_id
from .user import UserClient
from payments import BtcPayAPI

client = BtcPayAPI()


class TradeClient:
    "House all transactions with database layer"

    @staticmethod
    def open_new_trade(
        msg, currency: str = "USD", chat: str | None = None
    ) -> TradeType:
        """
        Returns a new trade without Agent
        """
        user: UserType = UserClient.get_user(msg)

        trade: TradeType = {
            "_id": generate_id(),
            "seller_id": user["_id"],
            "currency": currency,
            "is_active": False,
            "is_paid": False,
            "price": 0,
            "currency": "USD",
            "invoice_id": "",
            "is_completed": False,
            "invoice_id": "",
            "chat": chat,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        db.trades.insert_one(trade)
        return trade

    @staticmethod
    def get_most_recent_trade(user: UserType) -> TradeType | None:
        "Get the most recent trade created by this user"
        most_recent_trade = (
            db.trades.find(
                {
                    "$or": [
                        {"seller_id": str(user["_id"])},
                        {"buyer_id": str(user["_id"])},
                    ]
                }
            )
            .sort([("created_at", -1)])
            .limit(1)
        )

        # If there are no trades, return None or handle as needed
        return most_recent_trade[0] if most_recent_trade else None

    @staticmethod
    def get_trade(id: str) -> TradeType or None:
        trade: TradeType = db.trades.find_one({"_id": id})
        return trade

    @staticmethod
    def get_trade_by_invoice_id(id: str) -> TradeType or None:
        trade: TradeType = db.trades.find_one({"invoice_id": id})
        return trade

    @staticmethod
    def add_price(user: UserType, price: float) -> TradeType | None:
        trade = TradeClient.get_most_recent_trade(user)
        if trade is not None:
            db.trades.update_one({"_id": trade["_id"]}, {"$set": {"price": price}})
            return trade
        return None

    @staticmethod
    def add_terms(user: UserType, terms: str) -> TradeType | None:
        """
        Update terms of contract
        """
        trade = TradeClient.get_most_recent_trade(user)
        if trade is not None:
            db.trades.update_one({"_id": trade["_id"]}, {"$set": {"terms": terms}})
            return trade
        return None

    @staticmethod
    def add_invoice_id(trade: TradeType, invoice_id: str):
        """
        Update trade instance with price of service
        """
        db.trades.update_one(
            {"_id": trade["_id"]}, {"$set": {"invoice_id": invoice_id}}
        )
        return trade

    @staticmethod
    def add_buyer(trade: TradeType, buyer_id: str):
        "Add Buyer To Trade"
        db.trades.update_one(
            {"_id": trade["_id"]},
            {"$set": {"buyer_id": buyer_id, "updated_at": datetime.now()}},
        )
        return trade

    @staticmethod
    def get_invoice_status(trade: TradeType) -> str or None:
        "Get Payment Url"
        status = client.get_invoice_status(trade["invoice_id"])
        if status is not None:
            return status
        return None

    @staticmethod
    def get_invoice_url(trade: TradeType) -> str:
        "Get Payment Url"
        active_trade: TradeType = db.trades.find_one({"_id": trade["_id"]})
        url, invoice_id = client.create_invoice(active_trade)
        if url is not None:
            TradeClient.add_invoice_id(trade, str(invoice_id))
            return url
        return None

    @staticmethod
    def check_trade(user: UserType, trade_id: str) -> str | TradeType:
        "Return trade info"
        trade: TradeType = db.trades.find_one({"_id": trade_id})

        if trade == None:
            return "Not Found"

        elif trade.buyer_id != None:
            return "Both parties already exists"

        elif str(trade["seller_id"]) == str(user["_id"]):
            return "Not Permitted"

        else:
            TradeClient.add_buyer(trade=trade, buyer_id=user["_id"])
            return trade

    @staticmethod
    def get_trades(user_id: str):
        "Retrun list of trades the user is in"
        sells = db.trades.find({"seller_id": user_id})
        buys = db.trades.find({"buyer_id": user_id})

        return list(sells), list(buys)

    @staticmethod
    def get_trades_report(sells: list, buys: list):
        "Return aggregated data of trades"
        purchases = len(buys)
        sales = len(sells)

        active_buys = [i for i in buys if i["is_active"] is True]
        active_sells = [i for i in sells if i["is_active"] is True]
        active = len(active_buys) + len(active_sells)

        trades = purchases + sales

        r_buys = [i for i in buys if i["dispute"] != []]
        r_sells = [i for i in sells if i["dispute"] != []]
        reports = len(r_buys) + len(r_sells)

        return purchases, sales, trades, active, reports

    @staticmethod
    def delete_trade(trade_id: str):
        "Delete Trade"
        trade = db.trades.find_one({"_id": trade_id})

        if trade is None:
            return "Not Found!"
        else:
            db.trades.delete_one({"_id": trade_id})
            return "Complete!"

    @staticmethod
    def seller_delete_trade(user_id, trade_id):
        "Delete Trade"
        trade = db.trades.find_one({"_id": trade_id})

        if trade is None:
            return "Trade Not Found"

        elif trade["is_active"] is True:
            return (
                "You are not authorized to close an active trade, close the deal first."
            )

        elif trade["seller_id"] == user_id and trade["is_active"] is False:
            TradeClient.delete_trade(trade_id)
            return "Trade Deleted Successfully"

        else:
            return "You are not authorized to take this action. Please contact support!"

    # WEBHOOK FUNCTIONS TO HANDLE TRANSACTION RESPONSE FROM BTCPAY SERVER #
    @staticmethod
    def handle_invoice_paid(invoice_id: str) -> bool:
        trade = TradeClient.get_trade_by_invoice_id(invoice_id)
        if trade is not None:
            trade_id = trade["_id"]
            db.trades.update_one({"_id": trade_id}, {"$set": {"is_paid": True}})
            return True
        return False

    @staticmethod
    def handle_invoice_expired(invoice_id: str) -> bool:
        trade = TradeClient.get_trade_by_invoice_id(invoice_id)
        if trade is not None:
            trade_id = trade["_id"]
            db.trades.update_one(
                {"_id": trade_id}, {"$set": {"is_paid": False, "is_active": False}}
            )
            return True
        return False
