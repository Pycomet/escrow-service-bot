import os
import telebot
from telebot import types
import emoji
from flask import Flask, Blueprint, make_response, request, render_template
from flask_restful import Api, Resource

# from flask_sqlalchemy import SQLAlchemy
# from sqlalchemy import cast, Column, Integer, String, ForeignKey, Boolean, DateTime
# from sqlalchemy import create_engine
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker, relationship, backref, joinedload
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


DEBUG = False

# Configuration variable
TOKEN = os.getenv("TOKEN")

WEBHOOK_MODE = os.getenv("WEBHOOK_MODE")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

ADMIN_ID = int(os.getenv("ADMIN_ID"))

BTCPAY_URL = os.getenv("BTCPAY_URL")
BTCPAY_API_KEY = os.getenv("BTCPAY_API_KEY")
BTCPAY_STORE_ID = os.getenv("BTCPAY_STORE_ID")

DATABASE_URL = os.getenv("DATABASE_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME")

bot = telebot.TeleBot(TOKEN, threaded=True)

# Initialize application
app = Flask(__name__)

client = MongoClient(DATABASE_URL)
db = client[DATABASE_NAME]
