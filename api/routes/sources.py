from config import *


with app.app_context():

    users = db.users.find({})
    trades = db.trades.find({})
    disputes = db.disputes.find({})
    chats = db.chats.find({})
