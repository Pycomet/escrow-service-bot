import os
import telebot
from telebot import types
import emoji
from flask import Flask, Blueprint, make_response, request, render_template
from flask_restful import Api, Resource
from dotenv import load_dotenv
load_dotenv()

# Configuration variable
TOKEN = os.getenv("TOKEN")

ADMIN_ID = int(os.getenv("ADMIN_ID"))

ADMIN = os.getenv("ADMIN")
SERVER_URL = os.getenv("SERVER_URL")

# # Coinbase API for payments
# API_KEY = os.getenv("API_KEY")
# API_SECRET = os.getenv("API_SECRET")

FORGING_BLOCK_TOKEN = os.getenv("FORGING_BLOCK_TOKEN")
FORGING_BLOCK_STORE = os.getenv("FORGING_BLOCK_STORE")
FORGING_BLOCK_TRADE = os.getenv("FORGING_BLOCK_TRADE")
FORGING_BLOCK_ADDRESS = os.getenv("FORGING_BLOCK_ADDRESS")


BTCPAY_URL = os.getenv("BTCPAY_URL")
BTCPAY_API_KEY = os.getenv("BTCPAY_API_KEY")
BTCPAY_STORE_ID = os.getenv("BTCPAY_STORE_ID")

MAIL = os.getenv("MAIL")
PASS = os.getenv("PASS")

bot = telebot.TeleBot(TOKEN, threaded=True)

import importdir
importdir.do("handlers", globals())
