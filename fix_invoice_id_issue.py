#!/usr/bin/env python3
"""
Fix for MongoDB duplicate key error on invoice_id field.

This script:
1. Drops the existing unique index on invoice_id
2. Creates a new partial unique index that only applies to non-null values
3. Updates existing trades with empty invoice_id to null
4. Validates the fix
"""

import logging
from datetime import datetime

import pymongo

from config import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fix_invoice_id_issue():
    """Fix the invoice_id duplicate key issue"""

    try:
        logger.info("🔧 Starting invoice_id issue fix...")

        # Step 1: Check current state
        logger.info("📊 Checking current database state...")
        empty_invoice_trades = list(db.trades.find({"invoice_id": ""}))
        null_invoice_trades = list(db.trades.find({"invoice_id": None}))
        total_trades = db.trades.count_documents({})

        logger.info(
            f"Found {len(empty_invoice_trades)} trades with empty string invoice_id"
        )
        logger.info(f"Found {len(null_invoice_trades)} trades with null invoice_id")
        logger.info(f"Total trades: {total_trades}")

        # Step 2: Drop the existing unique index
        logger.info("🗑️ Dropping existing unique index on invoice_id...")
        try:
            db.trades.drop_index("invoice_id_unique")
            logger.info("✅ Successfully dropped invoice_id_unique index")
        except pymongo.errors.OperationFailure as e:
            if "index not found" in str(e).lower():
                logger.info("ℹ️ Index invoice_id_unique not found (already dropped)")
            else:
                logger.error(f"Error dropping index: {e}")
                return False

        # Step 3: Update trades with empty invoice_id to null
        logger.info("🔄 Updating trades with empty invoice_id to null...")
        result = db.trades.update_many(
            {"invoice_id": ""}, {"$set": {"invoice_id": None}}
        )
        logger.info(
            f"✅ Updated {result.modified_count} trades from empty string to null"
        )

        # Step 4: Create new partial unique index
        logger.info("🔧 Creating new partial unique index on invoice_id...")
        try:
            # Partial index only applies to documents where invoice_id exists and is a string
            # This will exclude null values and empty strings won't be an issue since we convert them to null
            db.trades.create_index(
                [("invoice_id", 1)],
                name="invoice_id_partial_unique",
                unique=True,
                background=True,
                partialFilterExpression={
                    "invoice_id": {"$exists": True, "$type": "string"}
                },
            )
            logger.info("✅ Successfully created partial unique index on invoice_id")
        except Exception as e:
            logger.error(f"Error creating partial unique index: {e}")
            return False

        # Step 5: Validate the fix
        logger.info("🔍 Validating the fix...")

        # Check that we can insert multiple trades with null invoice_id
        test_trade_1 = {
            "_id": "TEST_TRADE_1",
            "seller_id": "test_user_1",
            "buyer_id": "",
            "currency": "USD",
            "is_active": False,
            "is_paid": False,
            "price": 0,
            "invoice_id": None,  # This should be allowed (not indexed)
            "is_completed": False,
            "chat": None,
            "trade_type": "CryptoToCrypto",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "receiving_address": "",
            "seller_wallet_id": "",
            "is_wallet_trade": False,
        }

        test_trade_2 = test_trade_1.copy()
        test_trade_2["_id"] = "TEST_TRADE_2"
        test_trade_2["seller_id"] = "test_user_2"

        # Test trade with actual invoice_id (should be unique)
        test_trade_3 = test_trade_1.copy()
        test_trade_3["_id"] = "TEST_TRADE_3"
        test_trade_3["seller_id"] = "test_user_3"
        test_trade_3["invoice_id"] = "TEST_INVOICE_123"

        try:
            # Insert two test trades with null invoice_id (should work)
            db.trades.insert_one(test_trade_1)
            db.trades.insert_one(test_trade_2)
            logger.info("✅ Successfully inserted two test trades with null invoice_id")

            # Insert trade with actual invoice_id (should work)
            db.trades.insert_one(test_trade_3)
            logger.info("✅ Successfully inserted test trade with actual invoice_id")

            # Try to insert duplicate invoice_id (should fail)
            test_trade_4 = test_trade_3.copy()
            test_trade_4["_id"] = "TEST_TRADE_4"
            test_trade_4["seller_id"] = "test_user_4"
            # Same invoice_id as test_trade_3

            try:
                db.trades.insert_one(test_trade_4)
                logger.error("❌ Validation failed - duplicate invoice_id was allowed")
                return False
            except pymongo.errors.DuplicateKeyError:
                logger.info("✅ Correctly rejected duplicate invoice_id")

            # Clean up test trades
            db.trades.delete_many(
                {
                    "_id": {
                        "$in": [
                            "TEST_TRADE_1",
                            "TEST_TRADE_2",
                            "TEST_TRADE_3",
                            "TEST_TRADE_4",
                        ]
                    }
                }
            )
            logger.info("🧹 Cleaned up test trades")

        except pymongo.errors.DuplicateKeyError as e:
            logger.error(f"❌ Validation failed - unexpected duplicate key error: {e}")
            return False

        # Step 6: Final state check
        logger.info("📊 Final database state check...")
        empty_invoice_trades_after = list(db.trades.find({"invoice_id": ""}))
        null_invoice_trades_after = list(db.trades.find({"invoice_id": None}))

        logger.info(
            f"Trades with empty string invoice_id after fix: {len(empty_invoice_trades_after)}"
        )
        logger.info(
            f"Trades with null invoice_id after fix: {len(null_invoice_trades_after)}"
        )

        # List current indexes
        indexes = list(db.trades.list_indexes())
        logger.info("📋 Current indexes on trades collection:")
        for idx in indexes:
            logger.info(f"  - {idx['name']}: {idx.get('key', 'N/A')}")

        logger.info("🎉 Invoice ID issue fix completed successfully!")
        return True

    except Exception as e:
        logger.error(f"❌ Error during fix: {e}")
        return False


if __name__ == "__main__":
    success = fix_invoice_id_issue()
    if success:
        print("\n✅ Fix completed successfully!")
    else:
        print("\n❌ Fix failed!")
        exit(1)
