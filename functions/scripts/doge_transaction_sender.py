import hashlib, os, base58, traceback
from blockcypher import create_unsigned_tx, make_tx_signatures, broadcast_signed_transaction
from blockcypher.api import get_address_full
from ecdsa import SECP256k1, SigningKey
from decimal import Decimal, ROUND_DOWN
from imports.utils import log_message

# Function to convert a hex private key to WIF format
# def hex_to_wif(hex_key, compressed=True):
#     extended_key = 'c0' + hex_key  # 0xc0 is the Dogecoin mainnet prefix
#     if compressed:
#         extended_key += '01'
#     first_sha256 = hashlib.sha256(bytes.fromhex(extended_key)).hexdigest()
#     second_sha256 = hashlib.sha256(bytes.fromhex(first_sha256)).hexdigest()
#     checksum = second_sha256[:8]
#     final_key = extended_key + checksum
#     wif = base58.b58encode(bytes.fromhex(final_key)).decode('utf-8')
#     return wif

# Function to get the public key from a private key in hex format
def privkey_to_pubkey(hex_key):
    priv_key = SigningKey.from_string(bytes.fromhex(hex_key), curve=SECP256k1)
    pub_key = priv_key.get_verifying_key().to_string('compressed').hex()
    return pub_key


def send_doge_transaction(doge_address, doge_private_key_hex, recipient_address, amount_to_send, api_token,  escrow_fee_wallet_address, tradeDetails):
    # Create log directory if it doesn't exist
    log_file = doge_address

    try:
        doge_public_key_hex = privkey_to_pubkey(doge_private_key_hex)

       
        amount_to_send = Decimal(amount_to_send) * Decimal('1e8')  # In LTC
        escrow_fee_satoshi = 0
        broker_fee_satoshi = 0
        amount_to_send_satoshis = int(amount_to_send.quantize(Decimal('1'), rounding=ROUND_DOWN))  # Convert to satoshis

        
        if Decimal(tradeDetails["fee"])>0:
            escrow_fee_satoshi = Decimal(tradeDetails["fee"]) * Decimal('1e8')
            escrow_fee_satoshi = int(Decimal(escrow_fee_satoshi).quantize(Decimal('1'), rounding=ROUND_DOWN))
        if tradeDetails["brokerTrade"]:
            broker_fee_satoshi = Decimal(tradeDetails["broker_fee"]) * Decimal('1e8')
            broker_fee_satoshi = int(Decimal(broker_fee_satoshi).quantize(Decimal('1'), rounding=ROUND_DOWN))

        fee = 0.2 #hardcoded for doge ;)
        fee_satoshis = int(fee * 1e8)
        amount_to_send_satoshis = amount_to_send_satoshis - fee_satoshis - escrow_fee_satoshi - broker_fee_satoshi

        log_message(f"Sending {str(amount_to_send_satoshis)} Satoshi with fee of {str(fee_satoshis)}", log_file)

        # Fetch UTXO details for the address
        address_details = get_address_full(address=doge_address, coin_symbol='doge', api_key=api_token)
        utxos = []

        # Extract UTXOs from txs
        for tx in address_details['txs']:
            for idx, output in enumerate(tx['outputs']):
                if doge_address in output['addresses']:
                    utxos.append({
                        'tx_hash': tx['hash'],
                        'tx_output_n': idx,
                        'value': output['value']
                    })

        # Select the first UTXO for simplicity
        utxo = utxos[0]
        txid = utxo['tx_hash']
        vout = utxo['tx_output_n']
        value = utxo['value']  # In satoshis

        log_message(f"UTXO value: {value}", log_file)

        if value < amount_to_send_satoshis + fee_satoshis + escrow_fee_satoshi + broker_fee_satoshi:
            raise Exception('Insufficient funds')
        change_amount_satoshis = value - (amount_to_send_satoshis + fee_satoshis + escrow_fee_satoshi + broker_fee_satoshi)
        inputs = [{'address': doge_address}]
        outputs = []
        if Decimal(tradeDetails['fee'])>0:
            outputs.append({'address': escrow_fee_wallet_address, 'value': escrow_fee_satoshi})
        
        if Decimal(tradeDetails["broker_fee"])>0:
            outputs.append({'address': tradeDetails["brokerAddress"], 'value': broker_fee_satoshi})
        if change_amount_satoshis > 0:
            amount_to_send_satoshis += change_amount_satoshis
        outputs.append({'address': recipient_address, 'value': amount_to_send_satoshis})
        
        unsigned_tx = create_unsigned_tx(inputs=inputs, outputs=outputs, coin_symbol='doge', api_key=api_token, preference='low')
        outputs.pop()
        outputs.append({'address': recipient_address, 'value': amount_to_send_satoshis+fee_satoshis-unsigned_tx['tx']['fees']})
        unsigned_tx = create_unsigned_tx(inputs=inputs, outputs=outputs, coin_symbol='doge', api_key=api_token, preference='low' ,)
    
        log_message(f"Unsigned TX: {unsigned_tx}", log_file)

        # Sign the transaction
        privkey_list = [doge_private_key_hex]
        pubkey_list = [doge_public_key_hex]
        tx_signatures = make_tx_signatures(txs_to_sign=unsigned_tx['tosign'], privkey_list=privkey_list, pubkey_list=pubkey_list)
        #tx_signatures[0] = tx_signatures[0] + '01'

        log_message(f"Signed signatures: {tx_signatures}", log_file)
        
        # Broadcast the signed transaction
        log_message("Broadcasting TX", log_file)
        response = broadcast_signed_transaction(unsigned_tx=unsigned_tx, signatures=tx_signatures, pubkeys=pubkey_list, coin_symbol='doge', api_key=api_token)

        log_message(f'Transaction hash: {response["tx"]["hash"]}', log_file)
        log_message(f"Transaction Push Response: {response}", log_file)

    except Exception as e:
        error_message = f"An error occurred: {str(e)}\n{traceback.format_exc()}"
        log_message(error_message, log_file)
        raise

def send_transaction(bot_state, action_id):

    # Extract trade and wallet details
    tradeDetails = {}
    if action_id.startswith('TRADE'):
        tradeDetails = bot_state.get_var(action_id)
    elif action_id.startswith('TXID'):
        tradeDetails = bot_state.get_tx_var(action_id)
    walletDetails = bot_state.get_wallet_info(action_id)

    # Source Escrow Wallet Details
    doge_address = walletDetails["publicKey"]
    doge_private_key_hex = walletDetails["secretKey"]

    # To Wallet 
    recipient_address = tradeDetails['sellerAddress']
    amount_to_send = Decimal(tradeDetails["tradeAmount"])  # String
    escrow_fee_wallet_address = bot_state.config['doge_fee_wallet']
    send_doge_transaction(doge_address, doge_private_key_hex, recipient_address, amount_to_send, os.getenv('BLOCK_CYPHER_API_TOKEN'), escrow_fee_wallet_address, tradeDetails)


