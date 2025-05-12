import os, ecdsa, json
import hashlib
import base58
import traceback
from blockcypher import create_unsigned_tx, make_tx_signatures, broadcast_signed_transaction, pushtx
from blockcypher.api import get_address_full
from ecdsa import SECP256k1, SigningKey
from decimal import Decimal, ROUND_DOWN
from imports.utils import log_message
import requests, struct, hashlib, bech32

# def hex_to_wif(hex_key, compressed=True):
#     extended_key = 'b0' + hex_key  # 0xb0 is the Litecoin mainnet prefix
#     if compressed:
#         extended_key += '01'
#     first_sha256 = hashlib.sha256(bytes.fromhex(extended_key)).hexdigest()
#     second_sha256 = hashlib.sha256(bytes.fromhex(first_sha256)).hexdigest()
#     checksum = second_sha256[:8]
#     final_key = extended_key + checksum
#     wif = base58.b58encode(bytes.fromhex(final_key)).decode('utf-8')
#     return wif

def get_unspent(address, token):
    url = (f"https://api.blockcypher.com/v1/ltc/main/addrs/{address}"
           f"?unspentOnly=true&includeScript=true&token={token}")
    response = requests.get(url)
    data = response.json()
    return data.get("txrefs", [])

def privkey_to_pubkey(hex_key):
    priv_key = SigningKey.from_string(bytes.fromhex(hex_key), curve=SECP256k1)
    pub_key = priv_key.get_verifying_key().to_string('compressed').hex()
    return pub_key

def get_blockhash(height, token):
    url = f"https://api.blockcypher.com/v1/ltc/main/blocks/{height}?token={token}"
    response = requests.get(url)
    data = response.json()
    return data.get("hash", None)

def var_int(n):
    if n < 0xfd:
        return struct.pack("B", n)
    elif n <= 0xffff:
        return b'\xfd' + struct.pack("<H", n)
    elif n <= 0xffffffff:
        return b'\xfe' + struct.pack("<I", n)
    else:
        return b'\xff' + struct.pack("<Q", n)

def hash256(data):
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()

def address_to_segwit_scriptpubkey(address):
    
    hrp, data = bech32.bech32_decode(address)
    if hrp != "ltc" or data is None:
        raise ValueError("Invalid Litecoin Bech32 address")
    decoded = bech32.convertbits(data[1:], 5, 8, False)

    if decoded is None:
        raise ValueError("Invalid witness program conversion")
    witness_version = data[0]
    witness_program = decoded
    print(f"HRP: {hrp}")
    print(f"Witness Version: {witness_version}")
    print(f"Witness Program: {witness_program}")
    print(f"Witness Program Length: {len(witness_program)}")
    if witness_version != 0 or len(witness_program) not in (20, 32):
        raise ValueError("Invalid SegWit address witness program")
    witness_program_hex = ''.join(f"{byte:02x}" for byte in witness_program)
    script_pubkey = f"00{len(witness_program):02x}" + witness_program_hex
    return script_pubkey

def create_raw_segwit_transaction(inputs, outputs, version=1, locktime=0):
    tx = b""
    tx += struct.pack("<I", version)
    tx += b"\x00"  # marker
    tx += b"\x01"  # flag

    # Inputs
    tx += var_int(len(inputs))
    for inp in inputs:
        txid = bytes.fromhex(inp["txid"])[::-1]
        vout = struct.pack("<I", inp["vout"])
        # For segwit, scriptSig is empty.
        script_sig = b""
        tx += txid + vout + var_int(len(script_sig)) + script_sig
        tx += struct.pack("<I", inp.get("sequence", 0xffffffff))
    
    # Outputs
    tx += var_int(len(outputs))
    for out in outputs:
        value = struct.pack("<Q", out["value"])
        script_pubkey = bytes.fromhex(out["scriptPubKey"])
        tx += value + var_int(len(script_pubkey)) + script_pubkey

    tx += struct.pack("<I", locktime)
    return tx

