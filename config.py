import os
import logging
import sys
from telegram import Update
from telegram.ext import Application, ContextTypes, CommandHandler, MessageHandler, filters

import emoji
from quart import Quart, Blueprint, make_response, request
from flask_restful import Api, Resource
from pymongo import MongoClient
import random
import requests
import string
import asyncio
# from prisma import Client
from datetime import datetime
import cryptocompare
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

DEBUG = False

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

# Initialize bot application
application = Application.builder().token(TOKEN).build()

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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)
