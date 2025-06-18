import os
import base64
import pytest
import types
from cryptography.fernet import Fernet

from functions.wallet import WalletManager
from functions.utils import generate_id


@pytest.fixture(scope="session", autouse=True)
def _ensure_key():
    if not os.getenv("WALLET_ENCRYPTION_KEY"):
        os.environ["WALLET_ENCRYPTION_KEY"] = base64.urlsafe_b64encode(Fernet.generate_key()).decode()


@pytest.mark.asyncio
async def test_get_balance_uses_refresh(monkeypatch):
    """Integration‐style test that WalletManager.get_balance returns value provided by _refresh_coin_balance."""
    wm = WalletManager()
    user_id = generate_id()
    wallet = wm.create_wallet_for_user(user_id)
    btc_addr_doc = WalletManager.get_wallet_coin_address(wallet["_id"], "BTC")
    addr = btc_addr_doc["address"]

    # Monkeypatch _refresh_coin_balance to set balance to a known value.
    async def fake_refresh(coin_address):
        # Update mocked balance field directly in DB
        from config import db
        db.coin_addresses.update_one({"_id": coin_address["_id"]}, {"$set": {"balance": "0.123"}})
        return True

    monkeypatch.setattr(wm, "_refresh_coin_balance", fake_refresh)

    value = wm.get_balance(addr, "BTC")
    assert value == 0.123 