"""
Test configuration file that overrides production settings for testing.
"""

import os
from unittest.mock import MagicMock

# Test configuration
TEST_DATABASE_URL = "mongodb://testuser:testpass@localhost:27017/?authSource=admin"
TEST_DATABASE_NAME = "escrow_test"

# Mock objects
mock_db = MagicMock()
mock_application = MagicMock()
mock_client = MagicMock()

# Environment settings for tests
os.environ["TESTING"] = "True"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["DATABASE_NAME"] = TEST_DATABASE_NAME 