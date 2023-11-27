from config import *
import requests


class BitcoinApi(object):
    def __init__(self):
        self.email = ""
        self.password = ""
        self.token = ""
        self.xpub = ""
        self.mnemonic = ""

    def create_wallet(self):
        # import pdb; pdb.set_trace()
        try:
            res1 = requests.post(
                "https://wallet-api.forgingblock.io/v1/create-btc-mnemonic"
            ).json()
            self.mnemonic = res1["mnemonic"]
            print(self.mnemonic)

            payload = {"mnemonic": self.mnemonic, "number": 0}
            res2 = requests.post(
                "https://wallet-api.forgingblock.io/v1/retrieve-btc-wallet-address",
                data=payload,
            ).json()
            self.address = res2["address"]
            return self.mnemonic, self.address

        ### FETCH ETH ADDRESS

        except Exception as e:
            return None

    def get_xpub(self):
        payload = {
            "mnemonic": self.mnemonic,
        }
        res = requests.post(
            "https://wallet-api.forgingblock.io/v1/generate-btc-xpub", data=payload
        ).json()
        self.xpub = res["xpub"]

        return self.xpub

    def get_wif(self, mnemonic):
        payload = {"mnemonic": mnemonic, "number": 0}
        res = requests.post(
            "https://wallet-api.forgingblock.io/v1/generate-btc-wif", data=payload
        ).json()
        self.wif = res["wif"]

        return self.wif

    def get_btc_fee(self):
        res = requests.post("https://wallet-api.forgingblock.io/v1/find-btc-fee").json()
        return res["fastestFee"], res["halfHourFee"], res["hourFee"]

    def get_eth_fee(self):
        res = requests.post("https://wallet-api.forgingblock.io/v1/find-eth-gas").json()
        return res["FastGasPrice"], res["SafeGasPrice"], res["suggestBaseFee"]

    def create_store(self, name):
        payload = {
            "email": self.email,
            "password": self.password,
            "xpub": self.xpub,
            "name": name,
        }
        result = requests.post(
            "https://api.forgingblock.io/create-store", data=payload
        ).json()

        self.trade = result["trade"]
        self.token = result["token"]
        self.store = result["store"]
        return self.trade, self.token, self.store

    def connect_store(self):
        try:
            payload = {
                "email": self.email,
                "password": self.password,
                "address": self.address,
                "store": self.store,
            }
            result = requests.post(
                "https://api.forgingblock.io/connect-wallet-btc-single", data=payload
            ).json()
            return result["success"]

        except Exception as e:
            return "Failed"

    def create_invoice(self, trade, agent: None):

        # 5% Added to Invoice Payment
        extra = 0.05 * float(trade.price)

        if trade.agent_id != None:
            extra = 0.08 * float(trade.price)

        price = trade.price + extra

        try:
            if agent is None:
                payload = {
                    "trade": "",
                    "token": "",
                    "amount": int(price),
                    "currency": trade.currency.lower(),
                }
            else:
                payload = {
                    "trade": agent.trade,
                    "token": agent.token,
                    "amount": int(price),
                    "currency": trade.currency.lower(),
                }
            print(payload)
            result = requests.post(
                "https://api.forgingblock.io/create-invoice", data=payload
            ).json()

            self.invoice = result["id"]
            print(result)
            return self.invoice

        except Exception as e:

            return "Temporary Delay..."

    def get_payment_url(self, trade, agent: None):

        try:
            if agent is None:
                payload = {"trade": "", "token": "", "invoice": trade.invoice}
            else:
                payload = {
                    "trade": agent.trade,
                    "token": agent.token,
                    "invoice": trade.invoice,
                }
            result = requests.post(
                "https://api.forgingblock.io/check-invoice", data=payload
            ).json()
            return result["url"]

        except Exception as e:
            # import pdb; pdb.set_trace()
            return "Failed"

    def check_status(self, trade, agent: None):
        try:
            if agent is None:
                payload = {"trade": "", "token": "", "invoice": trade.invoice}
            else:
                payload = {
                    "trade": agent.trade,
                    "token": agent.token,
                    "invoice": trade.invoice,
                }
            result = requests.post(
                "https://api.forgingblock.io/check-invoice-status", data=payload
            ).json()
            print(result)
            return result["status"]

        except Exception as e:
            return "Failed"

    def get_btc_balance(self, address: str) -> object:
        try:
            payload = {"address": address}
            result = requests.post(
                "https://wallet-api.forgingblock.io/v1/find-btc-address-balance",
                data=payload,
            ).json()
            return result["balance"]

        except Exception as e:
            return "Failed"

    def get_eth_balance(self, address: str) -> object:
        try:
            payload = {"address": address}
            result = requests.post(
                "https://wallet-api.forgingblock.io/v1/find-eth-address-balance",
                data=payload,
            ).json()
            return result["balance"]

        except Exception as e:
            return "Failed"

    def send_btc(self, mnemonic: str, sender: str, amount: float, address: str) -> str:
        "send bitcoin to specific wallet"

        try:
            # fetch wif
            wif = self.get_wif(mnemonic)
            payload = {
                "mnemonic": mnemonic,
                "wif": wif,
                "orgAddress": sender,
                "amountToSend": amount,
                "recipientAddress": address,
            }
            print(payload)

            result = requests.post(
                "https://wallet-api.forgingblock.io/v1/send-btc-transaction",
                data=payload,
            ).json()
            print(result)

            if "error" in result.keys():
                return result["error"]
            else:
                return result["txid"]

        except Exception as ee:
            return "Failed"

    def send_eth(self) -> str:
        "send ethereum to wallet"
        pass
