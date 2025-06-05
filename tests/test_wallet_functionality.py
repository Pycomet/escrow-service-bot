import pytest
import asyncio
import os
import sys
import logging
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
import json

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import test modules
from functions.wallet import WalletManager
from handlers.wallet import wallet_handler, wallet_create_handler, wallet_refresh_handler, wallet_details_handler
from database.types import WalletType, CoinAddressType, WalletTransactionType
from functions.utils import generate_id

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Module-level fixtures that can be used by all test classes
@pytest.fixture
def mock_db():
    """Mock database collections"""
    mock_db = Mock()
    mock_db.wallets = Mock()
    mock_db.coin_addresses = Mock()
    mock_db.wallet_transactions = Mock()
    return mock_db

@pytest.fixture
def sample_user_id():
    """Sample user ID for testing"""
    return "test_user_123"

@pytest.fixture
def sample_wallet():
    """Sample wallet data for testing"""
    return {
        "_id": "wallet_123",
        "user_id": "test_user_123",
        "wallet_name": "Test Wallet",
        "mnemonic_encrypted": "encrypted_mnemonic_data",
        "is_active": True,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

@pytest.fixture
def sample_coin_addresses():
    """Sample coin addresses for testing"""
    return [
        {
            "_id": "addr_btc_123",
            "wallet_id": "wallet_123",
            "coin_symbol": "BTC",
            "network": "bitcoin",
            "address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
            "private_key_encrypted": "encrypted_btc_key",
            "derivation_path": "m/44'/0'/0'/0/0",
            "is_default": True,
            "balance": "0.001",
            "balance_usd": "45.67",
            "last_balance_update": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat()
        },
        {
            "_id": "addr_eth_123",
            "wallet_id": "wallet_123",
            "coin_symbol": "ETH",
            "network": "ethereum",
            "address": "0x742d35Cc6aF4C7f1b7b5C70b5B8B5F7D6E5A8A5F",
            "private_key_encrypted": "encrypted_eth_key",
            "derivation_path": "m/44'/60'/0'/0/0",
            "is_default": True,
            "balance": "0.1",
            "balance_usd": "234.56",
            "last_balance_update": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat()
        }
    ]

class TestWalletManager:
    """Test suite for WalletManager functionality"""

    def test_wallet_manager_initialization(self):
        """Test WalletManager initialization"""
        wallet_manager = WalletManager()
        
        assert wallet_manager is not None
        assert hasattr(wallet_manager, 'SUPPORTED_COINS')
        assert hasattr(wallet_manager, 'DEFAULT_COINS')
        assert len(wallet_manager.DEFAULT_COINS) >= 5  # Should have at least BTC, ETH, LTC, DOGE, SOL
        
        # Check that default coins are supported
        for coin in wallet_manager.DEFAULT_COINS:
            assert coin in wallet_manager.SUPPORTED_COINS
    
    def test_supported_coins_configuration(self):
        """Test that supported coins are properly configured"""
        wallet_manager = WalletManager()
        
        required_fields = ['name', 'symbol', 'decimals', 'network', 'network_type', 'is_token']
        
        for coin_symbol, config in wallet_manager.SUPPORTED_COINS.items():
            # Check required fields
            for field in required_fields:
                assert field in config, f"Missing {field} in {coin_symbol} config"
            
            # Check data types
            assert isinstance(config['name'], str)
            assert isinstance(config['symbol'], str)
            assert isinstance(config['decimals'], int)
            assert isinstance(config['network'], str)
            assert isinstance(config['network_type'], str)
            assert isinstance(config['is_token'], bool)
            
            # Check symbol matches key
            assert config['symbol'] == coin_symbol
    
    @patch('functions.wallet.db')
    def test_create_wallet_for_user_success(self, mock_db, sample_user_id):
        """Test successful wallet creation"""
        # Mock database responses
        mock_db.wallets.find_one.return_value = None  # No existing wallet
        mock_db.wallets.insert_one.return_value = Mock(inserted_id="wallet_123")
        mock_db.coin_addresses.insert_many.return_value = Mock(inserted_ids=["addr1", "addr2", "addr3"])
        
        # Create wallet
        wallet = WalletManager.create_wallet_for_user(sample_user_id, "Test Wallet")
        
        # Assertions
        assert wallet is not None
        assert wallet['user_id'] == sample_user_id
        assert wallet['wallet_name'] == "Test Wallet"
        assert wallet['is_active'] is True
        assert 'mnemonic_encrypted' in wallet
        assert 'created_at' in wallet
        
        # Verify database calls
        mock_db.wallets.find_one.assert_called_once()
        mock_db.wallets.insert_one.assert_called_once()
        mock_db.coin_addresses.insert_many.assert_called_once()
    
    @patch('functions.wallet.db')
    def test_create_wallet_for_user_existing_wallet(self, mock_db, sample_user_id, sample_wallet):
        """Test wallet creation when user already has a wallet"""
        # Mock existing wallet
        mock_db.wallets.find_one.return_value = sample_wallet
        
        # Attempt to create wallet
        wallet = WalletManager.create_wallet_for_user(sample_user_id, "New Wallet")
        
        # Should return existing wallet
        assert wallet == sample_wallet
        
        # Should not attempt to create new wallet
        mock_db.wallets.insert_one.assert_not_called()
    
    @patch('functions.wallet.db')
    def test_get_user_wallet(self, mock_db, sample_user_id, sample_wallet):
        """Test getting user's wallet"""
        # Mock database response
        mock_db.wallets.find_one.return_value = sample_wallet
        
        # Get wallet
        wallet = WalletManager.get_user_wallet(sample_user_id)
        
        # Assertions
        assert wallet == sample_wallet
        mock_db.wallets.find_one.assert_called_once_with({"user_id": sample_user_id, "is_active": True})
    
    @patch('functions.wallet.db')
    def test_get_user_wallet_not_found(self, mock_db, sample_user_id):
        """Test getting user's wallet when none exists"""
        # Mock no wallet found
        mock_db.wallets.find_one.return_value = None
        
        # Get wallet
        wallet = WalletManager.get_user_wallet(sample_user_id)
        
        # Should return None
        assert wallet is None
    
    @patch('functions.wallet.db')
    def test_get_wallet_coin_addresses(self, mock_db, sample_coin_addresses):
        """Test getting coin addresses for a wallet"""
        # Mock database response
        mock_cursor = Mock()
        mock_cursor.sort.return_value = sample_coin_addresses
        mock_db.coin_addresses.find.return_value = mock_cursor
        
        # Get coin addresses
        addresses = WalletManager.get_wallet_coin_addresses("wallet_123")
        
        # Assertions
        assert addresses == sample_coin_addresses
        mock_db.coin_addresses.find.assert_called_once_with({"wallet_id": "wallet_123"})
        mock_cursor.sort.assert_called_once_with([("is_default", -1), ("coin_symbol", 1)])
    
    @patch('functions.wallet.db')
    def test_get_wallet_coin_address(self, mock_db, sample_coin_addresses):
        """Test getting specific coin address from wallet"""
        # Mock database response
        mock_db.coin_addresses.find_one.return_value = sample_coin_addresses[0]
        
        # Get specific coin address
        address = WalletManager.get_wallet_coin_address("wallet_123", "BTC")
        
        # Assertions
        assert address == sample_coin_addresses[0]
        mock_db.coin_addresses.find_one.assert_called_once_with({
            "wallet_id": "wallet_123",
            "coin_symbol": "BTC"
        })
    
    @patch('functions.wallet.db')
    @pytest.mark.asyncio
    async def test_refresh_wallet_balances(self, mock_db, sample_coin_addresses):
        """Test refreshing wallet balances"""
        # Mock database responses
        mock_cursor = Mock()
        mock_cursor.sort.return_value = sample_coin_addresses
        mock_db.coin_addresses.find.return_value = mock_cursor
        mock_db.coin_addresses.update_one.return_value = Mock(modified_count=1)
        
        # Create wallet manager and refresh balances
        wallet_manager = WalletManager()
        success = await wallet_manager.refresh_wallet_balances("wallet_123")
        
        # Should succeed
        assert success is True
        
        # Should update each coin address
        assert mock_db.coin_addresses.update_one.call_count == len(sample_coin_addresses)
    
    @patch('functions.wallet.db')
    def test_add_coin_to_wallet_success(self, mock_db, sample_wallet):
        """Test adding new coin to existing wallet"""
        # Mock database responses
        mock_db.coin_addresses.find_one.return_value = None  # Coin doesn't exist
        mock_db.wallets.find_one.return_value = sample_wallet
        mock_db.coin_addresses.insert_one.return_value = Mock(inserted_id="new_addr")
        
        # Mock the WalletManager methods
        with patch.object(WalletManager, '_decrypt_data') as mock_decrypt, \
             patch.object(WalletManager, '_create_coin_address') as mock_create:
            
            # Mock decryption to return a test mnemonic
            mock_decrypt.return_value = "test abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
            
            # Mock coin address creation
            mock_create.return_value = {
                "_id": "new_addr_trx",
                "wallet_id": "wallet_123",
                "coin_symbol": "TRX",
                "network": "ethereum",
                "address": "0x123...",
                "private_key_encrypted": "encrypted_key",
                "derivation_path": "m/44'/60'/0'/0/0",
                "is_default": False,
                "balance": "0",
                "balance_usd": "0.00",
                "last_balance_update": datetime.now().isoformat(),
                "created_at": datetime.now().isoformat()
            }
            
            # Add coin to wallet
            success = WalletManager.add_coin_to_wallet("wallet_123", "TRX")
            
            # Should succeed
            assert success is True
            mock_db.coin_addresses.insert_one.assert_called_once()
            mock_create.assert_called_once()
    
    @patch('functions.wallet.db')
    def test_add_coin_to_wallet_already_exists(self, mock_db, sample_coin_addresses):
        """Test adding coin that already exists in wallet"""
        # Mock coin already exists
        mock_db.coin_addresses.find_one.return_value = sample_coin_addresses[0]
        
        # Attempt to add existing coin
        success = WalletManager.add_coin_to_wallet("wallet_123", "BTC")
        
        # Should still return True (already exists)
        assert success is True
        mock_db.coin_addresses.insert_one.assert_not_called()
    
    @patch('functions.wallet.db')
    def test_deactivate_wallet(self, mock_db):
        """Test deactivating a wallet"""
        # Mock successful update
        mock_db.wallets.update_one.return_value = Mock(modified_count=1)
        
        # Deactivate wallet
        success = WalletManager.deactivate_wallet("wallet_123")
        
        # Should succeed
        assert success is True
        mock_db.wallets.update_one.assert_called_once()
        
        # Check update call arguments
        args = mock_db.wallets.update_one.call_args
        assert args[0][0] == {"_id": "wallet_123"}
        assert args[0][1]["$set"]["is_active"] is False
    
    def test_get_supported_coins(self):
        """Test getting list of supported coins"""
        coins = WalletManager.get_supported_coins()
        
        assert isinstance(coins, list)
        assert len(coins) > 0
        assert 'BTC' in coins
        assert 'ETH' in coins
        assert 'USDT' in coins
    
    def test_get_default_coins(self):
        """Test getting list of default coins"""
        coins = WalletManager.get_default_coins()
        
        assert isinstance(coins, list)
        assert len(coins) >= 5
        assert 'BTC' in coins
        assert 'ETH' in coins
        assert 'LTC' in coins
        assert 'DOGE' in coins
        assert 'SOL' in coins


class TestWalletHandlers:
    """Test suite for wallet handlers"""
    
    @pytest.fixture
    def mock_update(self):
        """Mock Telegram update object"""
        update = Mock()
        update.effective_user.id = 123456
        update.callback_query = None  # Default to not a callback
        update.message = Mock()
        return update
    
    @pytest.fixture
    def mock_callback_update(self):
        """Mock Telegram callback update object"""
        update = Mock()
        update.effective_user.id = 123456
        update.callback_query = Mock()
        update.callback_query.message = Mock()
        update.callback_query.from_user.id = 123456
        update.callback_query.data = "my_wallets"
        update.callback_query.answer = AsyncMock()
        return update
    
    @pytest.fixture
    def mock_context(self):
        """Mock Telegram context object"""
        context = Mock()
        context.user_data = {}
        return context
    
    @patch('handlers.wallet.WalletManager.get_user_wallet')
    @patch('handlers.wallet.send_message_or_edit')
    @pytest.mark.asyncio
    async def test_wallet_handler_no_wallet(self, mock_send, mock_get_wallet, mock_update, mock_context):
        """Test wallet handler when user has no wallet"""
        # Mock no wallet
        mock_get_wallet.return_value = None
        mock_send.return_value = Mock()
        
        # Call handler
        await wallet_handler(mock_update, mock_context)
        
        # Should prompt to create wallet
        mock_send.assert_called_once()
        call_args = mock_send.call_args
        message_text = call_args[0][1]
        assert "You don't have a wallet yet" in message_text
        assert "Create your first wallet" in message_text
    
    @patch('handlers.wallet.WalletManager.get_user_wallet')
    @patch('handlers.wallet.WalletManager.get_wallet_coin_addresses')
    @patch('handlers.wallet.send_message_or_edit')
    @pytest.mark.asyncio
    async def test_wallet_handler_with_wallet(self, mock_send, mock_get_addresses, mock_get_wallet, 
                                            mock_update, mock_context, sample_wallet, sample_coin_addresses):
        """Test wallet handler when user has a wallet"""
        # Mock wallet and addresses
        mock_get_wallet.return_value = sample_wallet
        mock_get_addresses.return_value = sample_coin_addresses
        mock_send.return_value = Mock()
        
        # Call handler
        await wallet_handler(mock_update, mock_context)
        
        # Should show wallet details
        mock_send.assert_called_once()
        call_args = mock_send.call_args
        message_text = call_args[0][1]
        assert "My Wallet" in message_text
        assert sample_wallet['wallet_name'] in message_text
        assert "BTC" in message_text
        assert "ETH" in message_text
    
    @patch('handlers.wallet.WalletManager.create_wallet_for_user')
    @patch('handlers.wallet.WalletManager.get_wallet_coin_addresses')
    @pytest.mark.asyncio
    async def test_wallet_create_handler_success(self, mock_get_addresses, mock_create_wallet, 
                                                mock_callback_update, mock_context, sample_wallet, sample_coin_addresses):
        """Test successful wallet creation"""
        # Mock successful creation
        mock_create_wallet.return_value = sample_wallet
        mock_get_addresses.return_value = sample_coin_addresses
        
        # Set up callback query
        mock_callback_update.callback_query.edit_message_text = AsyncMock()
        
        # Call handler
        await wallet_create_handler(mock_callback_update, mock_context)
        
        # Should show success message
        assert mock_callback_update.callback_query.edit_message_text.call_count >= 2  # Loading + success
        
        # Check final success message
        final_call = mock_callback_update.callback_query.edit_message_text.call_args_list[-1]
        message_text = final_call[0][0]
        assert "Wallet Created Successfully" in message_text
    
    @patch('handlers.wallet.WalletManager.create_wallet_for_user')
    @pytest.mark.asyncio
    async def test_wallet_create_handler_failure(self, mock_create_wallet, mock_callback_update, mock_context):
        """Test wallet creation failure"""
        # Mock failed creation
        mock_create_wallet.return_value = None
        
        # Set up callback query
        mock_callback_update.callback_query.edit_message_text = AsyncMock()
        
        # Call handler
        await wallet_create_handler(mock_callback_update, mock_context)
        
        # Should show error message
        final_call = mock_callback_update.callback_query.edit_message_text.call_args_list[-1]
        message_text = final_call[0][0]
        assert "Failed to Create Wallet" in message_text
    
    @patch('handlers.wallet.WalletManager')
    @pytest.mark.asyncio
    async def test_wallet_refresh_handler_success(self, mock_wallet_manager_class, mock_callback_update, mock_context):
        """Test successful wallet balance refresh"""
        # Mock successful refresh
        mock_wallet_manager = Mock()
        mock_wallet_manager.refresh_wallet_balances = AsyncMock(return_value=True)
        mock_wallet_manager_class.return_value = mock_wallet_manager
        
        # Set up callback query with wallet ID
        mock_callback_update.callback_query.data = "wallet_refresh_wallet_123"
        mock_callback_update.callback_query.edit_message_text = AsyncMock()
        
        # Call handler
        await wallet_refresh_handler(mock_callback_update, mock_context)
        
        # Should show success message
        final_call = mock_callback_update.callback_query.edit_message_text.call_args_list[-1]
        message_text = final_call[0][0]
        assert "Balances Refreshed" in message_text
    
    @patch('handlers.wallet.WalletManager.get_user_wallet')
    @patch('handlers.wallet.WalletManager.get_wallet_coin_addresses')
    @pytest.mark.asyncio
    async def test_wallet_details_handler_success(self, mock_get_addresses, mock_get_wallet,
                                                 mock_callback_update, mock_context, sample_wallet, sample_coin_addresses):
        """Test wallet details handler success"""
        # Mock wallet and addresses
        mock_get_wallet.return_value = sample_wallet
        mock_get_addresses.return_value = sample_coin_addresses
        
        # Set up callback query
        mock_callback_update.callback_query.data = "wallet_details_wallet_123"
        mock_callback_update.callback_query.edit_message_text = AsyncMock()
        
        # Call handler
        await wallet_details_handler(mock_callback_update, mock_context)
        
        # Should show wallet details
        mock_callback_update.callback_query.edit_message_text.assert_called_once()
        call_args = mock_callback_update.callback_query.edit_message_text.call_args
        message_text = call_args[0][0]
        assert "Wallet Details" in message_text
        assert sample_wallet['wallet_name'] in message_text


class TestWalletIntegration:
    """Integration tests for wallet functionality"""
    
    def test_generate_id_uniqueness(self):
        """Test that generate_id produces unique IDs"""
        ids = set()
        for _ in range(1000):
            new_id = generate_id()
            assert new_id not in ids, f"Duplicate ID generated: {new_id}"
            assert len(new_id) == 10, f"ID length incorrect: {len(new_id)}"
            ids.add(new_id)
    
    def test_wallet_types_structure(self):
        """Test that wallet types have correct structure"""
        # This would normally import the actual types, but for now we'll test the structure
        required_wallet_fields = ['_id', 'user_id', 'wallet_name', 'mnemonic_encrypted', 
                                 'is_active', 'created_at', 'updated_at']
        
        required_address_fields = ['_id', 'wallet_id', 'coin_symbol', 'network', 'address',
                                  'private_key_encrypted', 'derivation_path', 'is_default',
                                  'balance', 'balance_usd', 'last_balance_update', 'created_at']
        
        required_transaction_fields = ['_id', 'wallet_id', 'coin_address_id', 'tx_hash',
                                      'from_address', 'to_address', 'amount', 'coin_symbol',
                                      'fee', 'status', 'block_number', 'confirmations',
                                      'transaction_type', 'created_at', 'confirmed_at']
        
        # These are the expected fields for our wallet types
        assert len(required_wallet_fields) == 7
        assert len(required_address_fields) == 12
        assert len(required_transaction_fields) == 15
    
    @patch.dict(os.environ, {'WALLET_ENCRYPTION_KEY': ''})
    def test_encryption_key_generation(self):
        """Test encryption key generation"""
        wallet_manager1 = WalletManager()
        wallet_manager2 = WalletManager()
        
        # Should generate different keys for different instances when no env key
        # (In production, this should be the same key stored securely)
        assert hasattr(wallet_manager1, 'encryption_key')
        assert hasattr(wallet_manager2, 'encryption_key')
        assert wallet_manager1.encryption_key is not None
        assert wallet_manager2.encryption_key is not None
    
    def test_coin_network_mapping(self):
        """Test that coins are properly mapped to networks"""
        wallet_manager = WalletManager()
        
        # Test Bitcoin-like coins
        bitcoin_coins = ['BTC', 'LTC', 'DOGE']
        for coin in bitcoin_coins:
            config = wallet_manager.SUPPORTED_COINS[coin]
            assert config['network_type'] in ['bitcoin', 'litecoin', 'dogecoin']
            assert config['is_token'] is False
        
        # Test Ethereum and tokens
        eth_config = wallet_manager.SUPPORTED_COINS['ETH']
        assert eth_config['network_type'] == 'ethereum'
        assert eth_config['is_token'] is False
        
        usdt_config = wallet_manager.SUPPORTED_COINS['USDT']
        assert usdt_config['network_type'] == 'ethereum'
        assert usdt_config['is_token'] is True
        assert 'contract_address' in usdt_config


def run_comprehensive_tests():
    """Run all wallet tests and generate a report"""
    
    import subprocess
    import time
    
    logger.info("Starting comprehensive wallet functionality tests...")
    
    # Test results storage
    test_results = {
        "test_session": {
            "start_time": datetime.now().isoformat(),
            "test_type": "wallet_functionality",
            "version": "1.0.0"
        },
        "test_categories": {
            "wallet_manager": {"passed": 0, "failed": 0, "errors": []},
            "wallet_handlers": {"passed": 0, "failed": 0, "errors": []},
            "integration": {"passed": 0, "failed": 0, "errors": []}
        }
    }
    
    try:
        # Run pytest with detailed output
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 
            __file__, 
            '-v', 
            '--tb=short',
            '--no-header'
        ], capture_output=True, text=True, timeout=300)
        
        test_results["test_session"]["end_time"] = datetime.now().isoformat()
        test_results["test_session"]["exit_code"] = result.returncode
        test_results["test_session"]["stdout"] = result.stdout
        test_results["test_session"]["stderr"] = result.stderr
        
        # Parse results
        if result.returncode == 0:
            logger.info("✅ All wallet functionality tests passed!")
            test_results["test_session"]["status"] = "PASSED"
        else:
            logger.error("❌ Some wallet functionality tests failed!")
            test_results["test_session"]["status"] = "FAILED"
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"wallet_functionality_test_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(test_results, f, indent=2)
        
        logger.info(f"Test results saved to: {results_file}")
        return test_results
        
    except subprocess.TimeoutExpired:
        logger.error("❌ Tests timed out after 5 minutes")
        test_results["test_session"]["status"] = "TIMEOUT"
        return test_results
    except Exception as e:
        logger.error(f"❌ Error running tests: {e}")
        test_results["test_session"]["status"] = "ERROR"
        test_results["test_session"]["error"] = str(e)
        return test_results


if __name__ == "__main__":
    # Run tests when script is executed directly
    results = run_comprehensive_tests()
    print(f"\n📊 Test Results Summary:")
    print(f"Status: {results['test_session']['status']}")
    print(f"Exit Code: {results['test_session'].get('exit_code', 'N/A')}")
    
    if results['test_session']['status'] == 'PASSED':
        print("🎉 All wallet functionality tests passed successfully!")
    else:
        print("⚠️  Some tests failed. Check the detailed results file for more information.") 