import json
import os
import traceback
from decimal import Decimal

import base58
import requests
from globalState import GlobalState
from imports.utils import log_message
from solana.rpc.api import Client
from solana.rpc.commitment import Finalized, Processed
from solana.rpc.types import TxOpts
from solathon import keypair as solkeypair
from solders import message
from solders.hash import Hash
from solders.keypair import Keypair
from solders.message import Message
from solders.pubkey import Pubkey
from solders.token.associated import get_associated_token_address
from solders.transaction import Transaction, VersionedTransaction
from spl.token.instructions import (
    TransferCheckedParams,
    create_associated_token_account,
)
from spl.token.instructions import (
    get_associated_token_address as sol_get_associated_token_address,
)
from spl.token.instructions import transfer_checked


def get_latest_blockhash(log_file):
    url = "https://api.mainnet-beta.solana.com"
    headers = {"Content-Type": "application/json"}
    payload = {
        "id": 1,
        "jsonrpc": "2.0",
        "method": "getLatestBlockhash",
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))
    response_json = response.json()

    if "result" in response_json:
        blockhash = response_json["result"]["value"]["blockhash"]
        return blockhash
    else:
        log_message("Failed to fetch the latest blockhash", log_file)
        log_message(response_json, log_file)
    # try:
    #     transaction_json = json.loads(transaction_json_str)
    # except json.JSONDecodeError as e:
    #     print(f"Invalid JSON string: {e}")
    #     return {"error": f"Invalid JSON string: {e}"}

    # # Convert the transaction to bytes and then encode it in base64
    # transaction_bytes = json.dumps(transaction_json).encode('utf-8')
    # transaction_base58 = base58.b58encode(transaction_bytes).decode('utf-8')

    # # Create the payload for the RPC request
    # payload = {
    #     "jsonrpc": "2.0",
    #     "id": 1,
    #     "method": "sendTransaction",
    #     "params": [transaction_base58]
    # }

    # # Send the transaction via a POST request
    # headers = {"Content-Type": "application/json"}
    # response = requests.post(rpc_url, headers=headers, json=payload)

    # # Check for HTTP request errors
    # try:
    #     response.raise_for_status()
    # except requests.exceptions.HTTPError as err:
    #     print(f"HTTP error occurred: {err}")
    #     return {"error": str(err)}

    # # Parse the response JSON
    # result = response.json()

    # return result