def sign_segwit_input(tx, input_idx, inputs, outputs, private_key_hex, sighash=1):
    inp = inputs[input_idx]
    prevouts = b"".join(
        bytes.fromhex(i["txid"])[::-1] + struct.pack("<I", i["vout"]) for i in inputs
    )
    hashPrevouts = hash256(prevouts)

    sequences = b"".join(struct.pack("<I", i.get("sequence", 0xffffffff)) for i in inputs)
    hashSequence = hash256(sequences)
    outs = b"".join(
        struct.pack("<Q", out["value"]) + var_int(len(bytes.fromhex(out["scriptPubKey"]))) + bytes.fromhex(out["scriptPubKey"])
        for out in outputs
    )
    hashOutputs = hash256(outs)
    outpoint = bytes.fromhex(inp["txid"])[::-1] + struct.pack("<I", inp["vout"])
    
    # Extract P2WPKH scriptCode
    if not inp["scriptPubKey"].startswith("0014"):
        raise ValueError("Input scriptPubKey is not in native SegWit format.")
    pubkey_hash = inp["scriptPubKey"][4:]
    scriptCode = bytes.fromhex("76a914" + pubkey_hash + "88ac")
    amount = struct.pack("<Q", inp["value"])
    sequence = struct.pack("<I", inp.get("sequence", 0xffffffff))
    version = struct.pack("<I", 1)
    locktime = tx[-4:]  # Last 4 bytes of tx
    sighash_type = struct.pack("<I", sighash)

    preimage = (
        version +
        hashPrevouts +
        hashSequence +
        outpoint +
        var_int(len(scriptCode)) + scriptCode +
        amount +
        sequence +
        hashOutputs +
        locktime +
        sighash_type
    )

    hash_to_sign = hash256(preimage)
    sk = ecdsa.SigningKey.from_string(bytes.fromhex(private_key_hex), curve=ecdsa.SECP256k1)
    signature_der = sk.sign_digest(hash_to_sign, sigencode=ecdsa.util.sigencode_der_canonize)
    signature = signature_der + b'\x01'
    vk = sk.get_verifying_key()
    x, y = vk.pubkey.point.x(), vk.pubkey.point.y()
    prefix = b'\x02' if y % 2 == 0 else b'\x03'
    pubkey = prefix + x.to_bytes(32, byteorder="big")

    return signature, pubkey

def assemble_segwit_tx(raw_tx, witness_list):
    locktime = raw_tx[-4:]
    tx_without_locktime = raw_tx[:-4]
    witness = b""
    for wit in witness_list:
        witness += var_int(len(wit))
        for item in wit:
            witness += var_int(len(item)) + item
    final_tx = tx_without_locktime + witness + locktime
    return final_tx


