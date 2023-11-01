import os
import telegram
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

# # Coinbase API for payments
# API_KEY = os.getenv("API_KEY")
# API_SECRET = os.getenv("API_SECRET")

FORGING_BLOCK_TOKEN = os.getenv("FORGING_BLOCK_TOKEN")
FORGING_BLOCK_STORE = os.getenv("FORGING_BLOCK_STORE")
FORGING_BLOCK_TRADE = os.getenv("FORGING_BLOCK_TRADE")
FORGING_BLOCK_ADDRESS = os.getenv("FORGING_BLOCK_ADDRESS")

MAIL = os.getenv("MAIL")
PASS = os.getenv("PASS")

bot = telebot.TeleBot(TOKEN, threaded=True)

import importdir
importdir.do("handlers", globals())
