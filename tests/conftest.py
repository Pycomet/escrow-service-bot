import pytest
import sys
import os
import logging
import mongomock

# Configure logging for tests
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Patch the global Mongo client/db used across the codebase so tests run in-memory.
# We do this once per test session via an autouse session-scoped fixture.

@pytest.fixture(scope="session", autouse=True)
def _patch_mongo(monkeypatch):
    """Swap out the real MongoDB connection for an in-memory mongomock one."""
    # Import config lazily so environment variables for the real app are not required.
    import importlib
    config = importlib.import_module("config")

    # Create an in-memory Mongo client and database with same name the app expects.
    mock_client = mongomock.MongoClient()
    mock_db = mock_client[os.getenv("DATABASE_NAME", "escrowbot_test")]  # default name for tests

    # Monkey-patch the attributes used elsewhere in the codebase.
    monkeypatch.setattr(config, "client", mock_client)
    monkeypatch.setattr(config, "db", mock_db)

    # Also patch any modules that have already imported `config.db` at import-time.
    for module_name in list(sys.modules.keys()):
        module = sys.modules[module_name]
        if hasattr(module, "db") and getattr(module, "db") is getattr(config, "db"):
            monkeypatch.setattr(module, "db", mock_db)

    yield

    # Nothing to cleanup – mongomock is in-memory and will be discarded. 