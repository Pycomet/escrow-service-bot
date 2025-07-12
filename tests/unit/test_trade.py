from unittest.mock import MagicMock, patch

import pytest


class DummyUser:
    id = 111
    first_name = "Alice"


class DummyChat:
    id = 111


class DummyMsg:
    from_user = DummyUser()
    chat = DummyChat()


@patch("functions.trade.db")
@patch("functions.user.db")
def test_trade_lifecycle(mock_user_db, mock_trade_db):
    """Test complete trade lifecycle with mocked database operations"""
    from functions import trades_db

    # Mock database responses
    mock_user_db.users.find_one.return_value = {
        "_id": "111",
        "username": "Alice",
        "first_name": "Alice",
    }

    # Mock trade creation
    test_trade = {
        "_id": "test_trade_123",
        "seller_id": "111",
        "currency": "USDT",
        "trade_type": "CryptoToFiat",
        "is_crypto_deposited": False,
        "is_fiat_paid": False,
        "status": "created",
    }

    mock_trade_db.trades.insert_one.return_value = MagicMock(
        inserted_id="test_trade_123"
    )
    mock_trade_db.trades.find_one.return_value = test_trade
    mock_trade_db.trades.update_one.return_value = MagicMock(modified_count=1)

    # Create new trade as seller
    trade = trades_db.open_new_trade(
        DummyMsg(), currency="USDT", trade_type="CryptoToFiat"
    )
    tid = trade["_id"]

    # Update mock for deposited status
    test_trade["is_crypto_deposited"] = True
    test_trade["status"] = "deposited"
    mock_trade_db.trades.find_one.return_value = test_trade

    # Seller deposit
    assert trades_db.confirm_crypto_deposit(tid)
    trades_db.update_trade_status(tid, "deposited")

    # Add buyer
    test_trade["buyer_id"] = "222"
    mock_trade_db.trades.find_one.return_value = test_trade
    trades_db.add_buyer(trade, buyer_id="222")

    # Update mock for fiat paid status
    test_trade["is_fiat_paid"] = True
    test_trade["status"] = "fiat_paid"
    mock_trade_db.trades.find_one.return_value = test_trade

    # Buyer confirms fiat payment
    assert trades_db.confirm_fiat_payment(tid)
    trades_db.update_trade_status(tid, "fiat_paid")

    final = trades_db.get_trade(tid)
    assert final["is_crypto_deposited"] is True
    assert final["is_fiat_paid"] is True
    assert final["status"] == "fiat_paid"
