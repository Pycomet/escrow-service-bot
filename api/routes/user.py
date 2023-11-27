# User Resource
from config import *
from .sources import users, trades, disputes


class UserList(Resource):
    def get(self):
        count = len(users)
        user_list = [i.id for i in users]

        result = {"Total Count": count}

        for i in users:
            offset = users.index(i) + 1

            result.update({offset: i.id})
        return result, 200

    def post(self):
        payload = request.get_json()
        return f"You are not allowed to create users through the API", 500


class User(Resource):
    def get(self, user_id):
        for user in users:
            if user["_id"] == int(user_id):
                result = {"Chat Id": str(user["chat"])}

                # update result with user info
                data = get_user_info(user_id)
                result.update(data)

                return result, 200

        return "User Not Found!", 404

    def post(self):
        payload = request.get_json()
        return f"You are not allowed to create users through the API", 500


def get_user_info(id):
    "Returns The Accumulated User Information"
    info = {}

    selling = 0
    buying = 0
    disputes_count = 0

    # import pdb; pdb.set_trace()

    # Get number of trades (buy & sell)
    for i in trades:
        if str(id) == i.seller_id:
            selling += 1
        elif str(id) == i.buyer_id:
            buying += 1
        else:
            pass

    # Get the total number of disputes
    for j in disputes:
        if int(id) == j.user_id:
            disputes_count += 1
        else:
            pass

    trades_count = selling + buying

    # Update dictionary
    info.update(
        {"Total Trades": trades_count, "Total Open Dispute Trades": disputes_count}
    )
    return info
