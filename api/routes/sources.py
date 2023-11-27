from config import *
from database import User, Trade, Dispute, Chat


with app.app_context():

    users = prisma.user.find_many()
    trades = prisma.trade.find_many()
    disputes = prisma.dispute.find_many()
    chats = prisma.chat.find_many()
