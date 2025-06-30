import base64
import collections
import hashlib
import json
import math
import os
import re
from binascii import Error as BinasciiError
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from decimal import Decimal, InvalidOperation

import base58
import requests
from base58 import b58decode
from Crypto.Cipher import AES
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from eth_account import Account
from solathon import PublicKey
from telegram.error import BadRequest
from telegram.ext import CallbackContext
from web3 import Web3


def get_current_datetime():
    return datetime.now().strftime("[%d%b%y::%H:%M:%S]")


def log_message(message, log_file="error_log", mainThread=False):
    log_dir = "log"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    if mainThread:
        log_file = f"{log_dir}/{log_file}.txt"
    else:
        log_file = f"{log_dir}/wallet_log_{log_file}.txt"
    message = (
        "------Log Entry Open-------\n"
        f"{get_current_datetime()} {message}\n"
        "------Log Entry Close-------\n"
    )
    print(message)
    message = message.encode("utf-8", "ignore").decode("utf-8")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(message + "\n")


def validate_text(input_text, extra=[]):
    allowed_pattern = r"^[a-zA-Z0-9 ,\-$@./:]+$"
    if re.match(allowed_pattern, input_text):
        return True
    else:
        for char in input_text:
            if not re.match(r"[a-zA-Z0-9 ,\-$@./:]", char):
                if char not in extra:
                    return f"Illegal character found: '{char}'"
        return True


def is_number(input_string):
    try:
        # Try converting to an integer
        number = int(input_string)
        return number
    except ValueError:
        try:
            # If not an integer, try converting to a Decimal for precision
            number = Decimal(input_string)
            return number
        except InvalidOperation:
            # If conversion to Decimal fails, it's not a number
            return False


def is_valid_user(input_value, context: CallbackContext):
    try:
        user_chat = ""
        if input_value.isdigit():
            user_chat = context.bot.get_chat(int(input_value))
            if user_chat.type != "private":
                return False
        # else:
        #     if not input_value.startswith("@"):
        #         input_value = f"@{input_value}"
        #     user_chat = context.bot.get_chat(input_value)
        if hasattr(user_chat, "id"):
            return user_chat.id
        else:
            return False

    except (BadRequest, ValueError):
        return False


def is_address_valid(address: str, symbol: str) -> bool:
    if symbol.upper() == "SOL":
        return is_solana_address_valid(address)
    elif symbol.upper() == "LTC":
        return is_litecoin_address_valid(address)
    elif symbol.upper() == "BSC":
        return validate_bsc_address(address)
    elif symbol.upper() == "DOGE":
        return validate_doge_address(address)
    else:
        return False


def is_solana_address_valid(address: str) -> bool:
    try:
        PublicKey(address)
        return True
    except (ValueError, BinasciiError):
        return False


def is_litecoin_address_valid(address: str) -> bool:
    patterns = [
        r"^[LM][1-9A-HJ-NP-Za-km-z]{26,33}$",  # Legacy (P2PKH)
        r"^3[1-9A-HJ-NP-Za-km-z]{26,33}$",  # SegWit (P2SH)
        r"^ltc1[qpzry9x8gf2tvdw0s3jn54khce6mua7l]{39,59}$",  # Bech32
    ]
    if any(re.match(pattern, address) for pattern in patterns):
        return True
    else:
        return False


def validate_doge_address(address: str) -> bool:
    try:
        decoded = b58decode(address)
        if len(decoded) != 25:
            return False
        payload, checksum = decoded[:-4], decoded[-4:]
        hash1 = hashlib.sha256(payload).digest()
        hash2 = hashlib.sha256(hash1).digest()
        return checksum == hash2[:4]
    except Exception as e:
        return False


def validate_bsc_address(address: str) -> bool:
    if not re.match(r"^0x[a-fA-F0-9]{40}$", address):
        return False

    if address != address.lower() and address != address.upper():
        return Web3.is_checksum_address(address)  # ✅ Corrected function

    return True


def multi_task(task_list):
    with ThreadPoolExecutor() as executor:
        futures = []
        for task in task_list:
            fxn = task.pop(0)
            if type(task[0]).__name__ == "dict":
                future = executor.submit(fxn, **task[0])
            else:
                future = executor.submit(fxn, *task)
            futures.append(future)

        result = []
        for future in futures:
            response = future.result()
            result.append(response)
    return result


