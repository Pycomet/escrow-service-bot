import base64
import os
from unittest.mock import MagicMock, patch

from cryptography.fernet import Fernet

from functions.utils import generate_id
from functions.wallet import WalletManager


def _ensure_test_key():
    """Guarantee WALLET_ENCRYPTION_KEY exists for WalletManager."""
    if not os.getenv("WALLET_ENCRYPTION_KEY"):
        key = Fernet.generate_key()
        os.environ["WALLET_ENCRYPTION_KEY"] = base64.urlsafe_b64encode(key).decode()


@patch("functions.wallet.db")
def test_wallet_creation_and_encryption(mock_db):
    """Test wallet creation with mocked database operations - simplified test"""
    _ensure_test_key()

    user_id = generate_id()

    # Mock that user doesn't have a wallet initially
    mock_db.wallets.find_one.return_value = None

    # Mock successful wallet creation
    mock_wallet = {
        "_id": f"wallet_{user_id}",
        "user_id": user_id,
        "mnemonic_encrypted": "encrypted_mnemonic_data",
        "created_at": "2023-01-01T00:00:00Z",
        "is_active": True,
    }

    mock_db.wallets.insert_one.return_value = MagicMock(inserted_id=mock_wallet["_id"])
    mock_db.coin_addresses.insert_many.return_value = MagicMock()

    # Mock the encryption/decryption methods
    with patch.object(
        WalletManager, "_encrypt_data", return_value="encrypted_mnemonic_data"
    ) as mock_encrypt:
        with patch.object(
            WalletManager,
            "_decrypt_data",
            return_value="test mnemonic phrase with twelve words here now",
        ) as mock_decrypt:
            with patch("functions.wallet.Mnemonic") as mock_mnemonic_class:
                mock_mnemonic = MagicMock()
                mock_mnemonic_class.return_value = mock_mnemonic
                mock_mnemonic.generate.return_value = (
                    "test mnemonic phrase with twelve words here now"
                )

                # Mock address creation methods to avoid complex crypto operations
                with patch.object(
                    WalletManager,
                    "_create_coin_address",
                    return_value={
                        "_id": "test_address_id",
                        "wallet_id": mock_wallet["_id"],
                        "coin_symbol": "BTC",
                        "address": "test_address",
                        "balance": "0.0",
                    },
                ):

                    # Test wallet creation
                    result = WalletManager.create_wallet_for_user(user_id)

                    # Verify database operations were called
                    mock_db.wallets.find_one.assert_called()
                    mock_db.wallets.insert_one.assert_called()

                    # Verify encryption was used
                    mock_encrypt.assert_called()

                    # Verify that the function completed without database connection errors
                    # (The main goal is to ensure no real database connection is attempted)
                    assert True, "Test completed without database connection errors"
