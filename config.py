import os
import telebot
from telebot import types
import emoji
from flask import Flask, Blueprint, make_response, request, render_template
from flask_restful import Api, Resource
from sqlalchemy import cast, Column, Integer, String, ForeignKey, Boolean, DateTime
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref
import random
import requests
import string
from datetime import datetime
import cryptocompare

from dotenv import load_dotenv
load_dotenv()

# Configuration variable
TOKEN = os.getenv("TOKEN")

ADMIN_ID = int(os.getenv("ADMIN_ID"))

ADMIN = os.getenv("ADMIN")
SERVER_URL = os.getenv("SERVER_URL")


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


Base = declarative_base()
engine = create_engine(
    os.getenv("DATABASE_URL"),
    echo=False)

# import importdir
# importdir.do("handlers", globals())

# from handlers import *
