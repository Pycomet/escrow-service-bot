from web3 import Web3
from web3.middleware import geth_poa_middleware
from decimal import Decimal
def validate_and_format_address(address):
    
    if not Web3.is_checksum_address(address):
        raise ValueError("Invalid address format")

    return Web3.to_checksum_address(address)

def get_finalized_balance(address, min_confirmations=15):
    w3 = Web3(Web3.HTTPProvider('https://bsc-dataseed.binance.org/'))  # Mainnet
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    try:
        address = validate_and_format_address(address)
    except ValueError as e:
        raise ValueError(f"Address validation failed: {e}")
    balance_wei = w3.eth.get_balance(address)
    balance_eth = w3.from_wei(balance_wei, 'ether')

    return Decimal(balance_eth)