def send_transaction(
    sender_private_key,
    fee_payer_private_key,
    recipient_address,
    send_amount,
    log_file,
    tradeDetails,
    brokerAddress=None,
):
    try:
        # Connect to Solana client
        client = Client("https://api.mainnet-beta.solana.com")

        # Escrow Wallet

        temp_keypair = solkeypair.Keypair.from_private_key(
            base58.b58encode(bytes.fromhex(sender_private_key)).decode("utf-8")
        )
        public_key_bytes = bytes(temp_keypair.public_key)
        sender_private_key = bytes.fromhex(sender_private_key) + public_key_bytes
        sender_private_key = base58.b58encode(sender_private_key).decode("utf-8")

        # Fee Payer wallet

        temp_keypair = solkeypair.Keypair.from_private_key(
            base58.b58encode(bytes.fromhex(fee_payer_private_key)).decode("utf-8")
        )
        public_key_bytes = bytes(temp_keypair.public_key)
        fee_payer_private_key = bytes.fromhex(fee_payer_private_key) + public_key_bytes
        fee_payer_private_key = base58.b58encode(fee_payer_private_key).decode("utf-8")
        usdt_mint_address = "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"
        sender = Keypair.from_base58_string(sender_private_key)
        fee_payer = Keypair.from_base58_string(fee_payer_private_key)
        usdt_mint_address_bytes = base58.b58decode(usdt_mint_address)
        recipient_address_bytes = base58.b58decode(recipient_address)
        broker_address_bytes = None
        if tradeDetails["broker_fee"] > 0:
            broker_address_bytes = base58.b58decode(brokerAddress)

        sender_token_address = get_associated_token_address(
            sender.pubkey(), Pubkey(usdt_mint_address_bytes)
        )
        fee_payer_token_address = get_associated_token_address(
            fee_payer.pubkey(), Pubkey(usdt_mint_address_bytes)
        )
        recipient_token_address = get_associated_token_address(
            Pubkey(recipient_address_bytes), Pubkey(usdt_mint_address_bytes)
        )
        broker_token_address = None
        if tradeDetails["broker_fee"] > 0:
            broker_token_address = get_associated_token_address(
                Pubkey(broker_address_bytes), Pubkey(usdt_mint_address_bytes)
            )
        # amount = send_amount * Decimal(1_000_000)
        # ourfee = Decimal(0.02) * amount
        # finalamount = int(amount-ourfee)
        # ourfee = int(ourfee)

        amount = (Decimal(send_amount) - Decimal(tradeDetails["fee"])) * Decimal(
            1_000_000
        )
        ourfee = Decimal(tradeDetails["fee"]) * Decimal(1_000_000)
        brokerfee = Decimal(tradeDetails["broker_fee"]) * Decimal(1_000_000)
        finalamount = int(amount - ourfee - brokerfee)
        ourfee = int(ourfee)
        brokerfee = int(brokerfee)

        spl_creation_fee = int(Decimal(0.39) * Decimal(1_000_000))

        # Recepient's USDT account creation
        account_info = client.get_account_info(recipient_token_address)
        instruction = []

        if account_info.value is None:
            log_message(
                "Token account does not exist. Creating token account for receiver wallet...",
                log_file,
            )
            log_message("adding charges to out wallet", log_file)
            ourfee += spl_creation_fee
            finalamount -= spl_creation_fee

            instruction.append(
                create_associated_token_account(
                    payer=fee_payer.pubkey(),
                    owner=Pubkey(recipient_address_bytes),
                    mint=Pubkey(usdt_mint_address_bytes),
                )
            )
        # Dev's USDT account creation
        account_info = client.get_account_info(fee_payer_token_address)
        if account_info.value is None:
            log_message(
                "Token account does not exist. Creating token account for fee payer wallet...",
                log_file,
            )

            instruction.append(
                create_associated_token_account(
                    payer=fee_payer.pubkey(),
                    owner=Pubkey(fee_payer_token_address),
                    mint=Pubkey(usdt_mint_address_bytes),
                )
            )
        # Broker's USDT account creation
        if tradeDetails["broker_fee"] > 0:
            account_info = client.get_account_info(broker_token_address)
            if account_info.value is None:
                log_message(
                    "Token account does not exist. Creating token account for broker wallet...",
                    log_file,
                )
                log_message("adding charges to out wallet", log_file)

                ourfee += spl_creation_fee
                finalamount -= spl_creation_fee

                instruction.append(
                    create_associated_token_account(
                        payer=fee_payer.pubkey(),
                        owner=Pubkey(broker_address_bytes),
                        mint=Pubkey(usdt_mint_address_bytes),
                    )
                )
        # Dev's part in amount
        instruction.append(
            transfer_checked(
                TransferCheckedParams(
                    program_id=Pubkey(
                        base58.b58decode("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
                    ),
                    source=sender_token_address,
                    mint=Pubkey(usdt_mint_address_bytes),
                    dest=fee_payer_token_address,
                    owner=sender.pubkey(),
                    amount=ourfee,
                    decimals=6,
                )
            )
        )
        # Broker's part in amount
        if tradeDetails["broker_fee"] > 0:
            instruction.append(
                transfer_checked(
                    TransferCheckedParams(
                        program_id=Pubkey(
                            base58.b58decode(
                                "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
                            )
                        ),
                        source=sender_token_address,
                        mint=Pubkey(usdt_mint_address_bytes),
                        dest=broker_token_address,
                        owner=sender.pubkey(),
                        amount=brokerfee,
                        decimals=6,
                    )
                )
            )
        # Recepient's part in amount
        instruction.append(
            transfer_checked(
                TransferCheckedParams(
                    program_id=Pubkey(
                        base58.b58decode("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
                    ),
                    source=sender_token_address,
                    mint=Pubkey(usdt_mint_address_bytes),
                    dest=recipient_token_address,
                    owner=sender.pubkey(),
                    amount=finalamount,
                    decimals=6,
                )
            )
        )
        recent_hash = get_latest_blockhash(log_file)
        message1 = Message(
            instructions=instruction,
            payer=fee_payer.pubkey(),
            # recent_blockhash=Hash.from_string(get_latest_blockhash(log_file))
        )
        tempTrans = Transaction(
            from_keypairs=[fee_payer, sender],
            message=message1,
            recent_blockhash=Hash.from_string(recent_hash),
        )
        print(tempTrans)
        tempTrans.sign(
            [fee_payer, sender], recent_blockhash=Hash.from_string(recent_hash)
        )
        transaction = VersionedTransaction.from_bytes(tempTrans.__bytes__())

        # EH well why make it more complex lol
        # signature = fee_payer.sign_message(message.to_bytes_versioned(transaction.message))
        # signature2 = sender.sign_message(message.to_bytes_versioned(transaction.message))
        # signed_txn = VersionedTransaction.populate(transaction.message, [signature, signature2])

        opts = TxOpts(
            skip_preflight=False, preflight_commitment=Finalized, max_retries=5
        )
        result = client.send_raw_transaction(txn=bytes(transaction), opts=opts)
        transaction_id = json.loads(result.to_json())["result"]
        log_message(f"TX response: {result.to_json()}", log_file)
        log_message(
            f"Transaction sent: https://solscan.io/tx/{transaction_id}", log_file
        )
    except Exception as e:
        error_message = f"An error occurred: {str(e)}\n"
        error_message += "".join(traceback.format_exception(None, e, e.__traceback__))

        log_message(error_message, log_file)


def send_usdt_sol_transaction(action_id, bot_state: GlobalState):
    tradeDetails = {}
    if action_id.startswith("TRADE"):
        tradeDetails = bot_state.get_var(action_id)
    elif action_id.startswith("TXID"):
        tradeDetails = bot_state.get_tx_var(action_id)
    walletDetails = bot_state.get_wallet_info(action_id)

    log_file = tradeDetails["ourAddress"]
    sender_private_key = walletDetails["secretKey"]
    recipient_address = tradeDetails["sellerAddress"]
    send_amount = Decimal(tradeDetails["tradeAmount"])

    log_message(f"Initiating transaction for Trade ID: {action_id}", log_file)
    log_message(
        f"Sender: {walletDetails['publicKey']}, Recipient: {recipient_address}, Amount: {send_amount} USDT",
        log_file,
    )

    if tradeDetails["brokerTrade"]:
        send_transaction(
            sender_private_key,
            os.getenv("SOLANA_FEE_PAYER_SECRET"),
            recipient_address,
            send_amount,
            log_file,
            tradeDetails,
            tradeDetails["brokerAddress"],
        )
    else:
        send_transaction(
            sender_private_key,
            os.getenv("SOLANA_FEE_PAYER_SECRET"),
            recipient_address,
            send_amount,
            log_file,
            tradeDetails,
        )
    log_message(f"Transaction for Trade ID {action_id} completed", log_file)


# def get_usdt_account_creation_fee():
#     SOLANA_RPC_URL = "https://api.mainnet-beta.solana.com"
#     SOL_PRICE_API = "https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd"
#     headers = {"Content-Type": "application/json"}
#     payload = {
#         "jsonrpc": "2.0",
#         "id": 1,
#         "method": "getMinimumBalanceForRentExemption",
#         "params": [165]
#     }
#     response = requests.post(SOLANA_RPC_URL, headers=headers, data=json.dumps(payload))
#     rent_exempt_balance = response.json()["result"]
#     rent_exempt_balance_sol = rent_exempt_balance / 1_000_000_000
#     sol_price_response = requests.get(SOL_PRICE_API)
#     sol_price = sol_price_response.json()["solana"]["usd"]
#     rent_exempt_balance_usd = rent_exempt_balance_sol * sol_price

#     return {
#         "rent_exempt_balance_lamports": rent_exempt_balance,
#         "rent_exempt_balance_sol": rent_exempt_balance_sol,
#         "sol_price_usd": sol_price,
#         "rent_exempt_balance_usd": rent_exempt_balance_usd
#     }

# LOVE you Solana


# Issue1: After sending 2 taking a fee of 2% ie 0.04 but still leaves tiny amount of 0.000001 on escrow wallet (83hCEcaxPMSzaJAc2UAJ9tojeFLyweyeZvZwDs8JEdSv)
# reason: Not tried to figure yet
