# User Resource
from config import *
from .sources import users, trades, disputes


class TradeList(Resource):
    def get(self):
        count = len(trades)
        trade_list = [i.id for i in trades]

        result = {"Number Of Total Bot Trades": count}

        for i in trades:
            offset = trades.index(i) + 1

            result.update({offset: i.id})
        return result, 200

    def post(self):
        payload = request.get_json()
        return f"You are not allowed to create users through the API", 500


class Trade(Resource):
    def get(self, trade_id):
        for trade in trades:
            if trade.id == str(trade_id):
                result = {
                    "Id": trade.id,
                    "Seller": trade.seller,
                    "Buyer": trade.buyer,
                    "Price": f"{trade.price} {trade.currency}",
                    "Method of payment": trade.coin,
                    "Seller's wallet": trade.wallet,
                    "Payment status": trade.payment_status,
                    "Last updated on": trade.updated_at,
                    "Date created": trade.created_at,
                    "Dispute": str(trade.dispute),
                    "Agent": trade.agent_id,
                }

                if trade.is_open == False:
                    result.update({"Present state": "Closed"})
                else:
                    result.update({"Present state": "Open"})

                return result, 200

        return "Trade Not Found!", 404
