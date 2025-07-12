#!/usr/bin/env python3
"""
Production configuration validation test.
This script validates that all required environment variables are set correctly.
"""

import os
import sys

from config import ADMIN_ID, DATABASE_NAME, DATABASE_URL, TOKEN


def test_production_config():
    """Test that all required production environment variables are set."""
    print("🔍 Testing production configuration...")

    # Display current values (masked for security)
    print(f"TOKEN: {TOKEN[:10]}..." if TOKEN else "TOKEN: Not set")
    print(
        f"DATABASE_URL: {DATABASE_URL[:20]}..."
        if DATABASE_URL
        else "DATABASE_URL: Not set"
    )
    print(f"DATABASE_NAME: {DATABASE_NAME}")
    print(f"ADMIN_ID: {ADMIN_ID}")
    print(f"DEBUG: {os.getenv('DEBUG')}")

    # Basic validation
    errors = []

    if not TOKEN:
        errors.append("TELEGRAM_BOT_TOKEN is required")

    if not DATABASE_URL:
        errors.append("DATABASE_URL is required")

    if not ADMIN_ID or ADMIN_ID == 0:
        errors.append("ADMIN_ID is required")

    if errors:
        print("❌ Configuration errors found:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)

    print("✅ All required environment variables are set correctly")


if __name__ == "__main__":
    test_production_config()
