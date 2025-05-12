from web3 import Web3
from eth_account import Account
import json, time, os
from globalState import GlobalState
from imports.utils import log_message
from decimal import Decimal
from imports.utils import private_key_to_bsc_address
from imports.simple_bnb_transaction import send_bnb



USDT_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    }
]
USDT_CONTRACT_ADDRESS = "0x55d398326f99059fF775485246999027B3197955"

def send_gas_funding(web3, sender, sender_pk, receiver, log_file, gas_price_gwei=1, estimated_gas_usage=60000, buffer_percentage=0.05):
    try:
        gas_price = web3.to_wei(gas_price_gwei, 'gwei')
        gas_needed_wei = gas_price * estimated_gas_usage

        gas_needed_wei = int(gas_needed_wei * (1 + buffer_percentage)) # 10% buff

        receiver_balance_wei = web3.eth.get_balance(receiver)
        if receiver_balance_wei >= gas_needed_wei:
            log_message(f"✅ Wallet {receiver} already has enough BNB for gas. No need to send more.", log_file)
            return True

        sender_balance_wei = web3.eth.get_balance(sender)
        if sender_balance_wei < gas_needed_wei:
            log_message(f"🚨 Not enough BNB in {sender}! Cannot send gas funds.", log_file)
            return None

        # Only send the required difference
        amount_to_send = gas_needed_wei - receiver_balance_wei

        nonce = web3.eth.get_transaction_count(sender)
        tx = {
            'nonce': nonce,
            'to': receiver,
            'value': amount_to_send,
            'gas': 21000,  # Standard transfer
            'gasPrice': gas_price,
            'chainId': 56
        }

        signed_tx = web3.eth.account.sign_transaction(tx, sender_pk)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

        log_message(f"✅ Sent {web3.from_wei(amount_to_send, 'ether')} BNB to {receiver}", log_file)
        log_message(f"🔗 Transaction Hash: {web3.to_hex(tx_hash)}", log_file)

        return web3.to_hex(tx_hash)
    except Exception as e:
        log_message(f"❌ Error sending gas: {str(e)}", log_file)
        return None

def send_usdt_transaction(web3, sender, sender_pk, recipient, amount_wei, log_file):
    gas_price_gwei=1
    gas_limit=60000
    usdt_contract = web3.eth.contract(address=USDT_CONTRACT_ADDRESS, abi=USDT_ABI)

    try:
        
        nonce = web3.eth.get_transaction_count(sender)
        gas_price = web3.to_wei(gas_price_gwei, 'gwei')
        tx = usdt_contract.functions.transfer(recipient, amount_wei).build_transaction({
            'from': sender,
            'nonce': nonce,
            'gas': gas_limit,  
            'gasPrice': gas_price,
            'chainId': 56
        })

        signed_tx = web3.eth.account.sign_transaction(tx, sender_pk)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

        log_message(f"✅ USDT Sent! {web3.from_wei(amount_wei, 'ether')} USDT to {recipient}", log_file)
        log_message(f"🔗 Transaction Hash: {web3.to_hex(tx_hash)}", log_file)

        return web3.to_hex(tx_hash)

    except Exception as e:
        log_message(f"❌ Error sending USDT: {str(e)}", log_file)
        return None

def usdt_bnb_transaction(action_id, bot_state: GlobalState):
    tradeDetails = {}
    if action_id.startswith('TRADE'):
        tradeDetails = bot_state.get_var(action_id)
    elif action_id.startswith('TXID'):
        tradeDetails = bot_state.get_tx_var(action_id)
    walletDetails = bot_state.get_wallet_info(action_id)

    log_file = tradeDetails['ourAddress']
    escrow_private_key = walletDetails['secretKey']
    recipient_address = tradeDetails['sellerAddress']
    amount_to_send = Decimal(tradeDetails["tradeAmount"])
    
    log_message(f"Initiating transaction for Trade ID: {action_id}", log_file)
    log_message(f"Sender: {walletDetails['publicKey']}, Recipient: {recipient_address}, Amount: {amount_to_send} USDT", log_file)

    response = send_transaction(os.getenv('BSC_FEE_PAYER_SECRET'), escrow_private_key, recipient_address, amount_to_send, log_file, tradeDetails)
    log_message(f"Transaction response: {response}", log_file)

