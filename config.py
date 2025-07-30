import asyncio
import logging
import os
import random
import string
import sys

# from prisma import Client
from datetime import datetime
from typing import Optional

import cryptocompare
import emoji
import requests
from dotenv import load_dotenv
from flask_restful import Api, Resource
from pymongo import MongoClient
from quart import Blueprint, Quart, make_response, request
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv()

# Enable debug mode via environment variable (default False)
# This allows certain components (e.g., wallet manager) to be more lenient during local development.
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Configuration variables
TOKEN = os.getenv("TOKEN")  # Keep as TOKEN to maintain compatibility
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "codefred")

WEBHOOK_MODE = os.getenv("WEBHOOK_MODE", "False").lower() == "true"
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
DOMAIN = WEBHOOK_URL.replace("https://", "").split("/")[0] if WEBHOOK_URL else None
PORT = int(os.getenv("PORT", "8080"))  # Changed default to 8080

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

BTCPAY_URL = os.getenv("BTCPAY_URL")
BTCPAY_API_KEY = os.getenv("BTCPAY_API_KEY")
BTCPAY_STORE_ID = os.getenv("BTCPAY_STORE_ID")

DATABASE_URL = os.getenv("DATABASE_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME")

REVIEW_CHANNEL = os.getenv("REVIEW_CHANNEL", "trusted_escrow_bot_reviews")
CONTACT_SUPPORT = os.getenv("CONTACT_SUPPORT", "trusted_escrow_bot_support")
TRADING_CHANNEL = os.getenv("TRADING_CHANNEL", "trusted_escrow_bot_trading")

# Bot fee configuration
BOT_FEE_PERCENTAGE = float(os.getenv("BOT_FEE_PERCENTAGE", "2.5"))  # Default 2.5% fee

# Initialize bot application
if TOKEN:
    application = Application.builder().token(TOKEN).build()
else:
    # For testing environments where TOKEN might not be set
    application = None

# Initialize Quart application
app = Quart(__name__)

# Initialize database connection
client = MongoClient(DATABASE_URL)
db = client[DATABASE_NAME]

# Define collections
wallets = db.wallets
coin_addresses = db.coin_addresses
wallet_transactions = db.wallet_transactions

# Configure logging to stdout for Cloud Run
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Ensure critical MongoDB indexes exist (idempotent)
# These calls run at import-time, so every process verifies the indexes once.
# If they already exist, MongoDB is a no-op.
# ---------------------------------------------------------------------------


def _ensure_db_indexes():
    try:
        # Trades collection indexes
        # Use partial unique index for invoice_id to allow multiple null values
        db.trades.create_index(
            [("invoice_id", 1)],
            name="invoice_id_partial_unique",
            unique=True,
            background=True,
            partialFilterExpression={
                "invoice_id": {"$exists": True, "$type": "string"}
            },
        )
        db.trades.create_index(
            [("is_active", 1), ("updated_at", -1)],
            name="active_updated_idx",
            background=True,
        )
        db.trades.create_index([("seller_id", 1)], name="seller_idx", background=True)
        db.trades.create_index([("buyer_id", 1)], name="buyer_idx", background=True)

        # Users collection indexes (ensure fast look-ups by affiliate etc.)
        db.users.create_index(
            [("affiliate_code", 1)],
            name="affiliate_code_idx",
            background=True,
            unique=False,
        )

        logger.info("MongoDB indexes ensured ✅")
    except Exception as e:
        logger.error("Failed to create MongoDB indexes: %s", e)


# Invoke immediately
_ensure_db_indexes()
