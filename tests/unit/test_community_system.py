import asyncio
from datetime import datetime


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_database_connection_basic():
    from config import db

    test_doc = {"test": True, "timestamp": datetime.now(), "type": "system_test"}
    result = db.community_posts.insert_one(test_doc)
    found = db.community_posts.find_one({"_id": result.inserted_id})
    db.community_posts.delete_one({"_id": result.inserted_id})
    assert found is not None


def test_market_data_fetcher_returns_structure(monkeypatch):
    import community.content_generator as cg

    class DummyResp:
        def __init__(self, payload):
            self._payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    payload = {
        "bitcoin": {"usd": 43000, "usd_24h_change": 1.2},
        "ethereum": {"usd": 2500, "usd_24h_change": -0.8},
        "tether": {"usd": 1.0, "usd_24h_change": 0.0},
    }

    monkeypatch.setattr(
        cg, "requests", type("R", (), {"get": lambda *a, **k: DummyResp(payload)})
    )

    fetcher = cg.MarketDataFetcher()
    data = run(fetcher.get_market_data())

    assert "prices" in data and "changes" in data and "market_sentiment" in data
    assert "BTC" in data["prices"] and "ETH" in data["prices"] and "USDT" in data["prices"]


def test_ai_content_generator_returns_nonempty_without_gemini(monkeypatch):
    # Ensure GEMINI_API_KEY is not set so fallbacks are used
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    from community.content_generator import AIContentGenerator

    generator = AIContentGenerator()
    for content_type in [
        "educational",
        "market_brief",
        "platform_update",
        "security_tip",
        "weekly_analysis",
    ]:
        content = run(generator.generate_content(content_type))
        assert isinstance(content, str)
        assert len(content.strip()) > 0


def test_poster_channel_connection_without_config_returns_error(monkeypatch):
    # No COMMUNITY_CHANNEL_ID should yield a clear error and no posting
    monkeypatch.delenv("COMMUNITY_CHANNEL_ID", raising=False)

    from community.poster import CommunityPoster

    poster = CommunityPoster()
    result = run(poster.test_channel_connection())
    assert result.get("success") is False
    assert "COMMUNITY_CHANNEL_ID" in result.get("error", "")


def test_scheduler_initialization_and_status_lifecycle():
    from community.scheduler import get_community_scheduler

    scheduler = run(get_community_scheduler())

    # Seed a minimal valid schedule via public API to avoid env-specific defaults
    minimal_schedule = {
        "enabled": True,
        "weekly_schedule": {
            "monday": [{"time": "09:00", "type": "educational"}],
        },
    }

    # Apply schedule (restarts scheduler internally if running)
    assert run(scheduler.update_schedule(minimal_schedule)) is True

    status = scheduler.get_status()
    assert status["running"] is False

    run(scheduler.start())
    status_running = scheduler.get_status()
    assert status_running["running"] is True
    assert status_running["total_jobs"] >= 1

    run(scheduler.stop())
    status_stopped = scheduler.get_status()
    assert status_stopped["running"] is False