def send_transaction(environment_wallet_key, escrow_private_key, recipient_address, amount_to_send, log_file, tradeDetails):
    brokerfee = 0
    brokerAddress = ''
    if tradeDetails['brokerTrade']:
        brokerfee = Decimal(tradeDetails['broker_fee'])
        brokerAddress = tradeDetails['brokerAddress']
    
    fixed_fee = 0.00019 #bnb ~$0.1
    ourfee = Decimal(tradeDetails['fee'])
    # ourfee += fixed_fee
    

    
    # Therefore 3 tx if broker present
    BSC_RPC_URL = "https://bsc-dataseed.binance.org/"
    web3 = Web3(Web3.HTTPProvider(BSC_RPC_URL))

    gas_tx_hash = send_gas_funding(web3, private_key_to_bsc_address(environment_wallet_key), environment_wallet_key, private_key_to_bsc_address(escrow_private_key), log_file)

    if gas_tx_hash:
        log_message("⏳ Waiting 10s for gas transaction to be confirmed...", log_file)
        time.sleep(10)

        log_message("🔹 Transferring USDT from Escrow to ENV Wallet...", log_file)
        amount_in_wei = int(amount_to_send * (10 ** 18))
        
        usdt_tx_hash = send_usdt_transaction(web3, private_key_to_bsc_address(escrow_private_key), escrow_private_key, private_key_to_bsc_address(environment_wallet_key), amount_in_wei, log_file)
        

        if usdt_tx_hash:
            log_message(f"🎉 USDT Tranfer Successful to ENV Wallet! Hash: {usdt_tx_hash}", log_file)
        else:
            log_message("🚨 USDT Transfer Failed to ENV Wallet!", log_file)
            return
        log_message("⏳ Waiting 10s for USDT transaction to be confirmed...", log_file)
        time.sleep(10)

        #All funds in ENV wallet we assume
        seller_amount_to_send = amount_to_send - ourfee - brokerfee 
        seller_amount_to_send = int(seller_amount_to_send * (10 ** 18))
        broker_amount_in_wei = int(brokerfee * (10 ** 18))

        #Transfer USDT to Broker
        if brokerfee>0:
            log_message("🔹 Transferring USDT from ENV to Broker's Wallet...", log_file)
            usdt_tx_hash = send_usdt_transaction(web3, private_key_to_bsc_address(environment_wallet_key), environment_wallet_key, brokerAddress, broker_amount_in_wei, log_file)

            if usdt_tx_hash:
                log_message(f"🎉 USDT Tranfer Successful to Broker! Hash: {usdt_tx_hash}", log_file)
            else:
                log_message("🚨 USDT Transfer Failed to Broker!", log_file)
                return
            log_message("⏳ Waiting 10s for USDT transaction to be confirmed...", log_file)
            time.sleep(10)
        #Transfer USDT to Recepient(Seller)
        
        log_message("🔹 Transferring USDT from ENV to Seller's Wallet...", log_file)
        usdt_tx_hash = send_usdt_transaction(web3, private_key_to_bsc_address(environment_wallet_key), environment_wallet_key, recipient_address, seller_amount_to_send, log_file)

        if usdt_tx_hash:
            log_message(f"🎉 USDT Tranfer Successful to Seller! Hash: {usdt_tx_hash}", log_file)
        else:
            log_message("🚨 USDT Transfer Failed to Seller!", log_file)
            return
        
        #Claiming leftover funds
        time.sleep(5)
        log_message("🔹 Trying to claim back leftover funds...", log_file)
        send_bnb(private_key_to_bsc_address(escrow_private_key), escrow_private_key, private_key_to_bsc_address(environment_wallet_key), 1, log_file, empty_wallet=True, max_gas_price_gwei=1, retries=3, delay=5)


