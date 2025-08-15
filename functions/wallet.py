import asyncio
import base64
import logging
import os
import secrets
from datetime import datetime
from typing import Any, Dict, List, Optional

import base58
from cryptography.fernet import Fernet

from config import *
from database import *
from functions.utils import generate_id

# Import handler functions for testing compatibility
try:
    from handlers.wallet import send_message_or_edit
except ImportError:
    # Define a placeholder for testing if import fails
    async def send_message_or_edit(
        message, text, reply_markup, is_callback=False, parse_mode=None
    ):
        """Placeholder function for testing"""
        pass


# Web3 imports - we'll make these optional for now
try:
    import hashlib

    from eth_account import Account
    from mnemonic import Mnemonic
    from web3 import Web3

    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False
    logger.warning(
        "Web3 libraries not available. Install web3, mnemonic, and eth-account for full functionality."
    )

logger = logging.getLogger(__name__)


class WalletManager:
    """
    Handles multi-currency wallet operations for users.

    This class provides comprehensive wallet functionality including:
    - HD wallet generation with encrypted storage
    - Multi-currency address management (BTC, ETH, LTC, DOGE, SOL, USDT, etc.)
    - Real-time balance checking via blockchain APIs
    - Secure private key encryption/decryption
    - Cryptocurrency transfer operations
    """

    # Default coins that every wallet should have
    DEFAULT_COINS = ["BTC", "LTC", "DOGE", "ETH", "SOL", "USDT"]

    # Supported coins and their configurations
    SUPPORTED_COINS = {
        "BTC": {
            "name": "Bitcoin",
            "symbol": "BTC",
            "decimals": 8,
            "network": "bitcoin",
            "network_type": "bitcoin",
            "is_token": False,
        },
        "LTC": {
            "name": "Litecoin",
            "symbol": "LTC",
            "decimals": 8,
            "network": "litecoin",
            "network_type": "litecoin",
            "is_token": False,
        },
        "DOGE": {
            "name": "Dogecoin",
            "symbol": "DOGE",
            "decimals": 8,
            "network": "dogecoin",
            "network_type": "dogecoin",
            "is_token": False,
        },
        "ETH": {
            "name": "Ethereum",
            "symbol": "ETH",
            "decimals": 18,
            "network": "ethereum",
            "network_type": "ethereum",
            "rpc_url": os.getenv(
                "ETH_RPC_URL",
                "https://mainnet.infura.io/v3/104abeafa90045c490605995b21684c1",
            ),
            "is_token": False,
        },
        "SOL": {
            "name": "Solana",
            "symbol": "SOL",
            "decimals": 9,
            "network": "solana",
            "network_type": "solana",
            "rpc_url": os.getenv("SOL_RPC_URL", "https://api.mainnet-beta.solana.com"),
            "is_token": False,
        },
        "USDT": {
            "name": "Tether USD",
            "symbol": "USDT",
            "decimals": 6,
            "network": "ethereum",
            "network_type": "ethereum",
            "contract_address": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
            "is_token": True,
            "parent_coin": "ETH",
        },
        "BNB": {
            "name": "Binance Coin",
            "symbol": "BNB",
            "decimals": 18,
            "network": "ethereum",
            "network_type": "ethereum",
            "contract_address": "0xB8c77482e45F1F44dE1745F52C74426C631bDD52",
            "is_token": True,
            "parent_coin": "ETH",
        },
        "TRX": {
            "name": "TRON",
            "symbol": "TRX",
            "decimals": 6,
            "network": "ethereum",
            "network_type": "ethereum",
            "contract_address": "0xE17f017475a709De58E976081eB916081ff4c9d5",
            "is_token": True,
            "parent_coin": "ETH",
        },
    }

    def __init__(self):
        """Initialize wallet manager with encryption key"""
        self.encryption_key = self._get_or_create_encryption_key()
        self.fernet = Fernet(self.encryption_key)

    def _get_or_create_encryption_key(self) -> bytes:
        """Return the application-wide encryption key.

        Production rule: the key **must** come from the environment variable
        WALLET_ENCRYPTION_KEY (base64-url-safe encoded, 32-byte value).
        If the key is absent *and* the application is running in DEBUG mode,
        a throw-away key will be generated so that local developers can still
        use the wallet subsystem. In non-DEBUG mode missing/invalid keys raise
        a hard exception so the container crashes fast instead of silently
        generating a new, unrecoverable key.
        """

        key_env = os.getenv("WALLET_ENCRYPTION_KEY")

        if key_env:
            try:
                return base64.urlsafe_b64decode(key_env)
            except Exception as exc:
                logger.error("WALLET_ENCRYPTION_KEY is invalid base64: %s", exc)
                # fall through to error handling below

        # At this point the key is missing or invalid.
        if DEBUG:
            # Developer convenience – generate a temporary key but warn loudly.
            temp_key = Fernet.generate_key()
            logger.warning(
                "DEBUG mode is active and WALLET_ENCRYPTION_KEY was missing or invalid. "
                "Generated a temporary key (THIS WILL LOSE ACCESS TO FUNDS if used in production). "
                "%s - This is a test key and will be replaced with a production key in the future.",
                temp_key.decode() if isinstance(temp_key, bytes) else temp_key,
            )
            return temp_key

        # Production – abort startup.
        raise RuntimeError(
            "WALLET_ENCRYPTION_KEY environment variable is required in production "
            "and must contain a 32-byte url-safe base64-encoded key."
        )

    def _encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        return self.fernet.encrypt(data.encode()).decode()

    def _decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        return self.fernet.decrypt(encrypted_data.encode()).decode()

    @staticmethod
    def create_wallet_for_user(
        user_id: str, wallet_name: str = "My Wallet"
    ) -> Optional[WalletType]:
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
                "updated_at": datetime.now().isoformat(),
            }

            # Save wallet to database
            wallet_result = db.wallets.insert_one(wallet)
            if not wallet_result.inserted_id:
                logger.error(f"Failed to save wallet to database for user {user_id}")
                return None

            # Create default coin addresses for the wallet
            coin_addresses = []
            for coin_symbol in WalletManager.DEFAULT_COINS:
                coin_address = wallet_manager._create_coin_address(
                    wallet["_id"], coin_symbol, master_mnemonic
                )
                if coin_address:
                    coin_addresses.append(coin_address)

            # Save all coin addresses
            if coin_addresses:
                db.coin_addresses.insert_many(coin_addresses)
                logger.info(
                    f"Created wallet {wallet['_id']} with {len(coin_addresses)} coin addresses for user {user_id}"
                )

            return wallet

        except Exception as e:
            logger.error(f"Error creating wallet for user {user_id}: {e}")
            return None

    def _create_coin_address(
        self, wallet_id: str, coin_symbol: str, master_mnemonic: str
    ) -> Optional[CoinAddressType]:
        """Create a coin address within a wallet"""
        try:
            coin_config = self.SUPPORTED_COINS.get(coin_symbol)
            if not coin_config:
                logger.error(f"Unsupported coin: {coin_symbol}")
                return None

            # Generate address based on coin type
            if coin_config["network_type"] in ["bitcoin", "litecoin", "dogecoin"]:
                address_data = self._create_bitcoin_like_address(
                    coin_symbol, master_mnemonic
                )
            elif coin_config["network_type"] == "ethereum":
                address_data = self._create_ethereum_address(master_mnemonic)
            elif coin_config["network_type"] == "solana":
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
                "network": coin_config["network"],
                "address": address_data["address"],
                "private_key_encrypted": self._encrypt_data(
                    address_data["private_key"]
                ),
                "derivation_path": address_data.get("derivation_path", ""),
                "is_default": coin_symbol in self.DEFAULT_COINS,
                "balance": "0",
                "balance_usd": "0.00",
                "last_balance_update": datetime.now().isoformat(),
                "created_at": datetime.now().isoformat(),
            }

            return coin_address

        except Exception as e:
            logger.error(f"Error creating coin address for {coin_symbol}: {e}")
            return None

    def _create_bitcoin_like_address(
        self, coin_symbol: str, master_mnemonic: str
    ) -> Optional[Dict[str, str]]:
        """Create Bitcoin-like address (BTC, LTC, DOGE)"""
        try:
            if WEB3_AVAILABLE:
                # Generate seed from mnemonic
                mnemo = Mnemonic("english")
                seed = mnemo.to_seed(master_mnemonic)

                # Create derivation path based on coin
                if coin_symbol == "BTC":
                    derivation_path = "m/44'/0'/0'/0/0"
                    private_key = hashlib.sha256(
                        seed + coin_symbol.encode()
                    ).hexdigest()
                    # Simplified address generation for testing
                    address = f"1{private_key[:33]}"
                elif coin_symbol == "LTC":
                    derivation_path = "m/44'/2'/0'/0/0"
                    private_key = hashlib.sha256(
                        seed + coin_symbol.encode()
                    ).hexdigest()
                    address = f"L{private_key[:33]}"
                elif coin_symbol == "DOGE":
                    derivation_path = "m/44'/3'/0'/0/0"
                    private_key = hashlib.sha256(
                        seed + coin_symbol.encode()
                    ).hexdigest()
                    address = f"D{private_key[:33]}"
                else:
                    return None
            else:
                # Fallback for testing without web3
                derivation_path = f"m/44'/0'/0'/0/0"
                private_key = f"test_{coin_symbol}_{generate_id()[:10]}"
                address = f"{coin_symbol[0]}{generate_id()[:33]}"

            return {
                "address": address,
                "private_key": private_key,
                "derivation_path": derivation_path,
            }

        except Exception as e:
            logger.error(f"Error creating {coin_symbol} address: {e}")
            return None

    def _create_ethereum_address(
        self, master_mnemonic: str
    ) -> Optional[Dict[str, str]]:
        """Create Ethereum address (also used for ERC-20 tokens)"""
        try:
            if WEB3_AVAILABLE:
                # Generate account from mnemonic
                Account.enable_unaudited_hdwallet_features()
                account = Account.from_mnemonic(
                    master_mnemonic, account_path="m/44'/60'/0'/0/0"
                )

                return {
                    "address": account.address,
                    "private_key": account.key.hex(),
                    "derivation_path": "m/44'/60'/0'/0/0",
                }
            else:
                # Fallback for testing
                return {
                    "address": f"0x{generate_id()[:40]}",
                    "private_key": f"0x{generate_id()[:64]}",
                    "derivation_path": "m/44'/60'/0'/0/0",
                }

        except Exception as e:
            logger.error(f"Error creating Ethereum address: {e}")
            return None

    def _create_solana_address(self, master_mnemonic: str) -> Optional[Dict[str, str]]:
        """Create Solana address"""
        try:
            # Create a valid Solana address format for testing/development
            # This is a placeholder - in production you'd use proper Solana keypair generation

            # Generate a 32-byte private key and derive a valid public key format
            private_key_bytes = secrets.token_bytes(32)

            # Create a valid base58-encoded address (44 characters like real Solana addresses)
            # Using the first 32 bytes as the public key bytes
            public_key_bytes = private_key_bytes  # Simplified for demo
            address = base58.b58encode(public_key_bytes).decode("utf-8")

            return {
                "address": address,
                "private_key": base58.b58encode(private_key_bytes).decode("utf-8"),
                "derivation_path": "m/44'/501'/0'/0'",
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
            addresses_cursor = db.coin_addresses.find({"wallet_id": wallet_id}).sort(
                [("is_default", -1), ("coin_symbol", 1)]
            )

            return list(addresses_cursor)

        except Exception as e:
            logger.error(f"Error getting coin addresses for wallet {wallet_id}: {e}")
            return []

    @staticmethod
    def get_wallet_coin_address(
        wallet_id: str, coin_symbol: str
    ) -> Optional[CoinAddressType]:
        """Get specific coin address from wallet"""
        try:
            address = db.coin_addresses.find_one(
                {"wallet_id": wallet_id, "coin_symbol": coin_symbol}
            )
            return address

        except Exception as e:
            logger.error(
                f"Error getting {coin_symbol} address for wallet {wallet_id}: {e}"
            )
            return None

    def get_balance(self, address: str, coin_symbol: str) -> float:
        """Get current balance for a specific address and coin"""
        try:
            # Find the coin address record
            coin_address = db.coin_addresses.find_one(
                {"address": address, "coin_symbol": coin_symbol}
            )

            if not coin_address:
                logger.warning(
                    f"No coin address record found for {address} ({coin_symbol})"
                )
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
            refresh_success = loop.run_until_complete(
                self._refresh_coin_balance(coin_address)
            )

            if refresh_success:
                # Get the updated balance from database after refresh
                updated_coin_address = db.coin_addresses.find_one(
                    {"address": address, "coin_symbol": coin_symbol}
                )

                if updated_coin_address:
                    balance_str = updated_coin_address.get("balance", "0.0")
                    try:
                        balance = float(balance_str)
                        logger.info(
                            f"Refreshed and retrieved balance for {address} ({coin_symbol}): {balance}"
                        )
                        return balance
                    except ValueError:
                        logger.error(
                            f"Invalid balance format after refresh: {balance_str}"
                        )
                        return 0.0
                else:
                    logger.error(f"Could not find updated coin address after refresh")
                    return 0.0
            else:
                logger.error(f"Failed to refresh balance for {address} ({coin_symbol})")
                # Fallback to stored balance if refresh fails
                balance_str = coin_address.get("balance", "0.0")
                try:
                    balance = float(balance_str)
                    logger.warning(
                        f"Using stale balance for {address} ({coin_symbol}): {balance}"
                    )
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
            coin_symbol = coin_address["coin_symbol"]
            address = coin_address["address"]
            coin_config = self.SUPPORTED_COINS.get(coin_symbol)

            if not coin_config:
                return False

            # Use real blockchain APIs instead of simulation
            balance = 0.0

            try:
                if coin_symbol == "SOL":
                    # Use Solana balance checker
                    from functions.scripts.solwalletbalance import (
                        get_finalized_sol_balance,
                    )

                    result = get_finalized_sol_balance(address)
                    if result and len(result) > 0 and "amount" in result[0]:
                        balance = float(result[0]["amount"])

                elif coin_symbol == "USDT" and coin_config.get("network") == "solana":
                    # USDT on Solana
                    from functions.scripts.solwalletbalance import (
                        USDT_MINT_ADDRESS,
                        get_finalized_sol_balance,
                    )

                    result = get_finalized_sol_balance(address, USDT_MINT_ADDRESS)
                    if result and len(result) > 0 and "amount" in result[0]:
                        balance = float(result[0]["amount"])

                elif coin_symbol in ["ETH"] or (
                    coin_symbol == "USDT" and coin_config.get("network") == "ethereum"
                ):
                    # Ethereum mainnet balance checker
                    from web3 import Web3

                    # Determine the primary RPC URL from config, handling tokens
                    primary_rpc_url = None
                    if coin_config.get("is_token") and coin_config.get("parent_coin"):
                        parent_config = self.SUPPORTED_COINS.get(
                            coin_config["parent_coin"], {}
                        )
                        primary_rpc_url = parent_config.get("rpc_url")
                    else:
                        primary_rpc_url = coin_config.get("rpc_url")

                    # Public fallbacks
                    ETH_RPC_URLS = [
                        "https://eth-mainnet.g.alchemy.com/v2/demo",  # Alchemy demo
                        "https://cloudflare-eth.com",  # Cloudflare
                        "https://rpc.ankr.com/eth",  # Ankr
                    ]

                    # Create a list of RPCs to try, prioritizing the one from config
                    rpcs_to_try = []
                    if primary_rpc_url and "YOUR_INFURA_KEY" not in primary_rpc_url:
                        rpcs_to_try.append(primary_rpc_url)

                    rpcs_to_try.extend(ETH_RPC_URLS)

                    # Try multiple RPC endpoints for reliability
                    web3 = None
                    for rpc_url in rpcs_to_try:
                        try:
                            web3 = Web3(Web3.HTTPProvider(rpc_url))
                            if web3.is_connected():
                                logger.info(f"Connected to Ethereum RPC: {rpc_url}")
                                break
                        except Exception as rpc_error:
                            logger.warning(
                                f"Failed to connect to {rpc_url}: {rpc_error}"
                            )
                            web3 = None  # Ensure web3 is None if connection fails
                            continue

                    if not web3 or not web3.is_connected():
                        logger.error("Could not connect to any Ethereum RPC")
                        balance = 0.0
                    else:
                        if coin_symbol == "ETH":
                            # ETH balance
                            balance_wei = web3.eth.get_balance(
                                Web3.to_checksum_address(address)
                            )
                            balance = float(web3.from_wei(balance_wei, "ether"))

                        elif coin_symbol == "USDT":
                            # USDT on Ethereum (correct contract address)
                            ETHEREUM_USDT_CONTRACT = (
                                "0xdAC17F958D2ee523a2206206994597C13D831ec7"
                            )

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
                                },
                            ]

                            contract = web3.eth.contract(
                                address=Web3.to_checksum_address(
                                    ETHEREUM_USDT_CONTRACT
                                ),
                                abi=ERC20_ABI,
                            )

                            try:
                                # Get USDT balance (USDT has 6 decimals)
                                balance_raw = contract.functions.balanceOf(
                                    Web3.to_checksum_address(address)
                                ).call()
                                balance = balance_raw / (10**6)  # USDT has 6 decimals
                            except Exception as contract_error:
                                logger.error(
                                    f"Error calling USDT contract: {contract_error}"
                                )
                                balance = 0.0

                elif coin_symbol == "BNB":
                    # BNB on BSC - use existing BSC script
                    from functions.scripts.bsc_wallet_balance import (
                        get_finalized_bsc_balance,
                    )

                    result = get_finalized_bsc_balance(address)
                    if result and len(result) > 0 and "amount" in result[0]:
                        balance = float(result[0]["amount"])

                elif coin_symbol == "DOGE":
                    # Dogecoin balance checker
                    from functions.scripts.doge_transaction_checker import (
                        dogeTransactionChecker,
                    )

                    result = dogeTransactionChecker(address)
                    if result and len(result) > 0 and "amount" in result[0]:
                        balance = float(result[0]["amount"])

                elif coin_symbol == "LTC":
                    # Litecoin balance checker
                    from functions.scripts.ltc_transaction_checker import (
                        ltcTransactionChecker,
                    )

                    result = ltcTransactionChecker(address)
                    if result and len(result) > 0 and "amount" in result[0]:
                        balance = float(result[0]["amount"])

                elif coin_symbol == "BTC":
                    # Bitcoin balance checker - using similar API to LTC/DOGE
                    import requests

                    url = f"https://api.blockcypher.com/v1/btc/main/addrs/{address}/balance"
                    response = requests.get(url)
                    if response.status_code == 200:
                        data = response.json()
                        balance_satoshi = data.get("balance", 0)
                        balance = balance_satoshi / 1e8  # Convert satoshi to BTC

                else:
                    logger.warning(
                        f"No balance checker implemented for {coin_symbol}, using fallback"
                    )
                    # Fallback to simulate some balance for testing
                    if coin_symbol == "BTC":
                        balance = 0.001
                    elif coin_symbol == "ETH":
                        balance = 0.1
                    elif coin_symbol == "USDT":
                        balance = 100.0

                logger.info(
                    f"Retrieved balance for {coin_symbol} address {address}: {balance}"
                )

            except Exception as api_error:
                logger.error(
                    f"Error calling blockchain API for {coin_symbol}: {api_error}"
                )
                # Fallback to current stored balance on API error
                current_balance = coin_address.get("balance", "0")
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
                        "last_balance_update": datetime.now().isoformat(),
                    }
                },
            )
            return True

        except Exception as e:
            logger.error(
                f"Error refreshing balance for coin {coin_address.get('coin_symbol', 'unknown')}: {e}"
            )
            return False

    @staticmethod
    def add_coin_to_wallet(wallet_id: str, coin_symbol: str) -> bool:
        """Add a new coin address to existing wallet"""
        try:
            # Check if coin already exists in wallet
            existing_address = WalletManager.get_wallet_coin_address(
                wallet_id, coin_symbol
            )
            if existing_address:
                logger.warning(
                    f"Coin {coin_symbol} already exists in wallet {wallet_id}"
                )
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

            master_mnemonic = wallet_manager._decrypt_data(wallet["mnemonic_encrypted"])

            # Create new coin address
            coin_address = wallet_manager._create_coin_address(
                wallet_id, coin_symbol, master_mnemonic
            )
            if coin_address:
                db.coin_addresses.insert_one(coin_address)
                logger.info(f"Added {coin_symbol} address to wallet {wallet_id}")
                return True
            else:
                logger.error(
                    f"Failed to create {coin_symbol} address for wallet {wallet_id}"
                )
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
                        "updated_at": datetime.now().isoformat(),
                    }
                },
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error deactivating wallet {wallet_id}: {e}")
            return False

    @staticmethod
    def transfer_crypto(
        from_wallet_id: str,
        to_address: str,
        amount: float,
        currency: str,
        trade_id: str = None,
    ) -> bool:
        """Transfer crypto from wallet to external address

        Args:
            from_wallet_id: Source wallet ID
            to_address: Destination address
            amount: Amount to transfer
            currency: Currency symbol (ETH, USDT, etc.)
            trade_id: Associated trade ID for tracking

        Returns:
            bool: True if transfer successful, False otherwise
        """
        try:
            logger.info(
                f"Initiating crypto transfer: {amount} {currency} from wallet {from_wallet_id} to {to_address}"
            )

            # Get wallet information
            wallet = db.wallets.find_one({"_id": from_wallet_id})
            if not wallet:
                logger.error(f"Wallet {from_wallet_id} not found")
                return False

            # Get coin address for the currency
            coin_address = WalletManager.get_wallet_coin_address(
                from_wallet_id, currency
            )
            if not coin_address:
                logger.error(f"No {currency} address found for wallet {from_wallet_id}")
                return False

            # Check balance
            wallet_manager = WalletManager()
            current_balance = wallet_manager.get_balance(
                coin_address["address"], currency
            )
            if current_balance < amount:
                logger.error(
                    f"Insufficient balance: {current_balance} < {amount} {currency}"
                )
                return False

            # Get coin configuration
            coin_config = WalletManager.SUPPORTED_COINS.get(currency)
            if not coin_config:
                logger.error(f"Unsupported currency: {currency}")
                return False

            # Execute blockchain transfer
            if DEBUG:
                logger.warning(
                    f"DEBUG MODE: Simulating transfer of {amount} {currency} to {to_address}"
                )
                transfer_result = {
                    "success": True,
                    "tx_hash": f"simulated_tx_{generate_id()[:16]}",
                    "gas_used": 21000 if currency == "ETH" else 65000,
                    "gas_fee_eth": 0.001  # Simulated gas fee
                }
            else:
                # Execute actual blockchain transfer
                transfer_result = WalletManager._execute_blockchain_transfer(
                    coin_config, coin_address, to_address, amount, wallet_manager
                )

            if transfer_result.get("success", False):
                tx_hash = transfer_result.get("tx_hash")
                gas_used = transfer_result.get("gas_used", 0)
                gas_fee_eth = transfer_result.get("gas_fee_eth", 0.0)
                
                # Record transaction with gas fee information
                transaction_record = {
                    "_id": generate_id(),
                    "wallet_id": from_wallet_id,
                    "coin_symbol": currency,
                    "from_address": coin_address["address"],
                    "to_address": to_address,
                    "amount": amount,
                    "transaction_type": "outgoing",
                    "tx_hash": tx_hash,
                    "trade_id": trade_id,
                    "status": "completed",
                    "gas_used": gas_used,
                    "gas_fee_eth": gas_fee_eth,
                    "created_at": datetime.now().isoformat(),
                }

                db.wallet_transactions.insert_one(transaction_record)

                # Update coin address balance (subtract transferred amount and gas fees if ETH)
                new_balance = current_balance - amount
                if currency == "ETH":
                    # For ETH transfers, also subtract gas fees from ETH balance
                    new_balance -= gas_fee_eth
                elif gas_fee_eth > 0:
                    # For ERC-20 transfers, subtract gas fees from ETH balance in the same wallet
                    eth_address = WalletManager.get_wallet_coin_address(from_wallet_id, "ETH")
                    if eth_address:
                        eth_balance = wallet_manager.get_balance(eth_address["address"], "ETH")
                        new_eth_balance = max(0, eth_balance - gas_fee_eth)
                        db.coin_addresses.update_one(
                            {"_id": eth_address["_id"]},
                            {
                                "$set": {
                                    "balance": str(new_eth_balance),
                                    "updated_at": datetime.now().isoformat(),
                                }
                            },
                        )
                        logger.info(f"Deducted {gas_fee_eth} ETH gas fee from ETH balance")

                db.coin_addresses.update_one(
                    {"_id": coin_address["_id"]},
                    {
                        "$set": {
                            "balance": str(new_balance),
                            "updated_at": datetime.now().isoformat(),
                        }
                    },
                )

                logger.info(f"Transfer completed: {tx_hash}, Gas fee: {gas_fee_eth} ETH")
                return True
            else:
                logger.error(f"Blockchain transfer failed for {amount} {currency}")
                return False

        except Exception as e:
            logger.error(f"Error in crypto transfer: {e}")
            return False

    @staticmethod
    def _execute_blockchain_transfer(
        coin_config: dict,
        from_coin_address: dict,
        to_address: str,
        amount: float,
        wallet_manager,
    ) -> dict:
        """Execute actual blockchain transfer
        
        Returns:
            dict: {"success": bool, "tx_hash": str, "gas_used": int, "gas_fee_eth": float}
        """
        try:
            network_type = coin_config.get("network_type")

            if network_type == "ethereum":
                return WalletManager._execute_ethereum_transfer(
                    coin_config, from_coin_address, to_address, amount, wallet_manager
                )
            elif network_type == "bitcoin":
                # Bitcoin transfers not implemented yet
                logger.warning("Bitcoin transfers not yet implemented")
                return {"success": False, "tx_hash": None, "gas_used": 0, "gas_fee_eth": 0.0}
            elif network_type == "solana":
                # Solana transfers not implemented yet  
                logger.warning("Solana transfers not yet implemented")
                return {"success": False, "tx_hash": None, "gas_used": 0, "gas_fee_eth": 0.0}
            else:
                logger.error(f"Unsupported network type: {network_type}")
                return {"success": False, "tx_hash": None, "gas_used": 0, "gas_fee_eth": 0.0}

        except Exception as e:
            logger.error(f"Error executing blockchain transfer: {e}")
            return {"success": False, "tx_hash": None, "gas_used": 0, "gas_fee_eth": 0.0}

    @staticmethod
    def _execute_ethereum_transfer(
        coin_config: dict,
        from_coin_address: dict,
        to_address: str,
        amount: float,
        wallet_manager,
    ) -> dict:
        """Execute Ethereum/ERC-20 transfer
        
        Returns:
            dict: {"success": bool, "tx_hash": str, "gas_used": int, "gas_fee_eth": float}
        """
        try:
            if not WEB3_AVAILABLE:
                logger.error("Web3 libraries not available for Ethereum transfer")
                return {"success": False, "tx_hash": None, "gas_used": 0, "gas_fee_eth": 0.0}

            from web3 import Web3
            from eth_account import Account
            
            # Get Web3 connection
            web3 = WalletManager._get_web3_connection(coin_config)
            if not web3:
                logger.error("Failed to connect to Ethereum network")
                return {"success": False, "tx_hash": None, "gas_used": 0, "gas_fee_eth": 0.0}

            # Decrypt private key
            private_key = wallet_manager._decrypt_data(from_coin_address["private_key_encrypted"])
            if not private_key.startswith("0x"):
                private_key = "0x" + private_key
                
            from_address = from_coin_address["address"]
            
            # Validate addresses
            from_address = Web3.to_checksum_address(from_address)
            to_address = Web3.to_checksum_address(to_address)
            
            logger.info(f"Executing {coin_config['symbol']} transfer: {amount} from {from_address} to {to_address}")
            
            if coin_config.get("is_token", False):
                # ERC-20 token transfer (USDT, etc.)
                return WalletManager._execute_erc20_transfer(
                    web3, private_key, from_address, to_address, amount, coin_config
                )
            else:
                # Native ETH transfer
                return WalletManager._execute_eth_transfer(
                    web3, private_key, from_address, to_address, amount
                )

        except Exception as e:
            logger.error(f"Error in Ethereum transfer: {e}")
            return {"success": False, "tx_hash": None, "gas_used": 0, "gas_fee_eth": 0.0}

    @staticmethod
    def _execute_bitcoin_transfer(
        coin_config: dict,
        from_coin_address: dict,
        to_address: str,
        amount: float,
        wallet_manager,
    ) -> bool:
        """Execute Bitcoin transfer"""
        try:
            # TODO: Implement actual Bitcoin transfer
            logger.warning(
                "Bitcoin transfer not yet implemented - returning success for testing"
            )
            return True

        except Exception as e:
            logger.error(f"Error in Bitcoin transfer: {e}")
            return False

    @staticmethod
    def _execute_solana_transfer(
        coin_config: dict,
        from_coin_address: dict,
        to_address: str,
        amount: float,
        wallet_manager,
    ) -> bool:
        """Execute Solana transfer"""
        try:
            # TODO: Implement actual Solana transfer
            logger.warning(
                "Solana transfer not yet implemented - returning success for testing"
            )
            return True

        except Exception as e:
            logger.error(f"Error in Solana transfer: {e}")
            return False

    @staticmethod
    def _get_web3_connection(coin_config: dict):
        """Get a Web3 connection with fallback RPCs"""
        try:
            from web3 import Web3
            
            # Primary RPC from config
            primary_rpc_url = None
            if coin_config.get("is_token") and coin_config.get("parent_coin"):
                parent_config = WalletManager.SUPPORTED_COINS.get(coin_config["parent_coin"], {})
                primary_rpc_url = parent_config.get("rpc_url")
            else:
                primary_rpc_url = coin_config.get("rpc_url")
            
            # Fallback RPCs
            fallback_rpcs = [
                "https://eth.llamarpc.com",
                "https://rpc.ankr.com/eth",
                "https://ethereum.publicnode.com",
                "https://eth-mainnet.g.alchemy.com/v2/demo"
            ]
            
            # Build list of RPCs to try
            rpcs_to_try = []
            if primary_rpc_url and "YOUR_INFURA_KEY" not in primary_rpc_url:
                rpcs_to_try.append(primary_rpc_url)
            rpcs_to_try.extend(fallback_rpcs)
            
            # Try each RPC until one works
            for rpc_url in rpcs_to_try:
                try:
                    web3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 15}))
                    if web3.is_connected():
                        logger.info(f"Connected to Ethereum RPC: {rpc_url}")
                        return web3
                except Exception as rpc_error:
                    logger.warning(f"Failed to connect to {rpc_url}: {rpc_error}")
                    continue
            
            logger.error("Could not connect to any Ethereum RPC")
            return None
            
        except Exception as e:
            logger.error(f"Error getting Web3 connection: {e}")
            return None

    @staticmethod  
    def _execute_eth_transfer(web3, private_key: str, from_address: str, to_address: str, amount: float) -> dict:
        """Execute native ETH transfer"""
        try:
            from web3 import Web3
            from eth_account import Account
            
            # Convert amount to Wei
            amount_wei = web3.to_wei(amount, 'ether')
            
            # Get nonce
            nonce = web3.eth.get_transaction_count(from_address)
            
            # Get current gas price
            gas_price = web3.eth.gas_price
            
            # Build transaction
            transaction = {
                'to': to_address,
                'value': amount_wei,
                'gas': 21000,  # Standard ETH transfer gas limit
                'gasPrice': gas_price,
                'nonce': nonce,
                'chainId': web3.eth.chain_id
            }
            
            # Sign transaction
            signed_txn = web3.eth.account.sign_transaction(transaction, private_key)
            
            # Send transaction
            tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            tx_hash_hex = tx_hash.hex()
            
            logger.info(f"ETH transfer sent: {tx_hash_hex}")
            
            # Wait for transaction receipt (with timeout)
            try:
                receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                gas_used = receipt.gasUsed
                gas_fee_eth = float(web3.from_wei(gas_used * gas_price, 'ether'))
                
                if receipt.status == 1:
                    logger.info(f"ETH transfer confirmed: {tx_hash_hex}, Gas used: {gas_used}")
                    return {
                        "success": True,
                        "tx_hash": tx_hash_hex,
                        "gas_used": gas_used,
                        "gas_fee_eth": gas_fee_eth
                    }
                else:
                    logger.error(f"ETH transfer failed: {tx_hash_hex}")
                    return {"success": False, "tx_hash": tx_hash_hex, "gas_used": gas_used, "gas_fee_eth": gas_fee_eth}
                    
            except Exception as receipt_error:
                logger.warning(f"Could not get receipt for {tx_hash_hex}: {receipt_error}")
                # Transaction was sent, but we couldn't confirm
                gas_fee_eth = float(web3.from_wei(21000 * gas_price, 'ether'))  # Estimated
                return {
                    "success": True,  # Assume success since transaction was sent
                    "tx_hash": tx_hash_hex,
                    "gas_used": 21000,
                    "gas_fee_eth": gas_fee_eth
                }
                
        except Exception as e:
            logger.error(f"Error in ETH transfer: {e}")
            return {"success": False, "tx_hash": None, "gas_used": 0, "gas_fee_eth": 0.0}

    @staticmethod
    def _execute_erc20_transfer(web3, private_key: str, from_address: str, to_address: str, amount: float, coin_config: dict) -> dict:
        """Execute ERC-20 token transfer (USDT, etc.)"""
        try:
            from web3 import Web3
            from eth_account import Account
            
            # ERC-20 ABI for transfer function
            ERC20_ABI = [
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
                    "inputs": [],
                    "name": "decimals",
                    "outputs": [{"name": "", "type": "uint8"}],
                    "payable": False,
                    "stateMutability": "view",
                    "type": "function"
                }
            ]
            
            # Get contract
            contract_address = coin_config.get("contract_address")
            if not contract_address:
                logger.error(f"No contract address for {coin_config['symbol']}")
                return {"success": False, "tx_hash": None, "gas_used": 0, "gas_fee_eth": 0.0}
                
            contract = web3.eth.contract(
                address=Web3.to_checksum_address(contract_address),
                abi=ERC20_ABI
            )
            
            # Convert amount to token units (considering decimals)
            decimals = coin_config.get("decimals", 18)
            amount_units = int(amount * (10 ** decimals))
            
            # Get nonce
            nonce = web3.eth.get_transaction_count(from_address)
            
            # Get current gas price
            gas_price = web3.eth.gas_price
            
            # Build transaction
            transaction = contract.functions.transfer(
                to_address, amount_units
            ).build_transaction({
                'from': from_address,
                'gas': 100000,  # Estimate for ERC-20 transfer
                'gasPrice': gas_price,
                'nonce': nonce,
                'chainId': web3.eth.chain_id
            })
            
            # Estimate gas more precisely
            try:
                estimated_gas = web3.eth.estimate_gas(transaction)
                transaction['gas'] = int(estimated_gas * 1.2)  # Add 20% buffer
            except Exception as gas_error:
                logger.warning(f"Could not estimate gas, using default: {gas_error}")
            
            # Sign transaction
            signed_txn = web3.eth.account.sign_transaction(transaction, private_key)
            
            # Send transaction
            tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            tx_hash_hex = tx_hash.hex()
            
            logger.info(f"{coin_config['symbol']} transfer sent: {tx_hash_hex}")
            
            # Wait for transaction receipt
            try:
                receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                gas_used = receipt.gasUsed
                gas_fee_eth = float(web3.from_wei(gas_used * gas_price, 'ether'))
                
                if receipt.status == 1:
                    logger.info(f"{coin_config['symbol']} transfer confirmed: {tx_hash_hex}, Gas used: {gas_used}")
                    return {
                        "success": True,
                        "tx_hash": tx_hash_hex,
                        "gas_used": gas_used,
                        "gas_fee_eth": gas_fee_eth
                    }
                else:
                    logger.error(f"{coin_config['symbol']} transfer failed: {tx_hash_hex}")
                    return {"success": False, "tx_hash": tx_hash_hex, "gas_used": gas_used, "gas_fee_eth": gas_fee_eth}
                    
            except Exception as receipt_error:
                logger.warning(f"Could not get receipt for {tx_hash_hex}: {receipt_error}")
                # Transaction was sent, but we couldn't confirm
                gas_fee_eth = float(web3.from_wei(transaction['gas'] * gas_price, 'ether'))  # Estimated
                return {
                    "success": True,  # Assume success since transaction was sent
                    "tx_hash": tx_hash_hex,
                    "gas_used": transaction['gas'],
                    "gas_fee_eth": gas_fee_eth
                }
                
        except Exception as e:
            logger.error(f"Error in {coin_config['symbol']} transfer: {e}")
            return {"success": False, "tx_hash": None, "gas_used": 0, "gas_fee_eth": 0.0}
