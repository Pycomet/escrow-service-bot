import types
from unittest.mock import MagicMock, patch

import pytest

from handlers import join as join_handler_module


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


@patch("functions.trade.db")
@patch("functions.user.db")
@pytest.mark.asyncio
async def test_pay_callback_marks_fiat_paid(mock_user_db, mock_trade_db):
    """Test pay callback marks trade as fiat paid with mocked database"""
    from functions import trades_db

    # Mock database responses
    mock_user_db.users.find_one.return_value = {
        "_id": "111",
        "username": "Seller",
        "first_name": "Seller",
    }

    # Mock trade creation and updates
    test_trade = {
        "_id": "test_trade_123",
        "seller_id": "111",
        "buyer_id": "222",
        "currency": "USDT",
        "trade_type": "CryptoToFiat",
        "is_crypto_deposited": True,
        "is_fiat_paid": False,
        "status": "deposited",
    }

    mock_trade_db.trades.insert_one.return_value = MagicMock(
        inserted_id="test_trade_123"
    )
    mock_trade_db.trades.find_one.return_value = test_trade
    mock_trade_db.trades.update_one.return_value = MagicMock(modified_count=1)

    # Arrange: create trade and buyer
    seller_msg = types.SimpleNamespace(
        from_user=types.SimpleNamespace(id=111, first_name="Seller"),
        chat=types.SimpleNamespace(id=111),
    )
    trade = trades_db.open_new_trade(
        seller_msg, currency="USDT", trade_type="CryptoToFiat"
    )
    tid = trade["_id"]
    trades_db.confirm_crypto_deposit(tid)
    trades_db.update_trade_status(tid, "deposited")
    trades_db.add_buyer(trade, buyer_id="222")

    # Update mock for fiat payment
    test_trade["is_fiat_paid"] = True
    test_trade["status"] = "fiat_paid"
    mock_trade_db.trades.find_one.return_value = test_trade

    # Act: simulate buyer clicking pay
    cb = DummyCallbackQuery(data=f"pay_{tid}", user_id="222")
    update = DummyUpdate(cb)
    ctx = DummyContext()
    await join_handler_module.handle_join_callback(update, ctx)

    # Assert
    final = trades_db.get_trade(tid)
    assert final["is_fiat_paid"] is True
    assert final["status"] == "fiat_paid"