def private_key_gen():

    key = os.urandom(32)  # Generate a 256-bit key securely
    encoded_key = base64.b64encode(key).decode("utf-8")
    return encoded_key


def get_private_key():
    encoded_key = os.getenv("PRIVATE_KEY")
    key_bytes = base64.b64decode(encoded_key)
    if len(key_bytes) != 32:
        raise ValueError("Error in private key")

    return key_bytes


def encrypt_text(plain_text):

    key = get_private_key()
    if len(key) != 32:
        raise ValueError("Error in private key")

    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(plain_text.encode("utf-8")) + encryptor.finalize()
    encrypted_data = base64.b64encode(iv + ciphertext).decode("utf-8")

    return encrypted_data


def decrypt_text(encrypted_data):

    key = get_private_key()
    encrypted_data_bytes = base64.b64decode(encrypted_data)
    iv = encrypted_data_bytes[:16]  # First 16
    ciphertext = encrypted_data_bytes[16:]
    cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
    decrypted_padded_text = cipher.decrypt(ciphertext)
    try:
        decrypted_text = decrypted_padded_text.decode("utf-8")
    except UnicodeDecodeError:
        decrypted_text = decrypted_padded_text

    return decrypted_text


# def gen_escrow_text(escrow, hide_id=False):

#     escrow_text = f"Escrow ID: {escrow['escrow_id']}\n"
#     if not hide_id:
#         escrow_text = f"Sender: {escrow['sender']}\n"
#     escrow_text += f"Receiver: {escrow['receiver']}\n"
#     escrow_text += f"Amount: {escrow['amount']} {escrow['symbol']}\n"
#     escrow_text += f"Deadline: {escrow['deadline']}\n"
#     escrow_text += f"Status: {escrow['status']}\n"
#     return escrow_text


def calc_fee(amount, fee_rate, symbol, ourfee=False):
    try:
        amount = Decimal(amount)
        fee_rate = Decimal(fee_rate)
        fee = Decimal(amount * fee_rate)
        if ourfee:
            if symbol == "USDT (BSC Bep-20)":
                fee += Decimal("0.1")
            elif symbol == "USDT (TRC20)":
                fee += get_energy_fee_in_usdt()
        if symbol in ["SOL (Solana)", "LTC", "BNB"]:
            fee = fee.quantize(Decimal("0.0000001"))

        else:
            fee = fee.quantize(Decimal("0.001"))

        return fee
    except InvalidOperation:
        return "Invalid amount or fee rate"


def escape_markdown_v2(text):
    escape_chars = r"_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{char}" if char in escape_chars else char for char in text)


def private_key_to_bsc_address(private_key):
    account = Account.from_key(private_key)
    return account.address


def get_trx_price():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": "tron", "vs_currencies": "usd"}
    try:
        resp = requests.get(url, params=params)
        data = resp.json()
        print(data)
        return data.get("tron", {}).get("usd", False)
    except requests.RequestException as e:
        return False


def get_estimated_energy_cost():
    # Credits: https://gist.github.com/andelf/65121c2c7f81e773f5f879d9992843f8
    # Energy costs in trx for USDT transafer on tron chain
    CNTR = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
    PAGE = 1
    PRICE = 140
    try:
        url = f"https://api.trongrid.io/v1/accounts/{CNTR}/transactions?only_confirmed=true&only_to=true&limit=200&search_internal=false"

        resp = requests.get(url)
        payload = resp.json()
        data = payload["data"]

        for i in range(1, PAGE):
            # print(f"paging ... {i}/{PAGE}")
            url = payload["meta"]["links"]["next"]
            resp = requests.get(url)
            payload = resp.json()
            data += payload["data"]
        stat = collections.defaultdict(list)
        txns = 0
        for txn in data:
            if (
                txn.get("energy_usage_total", 0) > 0
                and txn["raw_data"]["contract"][0]["parameter"]["value"][
                    "contract_address"
                ]
                == base58.b58decode_check(CNTR).hex()
            ):
                txns += 1
                stat[txn["ret"][0]["contractRet"]].append(txn["energy_usage_total"])
        return (max(stat["SUCCESS"]) * PRICE) / 1_000_000
    except Exception as e:
        return False


def get_energy_fee_in_usdt():
    x = get_estimated_energy_cost()
    y = get_trx_price()
    return math.ceil(x * y) if x and y else 6
