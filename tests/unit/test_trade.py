import pytest
from functions import trades_db

class DummyUser:
    id = 111
    first_name = "Alice"

class DummyChat:
    id = 111

class DummyMsg:
    from_user = DummyUser()
    chat = DummyChat()


def test_trade_lifecycle():
    # Create new trade as seller
    trade = trades_db.open_new_trade(DummyMsg(), currency="USDT", trade_type="CryptoToFiat")
    tid = trade["_id"]

    # Seller deposit
    assert trades_db.confirm_crypto_deposit(tid)
    trades_db.update_trade_status(tid, "deposited")

    # Add buyer
    trades_db.add_buyer(trade, buyer_id="222")

    # Buyer confirms fiat payment
    assert trades_db.confirm_fiat_payment(tid)
    trades_db.update_trade_status(tid, "fiat_paid")

    final = trades_db.get_trade(tid)
    assert final["is_crypto_deposited"] is True
    assert final["is_fiat_paid"] is True
    assert final["status"] == "fiat_paid" 