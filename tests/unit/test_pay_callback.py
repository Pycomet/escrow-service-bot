import types
import pytest

from handlers import join as join_handler_module
from functions import trades_db

class DummyBot:
    async def send_message(self, *args, **kwargs):
        return None

class DummyMessage:
    async def edit_text(self, *args, **kwargs):
        return None

class DummyCallbackQuery:
    def __init__(self, data, user_id):
        self.data = data
        self.from_user = types.SimpleNamespace(id=user_id)
        self.message = DummyMessage()
    async def answer(self):
        return None

class DummyUpdate:
    def __init__(self, cb):
        self.callback_query = cb

class DummyContext:
    def __init__(self):
        self.bot = DummyBot()
        self.user_data = {}

@pytest.mark.asyncio
async def test_pay_callback_marks_fiat_paid():
    # Arrange: create trade and buyer
    seller_msg = types.SimpleNamespace(
        from_user=types.SimpleNamespace(id=111, first_name="Seller"),
        chat=types.SimpleNamespace(id=111)
    )
    trade = trades_db.open_new_trade(seller_msg, currency="USDT", trade_type="CryptoToFiat")
    tid = trade["_id"]
    trades_db.confirm_crypto_deposit(tid)
    trades_db.update_trade_status(tid, "deposited")
    trades_db.add_buyer(trade, buyer_id="222")

    # Act: simulate buyer clicking pay
    cb = DummyCallbackQuery(data=f"pay_{tid}", user_id="222")
    update = DummyUpdate(cb)
    ctx = DummyContext()
    await join_handler_module.handle_join_callback(update, ctx)

    # Assert
    final = trades_db.get_trade(tid)
    assert final["is_fiat_paid"] is True
    assert final["status"] == "fiat_paid" 