def send_ltc_transaction(ltc_address, ltc_private_key_hex, recipient_address, amount_to_send, api_token, escrow_fee_wallet_address, tradeDetails):
    log_file = ltc_address
    try:
        network_fee = Decimal(0.00002)
        ltc_public_key_hex = privkey_to_pubkey(ltc_private_key_hex)

       
        amount_to_send = Decimal(amount_to_send) * Decimal('1e8')  # In LTC
        escrow_fee_satoshi = 0
        broker_fee_satoshi = 0
        amount_to_send_satoshis = int(amount_to_send.quantize(Decimal('1'), rounding=ROUND_DOWN))  # Convert to satoshis

        fee = 0
        fee += network_fee
        
        if Decimal(tradeDetails["fee"])>0:
            escrow_fee_satoshi = Decimal(tradeDetails["fee"]) * Decimal('1e8')
            escrow_fee_satoshi = int(Decimal(escrow_fee_satoshi).quantize(Decimal('1'), rounding=ROUND_DOWN))
            fee += network_fee
        
        if tradeDetails["brokerTrade"]:
            broker_fee_satoshi = Decimal(tradeDetails["broker_fee"]) * Decimal('1e8')
            broker_fee_satoshi = int(Decimal(broker_fee_satoshi).quantize(Decimal('1'), rounding=ROUND_DOWN))
            fee += network_fee

        # fee = network_fee #fee too high
        fee_satoshis = int(fee * Decimal('1e8'))  # Convert to satoshis
        amount_to_send_satoshis = amount_to_send_satoshis - fee_satoshis - escrow_fee_satoshi - broker_fee_satoshi

        log_message(f"Sending {str(amount_to_send_satoshis)} Satoshi with fee of {str(fee_satoshis)}", log_file)
        utxos = get_unspent(ltc_address, api_token)
        if not utxos:
            print("No unspent outputs found for address:", ltc_address)
            return
        print("UTXOs:", json.dumps(utxos, indent=2))
        
        
        utxo = utxos[0]
        value = utxo["value"]
        input_tx = {
            "txid": utxo["tx_hash"],
            "vout": utxo["tx_output_n"],
            "scriptPubKey": utxo["script"],  # Expecting native segwit format.
            "value": value,
            "sequence": 0xffffffff
        }
        log_message(f"UTXO value: {value}", log_file)

        if value < amount_to_send_satoshis + fee_satoshis + escrow_fee_satoshi + broker_fee_satoshi:
            raise Exception('Insufficient funds')
        change_amount_satoshis = value - (amount_to_send_satoshis + fee_satoshis + escrow_fee_satoshi + broker_fee_satoshi)
        print(change_amount_satoshis)
        inputs = [{'address': ltc_address}]
        outputs = []
        
        
        block_height = 2000000
        block_hash = get_blockhash(block_height, api_token)
        print(f"Block hash at height {block_height}: {block_hash}")
        
        outputs = []
        if Decimal(tradeDetails['fee'])>0:
            outputs.append({'scriptPubKey': address_to_segwit_scriptpubkey(escrow_fee_wallet_address), 'value': escrow_fee_satoshi})
        if Decimal(tradeDetails["broker_fee"])>0 and tradeDetails["brokerTrade"]:
            outputs.append({'scriptPubKey': address_to_segwit_scriptpubkey(tradeDetails['brokerAddress']), 'value': broker_fee_satoshi})
        if change_amount_satoshis > 0:
            amount_to_send_satoshis += change_amount_satoshis
        outputs.append({'scriptPubKey': address_to_segwit_scriptpubkey(recipient_address), 'value': amount_to_send_satoshis})

        raw_tx = create_raw_segwit_transaction([input_tx], outputs, version=1, locktime=0)
        print("Raw TX (no witness) Hex:", raw_tx.hex())

        signature, pubkey = sign_segwit_input(raw_tx, 0, [input_tx], outputs, ltc_private_key_hex, sighash=1)
        print("Signature (DER + SIGHASH):", signature.hex())
        print("Compressed Pubkey:", pubkey.hex())

        witness_list = [[signature, pubkey]]

        final_tx = assemble_segwit_tx(raw_tx, witness_list)
        print("Final SegWit TX Hex:", final_tx.hex())
        print(pushtx(final_tx.hex(), coin_symbol='ltc', api_key=api_token))
        
    except Exception as e:
        error_message = f"An error occurred: {str(e)}\n{traceback.format_exc()}"
        log_message(error_message, log_file)
        raise



def send_transaction(bot_state, action_id):
    tradeDetails = {}
    if action_id.startswith('TRADE'):
        tradeDetails = bot_state.get_var(action_id)
    elif action_id.startswith('TXID'):
        tradeDetails = bot_state.get_tx_var(action_id)
    walletDetails = bot_state.get_wallet_info(action_id)
    ltc_address = walletDetails["publicKey"]
    ltc_private_key_hex = walletDetails["secretKey"]
    recipient_address = tradeDetails['sellerAddress']
    amount_to_send = tradeDetails["tradeAmount"]
    escrow_fee_wallet_address = bot_state.config['ltc_fee_wallet']
    send_ltc_transaction(ltc_address, ltc_private_key_hex, recipient_address, amount_to_send, os.getenv('BLOCK_CYPHER_API_TOKEN'), escrow_fee_wallet_address, tradeDetails)


