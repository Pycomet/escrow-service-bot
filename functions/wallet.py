from config import *
from database import *
from typing import Optional, List, Dict, Any
from functions.utils import generate_id
import logging
from datetime import datetime
import asyncio
from cryptography.fernet import Fernet
import os
import base64

# Web3 imports - we'll make these optional for now
try:
    from web3 import Web3
    from mnemonic import Mnemonic
    from eth_account import Account
    import hashlib
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False
    logger.warning("Web3 libraries not available. Install web3, mnemonic, and eth-account for full functionality.")

logger = logging.getLogger(__name__)

class WalletManager:
    """Handles multi-currency wallet operations for users"""
    
    # Default coins that every wallet should have
    DEFAULT_COINS = ['BTC', 'LTC', 'DOGE', 'ETH', 'SOL', 'USDT']
    
    # Supported coins and their configurations
    SUPPORTED_COINS = {
        'BTC': {
            'name': 'Bitcoin',
            'symbol': 'BTC',
            'decimals': 8,
            'network': 'bitcoin',
            'network_type': 'bitcoin',
            'is_token': False
        },
        'LTC': {
            'name': 'Litecoin',
            'symbol': 'LTC',
            'decimals': 8,
            'network': 'litecoin',
            'network_type': 'litecoin',
            'is_token': False
        },
        'DOGE': {
            'name': 'Dogecoin',
            'symbol': 'DOGE',
            'decimals': 8,
            'network': 'dogecoin',
            'network_type': 'dogecoin',
            'is_token': False
        },
        'ETH': {
            'name': 'Ethereum',
            'symbol': 'ETH',
            'decimals': 18,
            'network': 'ethereum',
            'network_type': 'ethereum',
            'rpc_url': os.getenv('ETH_RPC_URL', 'https://mainnet.infura.io/v3/YOUR_INFURA_KEY'),
            'is_token': False
        },
        'SOL': {
            'name': 'Solana',
            'symbol': 'SOL',
            'decimals': 9,
            'network': 'solana',
            'network_type': 'solana',
            'rpc_url': os.getenv('SOL_RPC_URL', 'https://api.mainnet-beta.solana.com'),
            'is_token': False
        },
        'USDT': {
            'name': 'Tether USD',
            'symbol': 'USDT',
            'decimals': 6,
            'network': 'ethereum',
            'network_type': 'ethereum',
            'contract_address': '0xdAC17F958D2ee523a2206206994597C13D831ec7',
            'is_token': True,
            'parent_coin': 'ETH'
        },
        'BNB': {
            'name': 'Binance Coin',
            'symbol': 'BNB',
            'decimals': 18,
            'network': 'ethereum',
            'network_type': 'ethereum',
            'contract_address': '0xB8c77482e45F1F44dE1745F52C74426C631bDD52',
            'is_token': True,
            'parent_coin': 'ETH'
        },
        'TRX': {
            'name': 'TRON',
            'symbol': 'TRX',
            'decimals': 6,
            'network': 'ethereum',
            'network_type': 'ethereum',
            'contract_address': '0xE17f017475a709De58E976081eB916081ff4c9d5',
            'is_token': True,
            'parent_coin': 'ETH'
        }
    }

    def __init__(self):
        """Initialize wallet manager with encryption key"""
        self.encryption_key = self._get_or_create_encryption_key()
        self.fernet = Fernet(self.encryption_key)
        
        # Initialize Web3 connections if available
        self.web3_connections = {}
        if WEB3_AVAILABLE:
            self._initialize_web3_connections()

    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for wallet data"""
        key_env = os.getenv('WALLET_ENCRYPTION_KEY')
        if key_env:
            try:
                return base64.urlsafe_b64decode(key_env)
            except Exception as e:
                logger.warning(f"Invalid encryption key in environment: {e}")
        
        # Generate new key - In production, this should be securely stored
        key = Fernet.generate_key()
        logger.warning(f"Generated new encryption key. Store this securely: {base64.urlsafe_b64encode(key).decode()}")
        return key

    def _initialize_web3_connections(self):
        """Initialize Web3 connections for supported networks"""
        try:
            # Ethereum connection
            eth_config = self.SUPPORTED_COINS['ETH']
            if eth_config.get('rpc_url') and 'YOUR_INFURA_KEY' not in eth_config['rpc_url']:
                self.web3_connections['ethereum'] = Web3(Web3.HTTPProvider(eth_config['rpc_url']))
                
        except Exception as e:
            logger.error(f"Error initializing Web3 connections: {e}")

    def _encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        return self.fernet.encrypt(data.encode()).decode()

    def _decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        return self.fernet.decrypt(encrypted_data.encode()).decode()

    @staticmethod
    def create_wallet_for_user(user_id: str, wallet_name: str = "My Wallet") -> Optional[WalletType]:
        """Create a new multi-currency wallet for a user"""
        try:
            # Check if user already has a wallet
            existing_wallet = WalletManager.get_user_wallet(user_id)
            if existing_wallet:
                logger.warning(f"User {user_id} already has a wallet")
                return existing_wallet

            wallet_manager = WalletManager()
            
            # Generate master mnemonic for the wallet
            if WEB3_AVAILABLE:
                mnemo = Mnemonic("english")
                master_mnemonic = mnemo.generate(strength=128)
            else:
                # Fallback to simple random generation for testing
                master_mnemonic = "test abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
            
            # Create wallet record
            wallet: WalletType = {
                "_id": generate_id(),
                "user_id": user_id,
                "wallet_name": wallet_name,
                "mnemonic_encrypted": wallet_manager._encrypt_data(master_mnemonic),
                "is_active": True,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }

            # Save wallet to database
            wallet_result = db.wallets.insert_one(wallet)
            if not wallet_result.inserted_id:
                logger.error(f"Failed to save wallet to database for user {user_id}")
                return None

            # Create default coin addresses for the wallet
            coin_addresses = []
            for coin_symbol in WalletManager.DEFAULT_COINS:
                coin_address = wallet_manager._create_coin_address(wallet["_id"], coin_symbol, master_mnemonic)
                if coin_address:
                    coin_addresses.append(coin_address)

            # Save all coin addresses
            if coin_addresses:
                db.coin_addresses.insert_many(coin_addresses)
                logger.info(f"Created wallet {wallet['_id']} with {len(coin_addresses)} coin addresses for user {user_id}")
            
            return wallet

        except Exception as e:
            logger.error(f"Error creating wallet for user {user_id}: {e}")
            return None

    def _create_coin_address(self, wallet_id: str, coin_symbol: str, master_mnemonic: str) -> Optional[CoinAddressType]:
        """Create a coin address within a wallet"""
        try:
            coin_config = self.SUPPORTED_COINS.get(coin_symbol)
            if not coin_config:
                logger.error(f"Unsupported coin: {coin_symbol}")
                return None

            # Generate address based on coin type
            if coin_config['network_type'] in ['bitcoin', 'litecoin', 'dogecoin']:
                address_data = self._create_bitcoin_like_address(coin_symbol, master_mnemonic)
            elif coin_config['network_type'] == 'ethereum':
                address_data = self._create_ethereum_address(master_mnemonic)
            elif coin_config['network_type'] == 'solana':
                address_data = self._create_solana_address(master_mnemonic)
            else:
                logger.error(f"Unsupported network type: {coin_config['network_type']}")
                return None

            if not address_data:
                logger.error(f"Failed to create address data for {coin_symbol}")
                return None

            # Create coin address record
            coin_address: CoinAddressType = {
                "_id": generate_id(),
                "wallet_id": wallet_id,
                "coin_symbol": coin_symbol,
                "network": coin_config['network'],
                "address": address_data['address'],
                "private_key_encrypted": self._encrypt_data(address_data['private_key']),
                "derivation_path": address_data.get('derivation_path', ''),
                "is_default": coin_symbol in self.DEFAULT_COINS,
                "balance": "0",
                "balance_usd": "0.00",
                "last_balance_update": datetime.now().isoformat(),
                "created_at": datetime.now().isoformat()
            }

            return coin_address

        except Exception as e:
            logger.error(f"Error creating coin address for {coin_symbol}: {e}")
            return None

    def _create_bitcoin_like_address(self, coin_symbol: str, master_mnemonic: str) -> Optional[Dict[str, str]]:
        """Create Bitcoin-like address (BTC, LTC, DOGE)"""
        try:
            if WEB3_AVAILABLE:
                # Generate seed from mnemonic
                mnemo = Mnemonic("english")
                seed = mnemo.to_seed(master_mnemonic)
                
                # Create derivation path based on coin
                if coin_symbol == 'BTC':
                    derivation_path = "m/44'/0'/0'/0/0"
                    private_key = hashlib.sha256(seed + coin_symbol.encode()).hexdigest()
                    # Simplified address generation for testing
                    address = f"1{private_key[:33]}"
                elif coin_symbol == 'LTC':
                    derivation_path = "m/44'/2'/0'/0/0"
                    private_key = hashlib.sha256(seed + coin_symbol.encode()).hexdigest()
                    address = f"L{private_key[:33]}"
                elif coin_symbol == 'DOGE':
                    derivation_path = "m/44'/3'/0'/0/0"
                    private_key = hashlib.sha256(seed + coin_symbol.encode()).hexdigest()
                    address = f"D{private_key[:33]}"
                else:
                    return None
            else:
                # Fallback for testing without web3
                derivation_path = f"m/44'/0'/0'/0/0"
                private_key = f"test_{coin_symbol}_{generate_id()[:10]}"
                address = f"{coin_symbol[0]}{generate_id()[:33]}"

            return {
                'address': address,
                'private_key': private_key,
                'derivation_path': derivation_path
            }

        except Exception as e:
            logger.error(f"Error creating {coin_symbol} address: {e}")
            return None

    def _create_ethereum_address(self, master_mnemonic: str) -> Optional[Dict[str, str]]:
        """Create Ethereum address (also used for ERC-20 tokens)"""
        try:
            if WEB3_AVAILABLE:
                # Generate account from mnemonic
                Account.enable_unaudited_hdwallet_features()
                account = Account.from_mnemonic(master_mnemonic, account_path="m/44'/60'/0'/0/0")
                
                return {
                    'address': account.address,
                    'private_key': account.key.hex(),
                    'derivation_path': "m/44'/60'/0'/0/0"
                }
            else:
                # Fallback for testing
                return {
                    'address': f"0x{generate_id()[:40]}",
                    'private_key': f"0x{generate_id()[:64]}",
                    'derivation_path': "m/44'/60'/0'/0/0"
                }

        except Exception as e:
            logger.error(f"Error creating Ethereum address: {e}")
            return None

    def _create_solana_address(self, master_mnemonic: str) -> Optional[Dict[str, str]]:
        """Create Solana address"""
        try:
            # Fallback implementation for testing
            return {
                'address': f"{generate_id()[:44]}",
                'private_key': f"{generate_id()[:64]}",
                'derivation_path': "m/44'/501'/0'/0'"
            }

        except Exception as e:
            logger.error(f"Error creating Solana address: {e}")
            return None

    @staticmethod
    def get_user_wallet(user_id: str) -> Optional[WalletType]:
        """Get user's wallet"""
        try:
            wallet = db.wallets.find_one({"user_id": user_id, "is_active": True})
            return wallet

        except Exception as e:
            logger.error(f"Error getting wallet for user {user_id}: {e}")
            return None

    @staticmethod
    def get_wallet_coin_addresses(wallet_id: str) -> List[CoinAddressType]:
        """Get all coin addresses for a wallet"""
        try:
            addresses_cursor = db.coin_addresses.find({
                "wallet_id": wallet_id
            }).sort([("is_default", -1), ("coin_symbol", 1)])
            
            return list(addresses_cursor)

        except Exception as e:
            logger.error(f"Error getting coin addresses for wallet {wallet_id}: {e}")
            return []

    @staticmethod
    def get_wallet_coin_address(wallet_id: str, coin_symbol: str) -> Optional[CoinAddressType]:
        """Get specific coin address from wallet"""
        try:
            address = db.coin_addresses.find_one({
                "wallet_id": wallet_id,
                "coin_symbol": coin_symbol
            })
            return address

        except Exception as e:
            logger.error(f"Error getting {coin_symbol} address for wallet {wallet_id}: {e}")
            return None

    def get_balance(self, address: str, coin_symbol: str) -> float:
        """Get current balance for a specific address and coin"""
        try:
            # Find the coin address record
            coin_address = db.coin_addresses.find_one({
                "address": address,
                "coin_symbol": coin_symbol
            })
            
            if not coin_address:
                logger.warning(f"No coin address record found for {address} ({coin_symbol})")
                return 0.0
            
            # Use the refresh paradigm to get fresh balance data
            import asyncio
            
            # Create event loop if none exists (for synchronous calls)
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                if not asyncio.get_running_loop():
                    asyncio.set_event_loop(loop)
            
            # Refresh the balance using the existing paradigm
            refresh_success = loop.run_until_complete(self._refresh_coin_balance(coin_address))
            
            if refresh_success:
                # Get the updated balance from database after refresh
                updated_coin_address = db.coin_addresses.find_one({
                    "address": address,
                    "coin_symbol": coin_symbol
                })
                
                if updated_coin_address:
                    balance_str = updated_coin_address.get('balance', '0.0')
                    try:
                        balance = float(balance_str)
                        logger.info(f"Refreshed and retrieved balance for {address} ({coin_symbol}): {balance}")
                        return balance
                    except ValueError:
                        logger.error(f"Invalid balance format after refresh: {balance_str}")
                        return 0.0
                else:
                    logger.error(f"Could not find updated coin address after refresh")
                    return 0.0
            else:
                logger.error(f"Failed to refresh balance for {address} ({coin_symbol})")
                # Fallback to stored balance if refresh fails
                balance_str = coin_address.get('balance', '0.0')
                try:
                    balance = float(balance_str)
                    logger.warning(f"Using stale balance for {address} ({coin_symbol}): {balance}")
                    return balance
                except ValueError:
                    logger.error(f"Invalid balance format in database: {balance_str}")
                    return 0.0
                
        except Exception as e:
            logger.error(f"Error getting balance for {address} ({coin_symbol}): {e}")
            return 0.0

    async def refresh_wallet_balances(self, wallet_id: str) -> bool:
        """Refresh all coin balances in a wallet"""
        try:
            coin_addresses = self.get_wallet_coin_addresses(wallet_id)
            
            success_count = 0
            for coin_address in coin_addresses:
                if await self._refresh_coin_balance(coin_address):
                    success_count += 1
            
            # Return True if at least half of the balances were updated successfully
            return success_count >= len(coin_addresses) // 2

        except Exception as e:
            logger.error(f"Error refreshing wallet balances for {wallet_id}: {e}")
            return False

    async def _refresh_coin_balance(self, coin_address: CoinAddressType) -> bool:
        """Refresh balance for a specific coin address"""
        try:
            coin_symbol = coin_address['coin_symbol']
            address = coin_address['address']
            coin_config = self.SUPPORTED_COINS.get(coin_symbol)
            
            if not coin_config:
                return False

            # Use real blockchain APIs instead of simulation
            balance = 0.0
            
            try:
                if coin_symbol == 'SOL':
                    # Use Solana balance checker
                    from functions.scripts.solwalletbalance import get_finalized_sol_balance
                    result = get_finalized_sol_balance(address)
                    if result and len(result) > 0 and 'amount' in result[0]:
                        balance = float(result[0]['amount'])
                
                elif coin_symbol == 'USDT' and coin_config.get('network') == 'solana':
                    # USDT on Solana
                    from functions.scripts.solwalletbalance import get_finalized_sol_balance, USDT_MINT_ADDRESS
                    result = get_finalized_sol_balance(address, USDT_MINT_ADDRESS)
                    if result and len(result) > 0 and 'amount' in result[0]:
                        balance = float(result[0]['amount'])
                
                elif coin_symbol in ['ETH'] or (coin_symbol == 'USDT' and coin_config.get('network') == 'ethereum'):
                    # Ethereum mainnet balance checker
                    from web3 import Web3
                    
                    # Use public Ethereum RPC endpoints (you can replace with your own)
                    ETH_RPC_URLS = [
                        "https://eth-mainnet.g.alchemy.com/v2/demo",  # Alchemy demo
                        "https://cloudflare-eth.com",  # Cloudflare
                        "https://rpc.ankr.com/eth"  # Ankr
                    ]
                    
                    # Try multiple RPC endpoints for reliability
                    web3 = None
                    for rpc_url in ETH_RPC_URLS:
                        try:
                            web3 = Web3(Web3.HTTPProvider(rpc_url))
                            if web3.is_connected():
                                break
                        except Exception as rpc_error:
                            logger.warning(f"Failed to connect to {rpc_url}: {rpc_error}")
                            continue
                    
                    if not web3 or not web3.is_connected():
                        logger.error("Could not connect to any Ethereum RPC")
                        balance = 0.0
                    else:
                        if coin_symbol == 'ETH':
                            # ETH balance
                            balance_wei = web3.eth.get_balance(Web3.to_checksum_address(address))
                            balance = float(web3.from_wei(balance_wei, 'ether'))
                        
                        elif coin_symbol == 'USDT':
                            # USDT on Ethereum (correct contract address)
                            ETHEREUM_USDT_CONTRACT = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
                            
                            # ERC-20 ABI for balanceOf function
                            ERC20_ABI = [
                                {
                                    "constant": True,
                                    "inputs": [{"name": "_owner", "type": "address"}],
                                    "name": "balanceOf",
                                    "outputs": [{"name": "balance", "type": "uint256"}],
                                    "payable": False,
                                    "stateMutability": "view",
                                    "type": "function",
                                },
                                {
                                    "constant": True,
                                    "inputs": [],
                                    "name": "decimals",
                                    "outputs": [{"name": "", "type": "uint8"}],
                                    "payable": False,
                                    "stateMutability": "view",
                                    "type": "function",
                                }
                            ]
                            
                            contract = web3.eth.contract(
                                address=Web3.to_checksum_address(ETHEREUM_USDT_CONTRACT), 
                                abi=ERC20_ABI
                            )
                            
                            try:
                                # Get USDT balance (USDT has 6 decimals)
                                balance_raw = contract.functions.balanceOf(Web3.to_checksum_address(address)).call()
                                balance = balance_raw / (10 ** 6)  # USDT has 6 decimals
                            except Exception as contract_error:
                                logger.error(f"Error calling USDT contract: {contract_error}")
                                balance = 0.0
                
                elif coin_symbol == 'BNB':
                    # BNB on BSC - use existing BSC script
                    from functions.scripts.bsc_wallet_balance import get_finalized_bsc_balance
                    result = get_finalized_bsc_balance(address)
                    if result and len(result) > 0 and 'amount' in result[0]:
                        balance = float(result[0]['amount'])
                
                elif coin_symbol == 'DOGE':
                    # Dogecoin balance checker
                    from functions.scripts.doge_transaction_checker import dogeTransactionChecker
                    result = dogeTransactionChecker(address)
                    if result and len(result) > 0 and 'amount' in result[0]:
                        balance = float(result[0]['amount'])
                
                elif coin_symbol == 'LTC':
                    # Litecoin balance checker
                    from functions.scripts.ltc_transaction_checker import ltcTransactionChecker
                    result = ltcTransactionChecker(address)
                    if result and len(result) > 0 and 'amount' in result[0]:
                        balance = float(result[0]['amount'])
                
                elif coin_symbol == 'BTC':
                    # Bitcoin balance checker - using similar API to LTC/DOGE
                    import requests
                    url = f"https://api.blockcypher.com/v1/btc/main/addrs/{address}/balance"
                    response = requests.get(url)
                    if response.status_code == 200:
                        data = response.json()
                        balance_satoshi = data.get('balance', 0)
                        balance = balance_satoshi / 1e8  # Convert satoshi to BTC
                
                else:
                    logger.warning(f"No balance checker implemented for {coin_symbol}, using fallback")
                    # Fallback to simulate some balance for testing
                    if coin_symbol == 'BTC':
                        balance = 0.001
                    elif coin_symbol == 'ETH':
                        balance = 0.1
                    elif coin_symbol == 'USDT':
                        balance = 100.0
                
                logger.info(f"Retrieved balance for {coin_symbol} address {address}: {balance}")
                
            except Exception as api_error:
                logger.error(f"Error calling blockchain API for {coin_symbol}: {api_error}")
                # Fallback to current stored balance on API error
                current_balance = coin_address.get('balance', '0')
                try:
                    balance = float(current_balance)
                except ValueError:
                    balance = 0.0
            
            # Update balance in database
            db.coin_addresses.update_one(
                {"_id": coin_address["_id"]},
                {
                    "$set": {
                        "balance": str(balance),
                        "last_balance_update": datetime.now().isoformat()
                    }
                }
            )
            return True

        except Exception as e:
            logger.error(f"Error refreshing balance for coin {coin_address.get('coin_symbol', 'unknown')}: {e}")
            return False

    @staticmethod
    def add_coin_to_wallet(wallet_id: str, coin_symbol: str) -> bool:
        """Add a new coin address to existing wallet"""
        try:
            # Check if coin already exists in wallet
            existing_address = WalletManager.get_wallet_coin_address(wallet_id, coin_symbol)
            if existing_address:
                logger.warning(f"Coin {coin_symbol} already exists in wallet {wallet_id}")
                return True

            # Get wallet to access master mnemonic
            wallet = db.wallets.find_one({"_id": wallet_id})
            if not wallet:
                logger.error(f"Wallet {wallet_id} not found")
                return False

            # Check if coin is supported
            wallet_manager = WalletManager()
            if coin_symbol not in wallet_manager.SUPPORTED_COINS:
                logger.error(f"Coin {coin_symbol} is not supported")
                return False

            master_mnemonic = wallet_manager._decrypt_data(wallet['mnemonic_encrypted'])
            
            # Create new coin address
            coin_address = wallet_manager._create_coin_address(wallet_id, coin_symbol, master_mnemonic)
            if coin_address:
                db.coin_addresses.insert_one(coin_address)
                logger.info(f"Added {coin_symbol} address to wallet {wallet_id}")
                return True
            else:
                logger.error(f"Failed to create {coin_symbol} address for wallet {wallet_id}")
                return False

        except Exception as e:
            logger.error(f"Error adding coin {coin_symbol} to wallet {wallet_id}: {e}")
            return False

    @staticmethod
    def get_supported_coins() -> List[str]:
        """Get list of all supported coins"""
        return list(WalletManager.SUPPORTED_COINS.keys())

    @staticmethod
    def get_default_coins() -> List[str]:
        """Get list of default coins for new wallets"""
        return WalletManager.DEFAULT_COINS.copy()

    @staticmethod
    def deactivate_wallet(wallet_id: str) -> bool:
        """Deactivate a wallet"""
        try:
            result = db.wallets.update_one(
                {"_id": wallet_id},
                {
                    "$set": {
                        "is_active": False,
                        "updated_at": datetime.now().isoformat()
                    }
                }
            )
            return result.modified_count > 0

        except Exception as e:
            logger.error(f"Error deactivating wallet {wallet_id}: {e}")
            return False 