from config import *
from database import *
from functions import *
from typing import Optional
from .utils import generate_id
from .user import UserClient
from payments import BtcPayAPI

client = BtcPayAPI()


class TradeClient:
    "House all transactions with database layer"

    @staticmethod
    def open_new_trade(
        msg, currency: str = "USD", chat: str | None = None, trade_type: str = "CryptoToCrypto"
    ) -> TradeType:
        """
        Returns a new trade without Agent
        """
        user: UserType = UserClient.get_user(msg)

        print(user.keys())

        trade: TradeType = {
            "_id": generate_id(),
            "seller_id": user["_id"],
            "buyer_id": "",
            "currency": currency,
            "is_active": False,
            "is_paid": False,
            "price": 0,
            "currency": "USD",
            "invoice_id": "",
            "is_completed": False,
            "chat": chat,
            "trade_type": trade_type,
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
    def get_active_trade_by_user_id(user_id: str) -> Optional[TradeType]:
        "Get the most recent active trade created by this user"
        active_trade_cursor = db.trades.find(
            {
                "$or": [
                    {"seller_id": user_id},
                    {"buyer_id": user_id},
                ],
                "is_active": True
            }
        ).sort([("created_at", -1)]).limit(1)
        
        active_trades = list(active_trade_cursor)
        logging.info(f"Active trades: {active_trades}")
        return active_trades[0] if active_trades else None


    @staticmethod
    def get_trade(id: str) -> TradeType or None: # type: ignore
        trade: TradeType = db.trades.find_one({"_id": id})
        return trade

    @staticmethod
    def get_trade_by_invoice_id(id: str) -> TradeType or None: # type: ignore
        trade: TradeType = db.trades.find_one({"invoice_id": id})
        return trade

    @staticmethod
    def add_price(*, price: float, user: Optional[UserType] = None, trade_id: Optional[str] = None) -> TradeType | None:
        if not trade_id and not user:
            raise ValueError("Either user or trade_id must be provided to add_price")
        
        trade: Optional[TradeType] = None
        if trade_id:
            trade = TradeClient.get_trade(trade_id)
        elif user: # user is not None
            trade = TradeClient.get_most_recent_trade(user)
        
        if trade is not None:
            db.trades.update_one({"_id": trade["_id"]}, {"$set": {"price": price, "updated_at": datetime.now()}})
            return TradeClient.get_trade(trade["_id"]) # Return fresh trade data
        return None

    @staticmethod
    def add_terms(*, terms: str, user: Optional[UserType] = None, trade_id: Optional[str] = None) -> TradeType | None:
        """
        Update terms of contract
        """
        if not trade_id and not user:
            raise ValueError("Either user or trade_id must be provided to add_terms")

        trade: Optional[TradeType] = None
        if trade_id:
            trade = TradeClient.get_trade(trade_id)
        elif user: # user is not None
            trade = TradeClient.get_most_recent_trade(user)

        if trade is not None:
            db.trades.update_one({"_id": trade["_id"]}, {"$set": {"terms": terms, "updated_at": datetime.now()}})
            return TradeClient.get_trade(trade["_id"]) # Return fresh trade data
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
    def get_invoice_status(trade: TradeType) -> Optional[str]: # type: ignore
        "Get Payment Url"
        status = client.get_invoice_status(trade["invoice_id"])
        if status is not None:
            return status
        return None

    @staticmethod
    def get_invoice_url(trade: TradeType) -> str:
        "Get Payment Url"
        active_trade: TradeType = db.trades.find_one({"_id": trade["_id"]})
        
        if active_trade['invoice_id'] == "":
            try:
                url, invoice_id = client.create_invoice(active_trade)
                if url is not None:
                    TradeClient.add_invoice_id(trade, str(invoice_id))
                    return url
            except Exception as e:
                app.logger.info(e)
                print(f"Error creating invoice: {e}")
        else:
            return f"{BTCPAY_URL}/i/{trade['invoice_id']}"
        return None

    @staticmethod
    def check_trade(user: UserType, trade_id: str) -> str | TradeType:
        "Return trade info"
        trade: TradeType = db.trades.find_one({"_id": trade_id})
        print(trade)

        if trade == None:
            return "Not Found"

        # elif trade['buyer_id'] != "":
        #     return "Both parties already exists"

        elif str(trade["seller_id"]) == str(user["_id"]):
            return "Not Permitted"

        else:
            TradeClient.add_buyer(trade=trade, buyer_id=user["_id"])
            return trade

    @staticmethod
    def get_trades(user_id: str):
        "Retrun list of trades the user is in"
        sells_cursor = db.trades.find({"seller_id": user_id})
        buys_cursor = db.trades.find({"buyer_id": user_id})

        sells = list(sells_cursor)
        buys = list(buys_cursor)

        logger.info(f"Sells: {sells}")
        logger.info(f"Buys: {buys}")

        return sells + buys

    @staticmethod
    def get_trades_report(sells: list, buys: list):
        "Return aggregated data of trades"
        purchases = len(buys)
        sales = len(sells)

        active_buys = [i for i in buys if i["is_active"] is True]
        active_sells = [i for i in sells if i["is_active"] is True]
        active = len(active_buys) + len(active_sells)

        trades = purchases + sales

        # r_buys = [i for i in buys if i["dispute"] != []]
        # r_sells = [i for i in sells if i["dispute"] != []]
        # reports = len(r_buys) + len(r_sells)
        reports = []
        for trade in buys + sells:
            trade_report = db.disputes.find({ "trade_id": trade["_id"] })
            [reports.append(i) for i in trade_report]

        return purchases, sales, trades, active, len(reports)

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

    @staticmethod
    def reset_all_active_trades() -> int:
        """Reset all active trades to inactive state
        
        Returns the number of trades that were reset
        """
        result = db.trades.update_many(
            {"is_active": True},
            {"$set": {"is_active": False, "updated_at": datetime.now()}}
        )
        return result.modified_count
        
    @staticmethod
    def get_all_active_trades():
        """Get all active trades in the database
        
        Returns a list of all active trades
        """
        active_trades_cursor = db.trades.find({"is_active": True})
        return list(active_trades_cursor)

    @staticmethod
    def get_active_market_shops():
        """Get all active market shops"""
        shops = db.trades.find({
            "trade_type": "MarketShop",
            "is_active": True,
            "buyer_id": ""  # No buyer yet
        }).sort([("created_at", -1)])
        return list(shops)

    @staticmethod
    def get_trade_by_invoice_id(invoice_id: str) -> TradeType | None:
        """Get trade by invoice ID"""
        trade = db.trades.find_one({"invoice_id": invoice_id})
        return trade

    @staticmethod
    def update_trade_status(trade_id: str, status: str) -> bool:
        """Update trade status"""
        try:
            db.trades.update_one(
                {"_id": trade_id},
                {
                    "$set": {
                        "status": status,
                        "updated_at": datetime.now()
                    }
                }
            )
            return True
        except Exception as e:
            logger.error(f"Error updating trade status: {e}")
            return False

    @staticmethod
    def confirm_crypto_deposit(trade_id: str) -> bool:
        """Confirm crypto deposit for a trade"""
        try:
            db.trades.update_one(
                {"_id": trade_id},
                {
                    "$set": {
                        "is_crypto_deposited": True,
                        "crypto_deposit_time": datetime.now(),
                        "updated_at": datetime.now()
                    }
                }
            )
            return True
        except Exception as e:
            logger.error(f"Error confirming crypto deposit: {e}")
            return False

    @staticmethod
    def confirm_fiat_payment(trade_id: str) -> bool:
        """Confirm fiat payment for a trade"""
        try:
            db.trades.update_one(
                {"_id": trade_id},
                {
                    "$set": {
                        "is_fiat_paid": True,
                        "fiat_payment_time": datetime.now(),
                        "updated_at": datetime.now()
                    }
                }
            )
            return True
        except Exception as e:
            logger.error(f"Error confirming fiat payment: {e}")
            return False
