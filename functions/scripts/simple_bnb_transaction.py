import os
import time
from decimal import Decimal

from globalState import GlobalState
from imports.utils import log_message, private_key_to_bsc_address
from web3 import Web3


def send_bnb(
    sender,
    sender_pk,
    recipients,
    amounts,
    log_file,
    empty_wallet=False,
    max_gas_price_gwei=1,
    retries=3,
    delay=5,
):
    BSC_RPC_URL = "https://bsc-dataseed.binance.org/"
    web3 = Web3(Web3.HTTPProvider(BSC_RPC_URL))
    if isinstance(recipients, str):
        recipients = [recipients]
        amounts = [amounts]

    gas_limit = 21_000

    for i, recipient in enumerate(recipients):
        if empty_wallet and i == len(recipients) - 1:
            balance_wei = web3.eth.get_balance(sender)
            gas_price_wei = web3.eth.gas_price
            max_gas_price_wei = web3.to_wei(max_gas_price_gwei, "gwei")
            gas_price = min(gas_price_wei, max_gas_price_wei)

            # Ensure enough balance for gas
            amount_wei = balance_wei - (gas_limit * gas_price)
            if amount_wei <= 0:
                log_message(
                    f"❌ Not enough balance to empty wallet to {recipient}", log_file
                )
                return
        else:
            amount_wei = web3.to_wei(amounts[i], "ether")

        for attempt in range(retries):
            try:
                gas_price_wei = web3.eth.gas_price
                max_gas_price_wei = web3.to_wei(max_gas_price_gwei, "gwei")
                gas_price = min(gas_price_wei, max_gas_price_wei)

                tx = {
                    "to": recipient,
                    "value": amount_wei,
                    "gas": gas_limit,
                    "gasPrice": gas_price,
                    "nonce": web3.eth.get_transaction_count(sender),
                    "chainId": 56,
                }

                signed_tx = web3.eth.account.sign_transaction(tx, sender_pk)
                tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

                log_message(
                    f"✅ Sent {web3.from_wei(amount_wei, 'ether')} BNB to {recipient}! TX: {web3.to_hex(tx_hash)}",
                    log_file,
                )
                time.sleep(5)  # Short delay
                break

            except Exception as e:
                log_message(
                    f"⚠️ Attempt {attempt + 1}/{retries} failed: {str(e)}", log_file
                )
                if attempt < retries - 1:
                    log_message(f"🔄 Retrying in {delay} seconds...", log_file)
                    time.sleep(delay)
                else:
                    log_message(
                        f"❌ Failed to send BNB to {recipient}, exiting function.",
                        log_file,
                    )
                    return


def send_bnb_transaction(tradeId: str, bot_state: GlobalState):
    tradeDetails = bot_state.get_var(tradeId)
    walletDetails = bot_state.get_wallet_info(tradeId=tradeId)

    log_file = tradeDetails["ourAddress"]

    ourfee = 0
    brokerfee = 0
    amount_to_send = 0
    secret_key = walletDetails["secretKey"]
    recipient_address = tradeDetails["sellerAddress"]

    amount = tradeDetails[
        "tradeAmount"
    ]  # Total amount in BNB, including the transaction fee
    ourfee = Decimal(tradeDetails["fee"])
    brokerfee = Decimal(tradeDetails["broker_fee"])
    brokerAddress = tradeDetails["brokerAddress"]
    recepients = []
    amounts = []
    if ourfee > 0:
        recepients.append(private_key_to_bsc_address(os.getenv("BSC_FEE_PAYER_SECRET")))
        amounts.append(ourfee)
    if brokerfee > 0:
        recepients.append(brokerAddress)
        amounts.append(brokerfee)
    recepients.append(recipient_address)
    amounts.append(amount - ourfee - brokerfee)
    log_message(f"Initiating transaction for Trade ID: {tradeId}", log_file)
    send_bnb(
        private_key_to_bsc_address(secret_key),
        secret_key,
        recepients,
        amounts,
        log_file,
    )
