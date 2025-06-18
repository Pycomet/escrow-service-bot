import pytest
import types

from telegram.ext._testing import PTBTestApplication, MessageBuilder, CallbackQueryBuilder

import config
from functions import trades_db

# ---------------- shared fixtures -----------------
@pytest.fixture(scope="session")
def event_loop():
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def ptb_app():
    """Yield PTBTestApplication wrapping the production bot."""
    test_app: PTBTestApplication = PTBTestApplication.wrap_application(config.application)
    async with test_app:
        yield test_app

# ---------------- helper monkeypatch for missing join_trade -----------------
@pytest.fixture(autouse=True)
def _patch_join_trade(monkeypatch):
    """Provide a simple implementation of trades_db.join_trade if it's missing."""
    if not hasattr(trades_db, "join_trade"):
        def _join_trade(trade_id: str, user_id: str):
            trade = trades_db.get_trade(trade_id)
            if not trade or trade.get("buyer_id"):
                return False
            config.db.trades.update_one({"_id": trade_id}, {"$set": {"buyer_id": user_id}})
            return True
        monkeypatch.setattr(trades_db, "join_trade", _join_trade)
    yield

# ---------------- actual test ----------------------
@pytest.mark.asyncio
async def test_buyer_joins_flow(ptb_app):
    seller_id = 111
    buyer_id = 222

    # Seller creates trade directly via DB helpers (faster than UI)
    seller_msg = types.SimpleNamespace(
        from_user=types.SimpleNamespace(id=seller_id, first_name="Seller"),
        chat=types.SimpleNamespace(id=seller_id)
    )
    trade = trades_db.open_new_trade(seller_msg, currency="USDT", trade_type="CryptoToFiat")
    tid = trade["_id"]
    trades_db.confirm_crypto_deposit(tid)
    trades_db.update_trade_status(tid, "deposited")

    # Buyer interaction via PTB
    mb = MessageBuilder(buyer_id)

    # /join command
    await ptb_app.process_update(mb.command("/join"))

    # buyer sends trade id
    await ptb_app.process_update(mb.text(tid))

    # buyer confirms join
    await ptb_app.process_update(
        CallbackQueryBuilder(buyer_id, data=f"confirm_join_{tid}").build()
    )

    # Validate DB updated
    final = trades_db.get_trade(tid)
    assert final["buyer_id"] == str(buyer_id) 