from web3 import Web3
from eth_account import Account
import json, time, os
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

# USDT contract ABI (ERC-20 standard)
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
    },
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }
]

# USDT contract address on Ethereum mainnet
USDT_CONTRACT_ADDRESS = "0xdAC17F958D2ee523a2206206994597C13D831ec7"

def send_usdt_ethereum_transaction(sender_private_key, recipient_address, amount_usdt, log_file=None):
    """
    Send USDT on Ethereum network
    
    NOTE: This is a custom implementation where USDT fees are paid in USDT,
    not ETH as in standard Ethereum. The system deducts 10 USDT as fee.
    
    Args:
        sender_private_key (str): Private key of sender wallet
        recipient_address (str): Recipient's Ethereum address
        amount_usdt (float): Amount of USDT to send
        log_file (str): Optional log file identifier
    
    Returns:
        str: Transaction hash if successful, None if failed
    """
    try:
        logger.info(f"=== CUSTOM USDT ETHEREUM TRANSACTION ===")
        logger.info(f"System: USDT fees paid in USDT (10 USDT fee)")
        logger.info(f"Amount: {amount_usdt} USDT")
        logger.info(f"Fee: 10 USDT (deducted by system)")
        logger.info(f"Total USDT needed: {float(amount_usdt) + 10} USDT")
        
        # Connect to Ethereum mainnet
        infura_id = os.getenv('INFURA_PROJECT_ID', '104abeafa90045c490605995b21684c1')
        if infura_id and infura_id != 'your-infura-project-id':
            ETH_RPC_URL = f"https://mainnet.infura.io/v3/{infura_id}"
            logger.info(f"Using Infura endpoint: {ETH_RPC_URL[:50]}...")
        else:
            # Fallback to public RPC endpoints
            ETH_RPC_URL = "https://eth.llamarpc.com"  # Public Ethereum RPC
            logger.warning("Using public RPC endpoint. Consider setting INFURA_PROJECT_ID for better reliability.")
        
        web3 = Web3(Web3.HTTPProvider(ETH_RPC_URL))
        
        if not web3.is_connected():
            logger.error("Failed to connect to Ethereum network")
            return None
        
        # Get sender account from private key
        account = Account.from_key(sender_private_key)
        sender_address = account.address
        
        logger.info(f"Sending {amount_usdt} USDT from {sender_address} to {recipient_address}")
        
        # Create contract instance
        usdt_contract = web3.eth.contract(address=USDT_CONTRACT_ADDRESS, abi=USDT_ABI)
        
        # Convert amount to wei (USDT has 6 decimals)
        amount_wei = int(Decimal(str(amount_usdt)) * Decimal('1000000'))
        
        # Check USDT balance (system already checked this includes fee)
        usdt_balance = usdt_contract.functions.balanceOf(sender_address).call()
        usdt_balance_readable = usdt_balance / 1000000
        logger.info(f"Current USDT balance: {usdt_balance_readable} USDT")
        
        # In this custom system, we only check if we have enough USDT for the amount
        # The 10 USDT fee is handled by the admin system, not by ETH gas
        if usdt_balance < amount_wei:
            logger.error(f"Insufficient USDT balance. Has {usdt_balance_readable}, need {amount_usdt}")
            return None
        
        # For this custom implementation, we still need some ETH for actual gas
        # but the "fee" in the system is the 10 USDT, not the ETH gas cost
        eth_balance = web3.eth.get_balance(sender_address)
        eth_balance_readable = web3.from_wei(eth_balance, 'ether')
        logger.info(f"ETH balance for gas: {eth_balance_readable} ETH")
        
        # Estimate minimal ETH needed for gas
        gas_price = web3.eth.gas_price
        estimated_gas = 100000  # Conservative estimate for USDT transfer
        min_eth_needed = gas_price * estimated_gas
        
        if eth_balance < min_eth_needed:
            min_eth_readable = web3.from_wei(min_eth_needed, 'ether')
            logger.error(f"Insufficient ETH for gas. Has {eth_balance_readable}, need at least {min_eth_readable}")
            return None
        
        # Build transaction
        nonce = web3.eth.get_transaction_count(sender_address)
        
        # Build the transaction
        transaction = usdt_contract.functions.transfer(recipient_address, amount_wei).build_transaction({
            'from': sender_address,
            'nonce': nonce,
            'gas': estimated_gas,
            'gasPrice': gas_price,
            'chainId': 1  # Ethereum mainnet
        })
        
        logger.info(f"Transaction built - Gas: {estimated_gas}, Gas Price: {web3.from_wei(gas_price, 'gwei')} Gwei")
        
        # Sign the transaction
        signed_txn = web3.eth.account.sign_transaction(transaction, sender_private_key)
        
        # Send the transaction
        tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
        tx_hash_hex = web3.to_hex(tx_hash)
        
        logger.info(f"✅ USDT transaction sent! Hash: {tx_hash_hex}")
        logger.info(f"🔗 View on Etherscan: https://etherscan.io/tx/{tx_hash_hex}")
        logger.info(f"📊 Amount sent: {amount_usdt} USDT")
        logger.info(f"💰 System fee: 10 USDT (handled by admin system)")
        
        return tx_hash_hex
        
    except Exception as e:
        logger.error(f"❌ Error sending USDT on Ethereum: {str(e)}")
        return None

def send_transaction(sender_private_key, recipient_address, amount, sender_address, trade_details):
    """
    Simplified interface for admin panel compatibility
    
    Args:
        sender_private_key (str): Private key of sender
        recipient_address (str): Recipient address
        amount (float): Amount to send
        sender_address (str): Sender address (for logging)
        trade_details (dict): Trade details (for compatibility)
    
    Returns:
        str: Transaction hash if successful, "Failed" if not
    """
    try:
        logger.info(f"=== USDT ETHEREUM TRANSACTION ===")
        logger.info(f"From: {sender_address}")
        logger.info(f"To: {recipient_address}")
        logger.info(f"Amount: {amount} USDT")
        
        tx_hash = send_usdt_ethereum_transaction(
            sender_private_key=sender_private_key,
            recipient_address=recipient_address,
            amount_usdt=amount,
            log_file=sender_address
        )
        
        if tx_hash:
            logger.info(f"✅ Transaction successful: {tx_hash}")
            return tx_hash
        else:
            logger.error("❌ Transaction failed")
            return "Failed"
            
    except Exception as e:
        logger.error(f"❌ Error in send_transaction: {str(e)}")
        return "Failed"

# Test function
if __name__ == "__main__":
    # This is for testing only - do not use in production
    print("USDT Ethereum sender module loaded successfully") 