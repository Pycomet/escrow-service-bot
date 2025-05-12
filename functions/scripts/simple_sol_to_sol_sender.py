import base64
import base58, traceback, os
from solathon.core.instructions import transfer
from solathon import Client, Transaction, PublicKey, Keypair
from decimal import Decimal
from globalState import GlobalState
from imports.utils import log_message
from solana.constants import SYSTEM_PROGRAM_ID
from solathon.core.instructions import Instruction, AccountMeta
import struct

log_file = ''
def sol_to_lamports(sol_amount_str):
    # Convert SOL amount (string) to Decimal
    sol_amount = Decimal(sol_amount_str)
    # Convert to lamports (1 SOL = 1,000,000,000 lamports)
    lamports = int(sol_amount * Decimal(1_000_000_000))
    return lamports

def is_account_initialized(client: Client, pub_key):
    """Check if a Solana account is initialized (exists)."""
    try: # idk why get_account_info doesn't give None as result for non existent account ;(
        account_info = client.get_account_info(pub_key)
        if account_info is None or "error" in account_info:
            return False  # Account is not initialized
        
        balance = account_info.get("lamports", 0)
        return balance > 0  # Returns True if initialized
    except Exception as e:
        return False  # Account does not exist or API error

def send_transaction(hex_private_key, recipient_address, sol_amount_str, log_file, tradeDetails,  fee_payer_private_key ):
    try: 
        client = Client("https://api.mainnet-beta.solana.com")

        RENT_EXEMPT_BALANCE = client.get_minimum_balance_for_rent_exemption(0)

        brokerAddress = None
        if tradeDetails['brokerTrade']:
            brokerAddress = tradeDetails['brokerAddress']
        
        #Escrow Wallet
        private_key_base58 = base58.b58encode(bytes.fromhex(hex_private_key)).decode('utf-8')
        keypair = Keypair.from_private_key(private_key_base58)
        #Fee Wallet
        fee_wallet_key_base58 = base58.b58encode(bytes.fromhex(fee_payer_private_key)).decode('utf-8')
        fee_wallet_keypair = Keypair.from_private_key(fee_wallet_key_base58)

        
        our_fee = sol_to_lamports(tradeDetails['fee'])
        broker_fee = sol_to_lamports(tradeDetails['broker_fee'])
        sol_amount_str = Decimal(sol_amount_str) 
        amount = sol_to_lamports(sol_amount_str) - our_fee - broker_fee
        fee = 5000
        send_amount = amount
        
        
        if send_amount <= 0:
            raise ValueError("The amount to send is too low to cover the transaction fee.")
        
        

        # Create transfer instructions
        instructions = []
        
        #Dev's fee cut

        if our_fee>0:
            
            instruction = transfer(
                from_public_key=keypair.public_key,
                to_public_key=fee_wallet_keypair.public_key, 
                lamports=our_fee
            )
            instructions.append(instruction)


        # Broker's cut

        if tradeDetails['broker_fee']>0:
            broker_acc_initialized = is_account_initialized(client, PublicKey(brokerAddress))
            a = broker_fee if broker_acc_initialized else max(broker_fee, RENT_EXEMPT_BALANCE)
            
            instruction = transfer(
                from_public_key=keypair.public_key,
                to_public_key=PublicKey(brokerAddress), 
                lamports=a
            )
            instructions.append(instruction)
        
       
        # Recepient's amount

        send_amount -= fee
        b = send_amount if broker_acc_initialized else min((send_amount+broker_fee-RENT_EXEMPT_BALANCE), send_amount)
        sender_balance = client.get_balance(keypair.public_key)
        change = sender_balance-our_fee-a-b-fee
        if change>0:
            b+=change
        instruction = transfer(
            from_public_key=keypair.public_key,
            to_public_key=PublicKey(recipient_address), 
            lamports=b
        )
        instructions.append(instruction)


        transaction = Transaction(instructions=instructions, signers=[keypair])
        # print(transaction.instructions)
        # Send the transaction
        result = client.send_transaction(transaction)
        return result
    except Exception as e:
        error_message = f"An error occurred: {str(e)}\n"
        error_message += ''.join(traceback.format_exception(None, e, e.__traceback__))
        
        # Log the detailed error message
        log_message(error_message, log_file)


def simple_sol_to_sol_transaction(action_id, bot_state: GlobalState):
    tradeDetails = {}
    if action_id.startswith('TRADE'):
        tradeDetails = bot_state.get_var(action_id)
    elif action_id.startswith('TXID'):
        tradeDetails = bot_state.get_tx_var(action_id)
    walletDetails = bot_state.get_wallet_info(action_id)

    log_file = tradeDetails['ourAddress']
    hex_private_key = walletDetails['secretKey']
    recipient_address = tradeDetails['sellerAddress']
    amount_to_send = tradeDetails["tradeAmount"] 
    
    log_message(f"Initiating transaction for Trade ID: {action_id}", log_file)
    log_message(f"Sender: {walletDetails['publicKey']}, Recipient: {recipient_address}, Amount: {amount_to_send} USDT", log_file)

    response = send_transaction(hex_private_key, recipient_address, amount_to_send, log_file, tradeDetails, os.getenv('SOLANA_FEE_PAYER_SECRET'))
    log_message(f"Transaction response: {response}", log_file)



# TEst run2



