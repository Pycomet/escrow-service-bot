import time
from tronpy import Tron
from tronpy.keys import PrivateKey

def send_token_tx(private_key_hex, recipient_address, token_amount, token_contract_address, fee_limit=10_000_000):
   
    client = Tron(network="shasta")
    
    
    contract = client.get_contract(token_contract_address)
    

    priv_key = PrivateKey(bytes.fromhex(private_key_hex))
    
   
    sender_address = priv_key.public_key.to_base58check_address()
    
 
    amount = int(token_amount * 1_000_000)
    
    # Build, sign, and broadcast the transfer transaction
    txn = (
        contract.functions.transfer(recipient_address, amount)
        .with_owner(sender_address)
        .fee_limit(fee_limit)
        .build()
        .sign(priv_key)
    )
    
    result = txn.broadcast()
    txid = result.get("txid")
    print(f"Transaction broadcasted. TXID: {txid}")
    
    # Poll for transaction info until available (this may take a few seconds)
    tx_info = None
    for _ in range(20):
        tx_info = client.get_transaction_info(txid)
        if tx_info:
            break
        time.sleep(1)
    
    if not tx_info:
        print("Transaction info not available yet.")
    else:
        # Energy consumed is reported in the transaction info (if applicable)
        energy_used = tx_info.get("energy_used", 0)
        # TRX fee is energy_used in SUN if no free energy is used.
        trx_fee = energy_used  # in SUN (1 TRX = 1,000,000 SUN)
        print(f"Energy used: {energy_used} units")
        print(f"Approximate TRX fee (if no free Energy available): {trx_fee / 1_000_000} TRX")
        print(f"View transaction: https://shasta.tronscan.org/#/transaction/{txid}")
    
    return txid

# Example usage:
if __name__ == "__main__":
    PRIVATE_KEY = "8e0213d1d47580e940dd6317cd2a7d050eefd33a2a00a517618a0616b5fa08f3"
    RECIPIENT = "RECIPIENT_ADDRESS_HERE"
    TOKEN_CONTRACT = "TXy6wdiMaqJBt8TDYgvr8H4SM6csonPVXL"
    TOKEN_AMOUNT = 100
    
    send_token_tx(PRIVATE_KEY, RECIPIENT, TOKEN_AMOUNT, TOKEN_CONTRACT)
