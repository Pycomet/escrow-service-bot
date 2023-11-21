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

from alembic.config import Config
from pathlib import Path

config = Config(Path(__file__).parent / "alembic.ini")

DEBUG = False

# Configuration variable
TOKEN = os.getenv("TOKEN")

WEBHOOK_MODE = os.getenv("WEBHOOK_MODE")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

ADMIN_ID = int(os.getenv("ADMIN_ID"))

BTCPAY_URL = os.getenv("BTCPAY_URL")
BTCPAY_API_KEY = os.getenv("BTCPAY_API_KEY")
BTCPAY_STORE_ID = os.getenv("BTCPAY_STORE_ID")

bot = telebot.TeleBot(TOKEN, threaded=True, num_threads=5)


Base = declarative_base()
engine = create_engine(
    os.getenv("DATABASE_URL"),
    echo=False)

# import importdir
# importdir.do("handlers", globals())

# from handlers import *
