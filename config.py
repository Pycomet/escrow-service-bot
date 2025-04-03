import os
import logging
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

from dotenv import load_dotenv
load_dotenv()

DEBUG = True

# Configuration variable
TOKEN = os.getenv("TOKEN")

WEBHOOK_MODE = os.getenv("WEBHOOK_MODE", "False").lower() == "true"
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
DOMAIN = WEBHOOK_URL.replace("https://", "").split("/")[0] if WEBHOOK_URL else None
PORT = int(os.getenv("PORT", "5000"))

ADMIN_ID = int(os.getenv("ADMIN_ID"))

BTCPAY_URL = os.getenv("BTCPAY_URL")
BTCPAY_API_KEY = os.getenv("BTCPAY_API_KEY")
BTCPAY_STORE_ID = os.getenv("BTCPAY_STORE_ID")

DATABASE_URL = os.getenv("DATABASE_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME")

application = Application.builder().token(TOKEN).build()

# Initialize application
app = Quart(__name__)

client = MongoClient(DATABASE_URL)
db = client[DATABASE_NAME]

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO if not DEBUG else logging.DEBUG
)
logger = logging.getLogger(__name__)
