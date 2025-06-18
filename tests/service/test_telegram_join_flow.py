import pytest
import types

from telegram import Update
from telegram.ext._testing import PTBTestApplication, MessageBuilder, CallbackQueryBuilder

from functions import trades_db
from functions.utils import generate_id
from handlers import join as join_handler_module
import config

# ---------------------------------------------------------------------------
# Full PTB integration test for seller creating trade
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def event_loop():
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def ptb_app():
    """Yield PTBTestApplication wrapping the production Application."""
    from config import application as prod_app
    test_app: PTBTestApplication = PTBTestApplication.wrap_application(prod_app)
    async with test_app:
        yield test_app

@pytest.mark.asyncio
async def test_seller_creates_trade_flow(ptb_app):
    chat_id = 101
    mb = MessageBuilder(chat_id)

    # /start
    await ptb_app.process_update(mb.command("/start"))

    # /trade to open main menu
    await ptb_app.process_update(mb.command("/trade"))

    # Choose Crypto→Fiat flow
    await ptb_app.process_update(
        CallbackQueryBuilder(chat_id, data="trade_type_CryptoToFiat").build()
    )

    # Enter amount
    await ptb_app.process_update(mb.text("150"))

    # Choose USDT as currency
    await ptb_app.process_update(
        CallbackQueryBuilder(chat_id, data="currency_USDT").build()
    )

    # Enter terms/description
    await ptb_app.process_update(mb.text("Selling 150 USDT, pay 150 EUR via SEPA."))

    # Verify trade exists in mocked DB
    trades = list(config.db.trades.find())
    assert len(trades) == 1
    t = trades[0]
    assert t["currency"] == "USDT"
    assert t["price"] == 150
    assert t["is_wallet_trade"] is True 