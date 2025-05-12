from web3 import Web3
from decimal import Decimal
BSC_RPC_URL = "https://bsc-dataseed.binance.org/"
web3 = Web3(Web3.HTTPProvider(BSC_RPC_URL))
USDT_CONTRACT_ADDRESS = "0x55d398326f99059fF775485246999027B3197955"

ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    }
]

def get_finalized_bsc_balance(wallet_address, token=None, confirmations=12):
    latest_block = web3.eth.block_number
    safe_block = max(0, latest_block - confirmations)  

    wallet_address = web3.to_checksum_address(wallet_address)

    if token is None:
        # Get BNB balance from a confirmed block
        balance_wei = web3.eth.get_balance(wallet_address, block_identifier=safe_block)
        return [{"publicKey": wallet_address, "amount": web3.from_wei(balance_wei, 'ether')}, f"https://bscscan.com/address/{wallet_address}"]

    else:
        # Get ERC-20 token balance from a confirmed block
        token = web3.to_checksum_address(token)
        contract = web3.eth.contract(address=token, abi=ERC20_ABI)
        balance = contract.functions.balanceOf(wallet_address).call({'block_identifier': safe_block}) 
        return [{"publicKey": wallet_address, "amount": Decimal(balance / (10 ** 18))}, f"https://bscscan.com/address/{wallet_address}"]


# Test
# wallet = "0x13A3F05547BF4d887a346975f15F2BFe9d9FE445"
# bnb_balance = get_finalized_bsc_balance(wallet)
# usdt_balance = get_finalized_bsc_balance(wallet, USDT_CONTRACT_ADDRESS)

# print(f"BNB Balance: {bnb_balance} BNB")
# print(f"USDT Balance: {usdt_balance} USDT")
