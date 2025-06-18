import os
import base64
from cryptography.fernet import Fernet

from functions.wallet import WalletManager
from functions.utils import generate_id


def _ensure_test_key():
    """Guarantee WALLET_ENCRYPTION_KEY exists for WalletManager."""
    if not os.getenv("WALLET_ENCRYPTION_KEY"):
        key = Fernet.generate_key()
        os.environ["WALLET_ENCRYPTION_KEY"] = base64.urlsafe_b64encode(key).decode()


def test_wallet_creation_and_encryption():
    _ensure_test_key()

    wm = WalletManager()

    user_id = generate_id()
    wallet = wm.create_wallet_for_user(user_id)

    assert wallet is not None, "Wallet should be created"

    # Mnemonic should be encrypted in DB
    encrypted = wallet["mnemonic_encrypted"]
    assert encrypted != "", "Encrypted mnemonic stored"

    # Decrypt and ensure it looks like a 12/24-word phrase
    decrypted = wm._decrypt_data(encrypted)
    words = decrypted.split()
    assert len(words) in {12, 24}, "Mnemonic should have 12 or 24 words"

    # Ensure default coin addresses were generated
    coin_addresses = WalletManager.get_wallet_coin_addresses(wallet["_id"])
    assert len(coin_addresses) >= len(WalletManager.DEFAULT_COINS)

    # Check balance query returns float (mocked, so 0.0)
    eth_address = WalletManager.get_wallet_coin_address(wallet["_id"], "ETH")
    balance = wm.get_balance(eth_address["address"], "ETH")
    assert isinstance(balance, float) 