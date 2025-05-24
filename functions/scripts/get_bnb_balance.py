from web3 import Web3
# Note: geth_poa_middleware import has changed in newer web3 versions
try:
    from web3.middleware import geth_poa_middleware
except ImportError:
    # For newer versions of web3
    from web3.middleware import simple_cache_middleware as geth_poa_middleware
from decimal import Decimal

def validate_and_format_address(address):
    
    if not Web3.is_checksum_address(address):
        raise ValueError("Invalid address format")

    return Web3.to_checksum_address(address)

def get_balance_bnb_bsc(address, min_confirmations=15):
    w3 = Web3(Web3.HTTPProvider('https://bsc-dataseed.binance.org/'))  # Mainnet
    # Note: BSC doesn't actually need PoA middleware, but keeping for compatibility
    try:
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    except:
        pass  # Skip if middleware injection fails
    
    try:
        address = validate_and_format_address(address)
    except ValueError as e:
        raise ValueError(f"Address validation failed: {e}")
    
    balance_wei = w3.eth.get_balance(address)
    balance_eth = w3.from_wei(balance_wei, 'ether')

    return Decimal(balance_eth)


