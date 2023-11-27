from config import *
from .sources import users, trades, disputes


class DisputeList(Resource):
    def get(self):
        count = len(disputes)
        dispute_list = [i.id for i in disputes]

        result = {"Number Of Disputes ": count}

        for i in disputes:
            offset = disputes.index(i) + 1

            result.update({offset: i.id})
        return result, 200

    def post(self):
        payload = request.get_json()
        return f"You are not allowed to create users through the API", 500


class Dispute(Resource):
    def get(self, dispute_id):
        for dispute in disputes:
            if dispute.id == str(dispute_id):
                result = {
                    "Id": dispute.id,
                    "Trade Id": str(dispute.trade_id),
                    "User": str(dispute.user),
                    "Complaint Message": dispute.complaint,
                    "Date created": dispute.created_on,
                }

                if dispute.is_seller() == True:
                    result.update({"Role": "Seller"})
                elif dispute.is_buyer() == True:
                    result.update({"Role": "Buyer"})
                else:
                    result.update({"Role": None})

                return result, 200

        return "Dispute Not Found!", 404
