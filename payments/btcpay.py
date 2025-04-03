from config import *
import requests
from database import TradeType


class BtcPayAPI(object):
    def __init__(self):
        self.url = BTCPAY_URL
        self.api_key = BTCPAY_API_KEY
        self.store_id = BTCPAY_STORE_ID
        self.header = {
            "Content-Type": "application/json",
            "Authorization": f"token {self.api_key}",
        }

    def get_invoice_status(self, invoice_id: str):
        "Get a single invoice"
        try:
            result = requests.get(
                f"{self.url}/api/v1/stores/{self.store_id}/invoices/{invoice_id}",
                headers=self.header,
            ).json()
            return result["status"]

        except Exception as e:
            print(e, "Error")
            return None

    def create_invoice(self, trade: TradeType):
        "Create A New Checkout"

        try:
            app.logger.info(f"Trade - {trade}")
            app.logger.info(f"Webhook - {WEBHOOK_URL} ---- {self.url}")
            # create checkout with trade info
            checkout_payload = {
                "metadata": {"creator": trade["seller_id"]},
                "checkout": {
                    "speedPolicy": "HighSpeed",
                    "paymentMethods": ["BTC"],
                    "defaultPaymentMethod": "BTC",
                    "expirationMinutes": 60,
                    "monitoringMinutes": 90,
                    "paymentTolerance": 0,
                    "redirectURL": f"{WEBHOOK_URL}/paid",
                    "redirectAutomatically": True,
                    "requiresRefundEmail": True,
                    "checkoutType": None,
                    "defaultLanguage": "en",
                },
                "receipt": {
                    "enabled": True,
                    "showQR": None,
                    "showPayments": None,
                },
                "amount": trade["price"],
                "currency": "USD",
            }

            result = requests.post(
                f"{self.url}/api/v1/stores/{self.store_id}/invoices",
                headers=self.header,
                json=checkout_payload,
            ).json()
            self.status = result["status"]
            self.invoice_id = result["id"]
            self.checkout_url = result["checkoutLink"]
            print("Invoice ", result)

            return self.checkout_url, self.invoice_id

        except Exception as e:
            app.logger.info(e)
            print(e, "Error")
            return None, None


# api = BtcPayAPI()
# # print(api.create_invoice(trade={
# #     'price': 500,
# #     'buyer': "User D",
# #     'seller': "User J"
# # }))

# print(api.get_invoice("VDPjEBbfoPpsPMhKme1pD3"))
