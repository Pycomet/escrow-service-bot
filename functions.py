from config import *
from model import User, Trade, Dispute, Affiliate, session

import random
import string
from datetime import datetime
import cryptocompare

client = Client(API_KEY, API_SECRET)
accounts = client.get_accounts()

eth_account = accounts.data[4]
btc_account = accounts.data[6]
ltc_account = accounts.data[1]
xrp_account = accounts.data[2]
bch_account = accounts.data[5]

def get_user(msg):
    "Returns or creates a new user"

    chat = msg.message.chat.id
    id = msg.from_user.id
    
    user = session.query(User).filter_by(id=id).first()
    if user:
        return user
    else:
        user = User(id=id, chat=chat)
        session.add(user)
        session.commit()
        return user

def get_received_msg(msg):
    "Delete This Message"
    message_id = msg.message_id
    chat = msg.chat
    return chat, message_id

def get_coin_price(coin_code, currency_code):
    """
    Returning the current btc/eth price for specified currency
    """
    data = cryptocompare.get_price(coin_code, currency_code)
    return data[coin_code][currency_code]


def generate_id():
    "Return unique id"
    u_id = ""
    
    lower_case = string.ascii_lowercase
    upper_case = string.ascii_uppercase
    digits = string.digits

    option = lower_case + upper_case + digits

    for i in range(10):
        u_id += str(random.choice(option))

    return u_id

def get_trade(id):
    "Return the trade"
    try:
        trade = session.query(Trade).filter(Trade.id == id).first()
        return trade

    except:
        return "Not Found"

def get_recent_trade(user):
    """
    Return a trade matching a seller
    """
    trades = session.query(Trade).filter(Trade.seller == user.id)
    if trades.count() != 0:
        dates = [trade.updated_at for trade in trades]
        position = dates.index(max(dates))

        return trades[position]
    
    else:
        trades = session.query(Trade).filter(Trade.buyer == user.id)

        dates = [trade.updated_at for trade in trades]
        position = dates.index(max(dates))

        return trades[position]

def create_affiliate(user, id):
    "Return a newly created affilate object"
    check = Affiliate().check_affiliate(id)

    if check == None:
        affiliate = Affiliate(
            id = id,
            admin = user,
        )
        session.add(affiliate)
        session.commit()
        return affiliate
    else:
        return "Already Exists"

def get_affiliate(id):
    "Returns affiliate"
    affiliate = Affiliate().check_affiliate(id)

    if affiliate != None:
        return affiliate
    else:
        return None

def add_affiliate_btc(id, wallet):
    affiliate = session.query(Affiliate).filter_by(id=id).first()
    affiliate.btc_wallet = wallet
    session.add(affiliate)

def add_affiliate_eth(id, wallet):
    affiliate = session.query(Affiliate).filter_by(id=id).first()
    affiliate.eth_wallet = wallet
    session.add(affiliate)
    # session.commit()

def add_affiliate_ltc(id, wallet):
    affiliate = session.query(Affiliate).filter_by(id=id).first()
    affiliate.ltc_wallet = wallet
    session.add(affiliate)

def add_affiliate_xrp(id, wallet):
    affiliate = session.query(Affiliate).filter_by(id=id).first()
    affiliate.xrp_wallet = wallet
    session.add(affiliate)

def add_affiliate_bch(id, wallet):
    affiliate = session.query(Affiliate).filter_by(id=id).first()
    affiliate.bch_wallet = wallet
    session.add(affiliate)
    session.commit()


def open_new_trade(user, currency):
    """
    Returns a new trade
    """
    user = get_user(msg=user)

    affiliate = get_affiliate(user.chat)
    if affiliate != None:
        affiliate = affiliate.id

    trade = Trade(
        id =  generate_id(),
        seller = user.id,
        currency = currency,
        payment_status = False,
        created_at = str(datetime.now()),
        updated_at = str(datetime.now()),
        is_open = True,
        affiliate_id = affiliate,
        )

    session.add(trade)
    session.commit()


def add_coin(user, coin):
    """
    Update trade instance with coin preference
    """
    trade = get_recent_trade(user)
    trade.coin = str(coin)

    if coin == "BTC":
        trade.receive_address_id = btc_account.create_address().id
    elif coin == "ETH":
        trade.receive_address_id = eth_account.create_address().id
    elif coin == "LTC":
        trade.receive_address_id = ltc_account.create_address().id
    elif coin == "XRP":
        trade.receive_address_id = xrp_account.create_address().id
    elif coin == "BCH":
        trade.receive_address_id = bch_account.create_address().id
    else:
        pass

    session.add(trade)

def add_price(user, price):
    """
    Update trade instance with price of service
    """
    trade = get_recent_trade(user)
    trade.price = float(price)
    session.add(trade)

def add_wallet(user, address):
    """
    Update trade instance with wallet for seller
    """
    trade = get_recent_trade(user)
    trade.wallet = str(address)
    trade.updated_at = str(datetime.now())
    session.add(trade)
    session.commit()

def add_buyer(trade, buyer):
    "Add Buyer To Trade"
    trade.buyer = buyer.id
    trade.updated_at = str(datetime.now())
    session.add(trade)
    session.commit()

def get_receive_address(trade):
    "Return the receive address"

    if trade.coin == "BTC":
        wallet = btc_account.get_address(trade.receive_address_id).address
    
    elif trade.coin == "ETH":
        wallet = eth_account.get_address(trade.receive_address_id).address

    elif trade.coin == "LTC":
        wallet = ltc_account.get_address(trade.receive_address_id).address

    elif trade.coin == "XRP":
        wallet = xrp_account.get_address(trade.receive_address_id).address

    elif trade.coin == "BCH":
        wallet = bch_account.get_address(trade.receive_address_id).address

    else:
        return "ERROR!"

    return wallet

def delete_trade(trade_id):
    "Delete Trade"
    trade = session.query(Trade).filter(Trade.id == trade_id).delete()
    
    if trade == None:
        return "Not Found!"
    else:
        session.commit()
        return "Complete!"


def check_trade(user, trade_id):
    "Return trade info"

    trade = session.query(Trade).filter(Trade.id == trade_id).first()
    if trade == None:

        return "Not Found"

    elif trade.buyer == trade.seller:

        return "Not Permitted"
    
    else:
        add_buyer(
            trade=trade,
            buyer=user
        )
        return trade


def get_trades(user):
    "Retrun list of trades the user is in"
    
    sells = session.query(Trade).filter(Trade.seller == user.id).all()
    buys = session.query(Trade).filter(Trade.buyer == user.id).all()

    return sells, buys

def confirm_pay(trade):
    "Confirm Payment"
    trade.payment_status = True
    trade.updated_at = str(datetime.now())
    session.add(trade)
    session.commit()

def check_payment(trade, hash):
    "Returns Status Of Payment"

    try:
        tx = blockexplorer.get_tx(hash)

        #Check if it is the same
        if trade.coin == "BTC":
            transaction_hash = btc_account.get_address_transactions(trade.receive_address_id).data[-1].network.hash
        elif trade.coin == "ETH":
            transaction_hash = eth_account.get_address_transactions(trade.receive_address_id).data[-1].network.hash
        elif trade.coin == "LTC":
            transaction_hash = ltc_account.get_address_transactions(trade.receive_address_id).data[-1].network.hash
        elif trade.coin == "XRP":
            transaction_hash = xrp_account.get_address_transactions(trade.receive_address_id).data[-1].network.hash
        elif trade.coin == "BCH":
            transaction_hash = bch_account.get_address_transactions(trade.receive_address_id).data[-1].network.hash
        else:
            transaction_hash = ""

        if transaction_hash == tx.hash:
            confirm_pay(trade)
            return "Approved"

    except:
        return "Pending"

def pay_funds_to_seller(trade):
    "Calculate Fees And Send Funds To Seller"
    affiliate = Affiliate().check_affiliate(trade.affiliate_id)
    
    coin_price = get_coin_price(
        coin_code=trade.coin,
        currency_code=trade.currency
    )

    value = float(trade.price)/float(coin_price)

    service_charge = 0.01 * float(value)
    fees = 0.0149 * value

    pay_price = float(value) - service_charge + fees

    price = "%.4f" % pay_price

    a_price = "%.4f" % service_charge # Affiliate pay
    if trade.coin == "BTC":

        btc_account.send_money(
            to = trade.wallet,
            amount = str(price),
            currency = "BTC"
        )
        if affiliate != None:

            btc_account.send_money(
                to = affiliate.btc_wallet,
                amount = str(a_price),
                currency = "BTC"
            )   

        close_trade(trade)

    elif trade.coin == "ETH":
        eth_account.send_money(
            to = trade.wallet,
            amount = str(price),
            currency = "ETH",
        )

        if affiliate != None:
    
            eth_account.send_money(
                to = affiliate.eth_wallet,
                amount = str(a_price),
                currency = "ETH"
            )

        close_trade(trade)

    elif trade.coin == "LTC":
        ltc_account.send_money(
            to = trade.wallet,
            amount = str(price),
            currency = "LTC",
        )

        if affiliate != None:
    
            ltc_account.send_money(
                to = affiliate.ltc_wallet,
                amount = str(a_price),
                currency = "LTC"
            )

        close_trade(trade)

    elif trade.coin == "XRP":
        xrp_account.send_money(
            to = trade.wallet,
            amount = str(price),
            currency = "XRP",
        )

        if affiliate != None:
    
            xrp_account.send_money(
                to = affiliate.xrp_wallet,
                amount = str(a_price),
                currency = "XRP"
            )

        close_trade(trade)

    elif trade.coin == "BCH":
        bch_account.send_money(
            to = trade.wallet,
            amount = str(price),
            currency = "BCH",
        )

        if affiliate != None:
    
            bch_account.send_money(
                to = affiliate.bch_wallet,
                amount = str(a_price),
                currency = "BCH"
            )

        close_trade(trade)

    else:
        pass


def close_trade(trade):
    "Closing The Trade"
    trade.is_open = False
    trade.updated_at = str(datetime.now())
    session.add(trade)
    session.commit()


def pay_to_buyer(trade, wallet):
    "Send Funds To Buyer"
    affiliate = Affiliate().check_affiliate(trade.affiliate_id)

    coin_price = get_coin_price(
        coin_code=trade.coin,
        currency_code=trade.currency
    )

    value = float(trade.price)/float(coin_price)

    service_charge = 0.01 * float(value)
    fees = 0.0149 * value

    pay_price = float(value) - service_charge + fees

    price = "%.4f" % pay_price

    a_price = "%.4f" % service_charge # Affiliate pay

    if trade.coin == "BTC":
        btc_account.send_money(
            to = wallet,
            amount = str(price),
            currency = "BTC"
        )

        if affiliate != None:
    
            btc_account.send_money(
                to = affiliate.btc_wallet,
                amount = str(a_price),
                currency = "BTC"
            )   
        close_trade(trade)

    elif trade.coin == "ETH":
        eth_account.send_money(
            to = wallet,
            amount = str(price),
            currency = "ETH",
        )

        if affiliate != None:
        
            eth_account.send_money(
                to = affiliate.eth_wallet,
                amount = str(a_price),
                currency = "ETH"
            )
        close_trade(trade)

    elif trade.coion == "LTC":
        ltc_account.send_money(
            to = trade.wallet,
            amount = str(price),
            currency = "LTC",
        )

        if affiliate != None:
    
            ltc_account.send_money(
                to = affiliate.ltc_wallet,
                amount = str(a_price),
                currency = "LTC"
            )

        close_trade(trade)

    elif trade.coion == "XRP":
        xrp_account.send_money(
            to = trade.wallet,
            amount = str(price),
            currency = "XRP",
        )

        if affiliate != None:
    
            xrp_account.send_money(
                to = affiliate.xrp_wallet,
                amount = str(a_price),
                currency = "XRP"
            )

        close_trade(trade)

    elif trade.coion == "BCH":
        bch_account.send_money(
            to = trade.wallet,
            amount = str(price),
            currency = "BCH",
        )

        if affiliate != None:
    
            bch_account.send_money(
                to = affiliate.bch_wallet,
                amount = str(a_price),
                currency = "BCH"
            )

        close_trade(trade)

    else:
        pass




#######################DISPUTE############################
def get_dispute(id):
    "Returns the dispute on attached to this user"

    user_id = id
    dispute = session.query(Dispute).filter(Dispute.user == user_id)
    if dispute == None:
        return "No Dispute"

    elif dispute.count() >= 1:
        return dispute[-1]
    else:
        return dispute

def get_dispute_by_id(id):
    "Return The Dispute By ID"
    dispute = session.query(Dispute).filter(Dispute.id == id).first()
    return dispute


def create_dispute(user, trade):
    "Returns a newly created disput to a trade"

    dispute = Dispute(
        id = generate_id(),
        user = user.id,
        created_on = str(datetime.now()),
        trade = trade,
    )
    trade.dispute.append(dispute)

    if user.id == trade.seller and user.id == trade.buyer:
        dispute.is_buyer = True
        dispute.is_seller = True

    elif user.id != trade.seller and user.id == trade.buyer:
        dispute.is_buyer = True
        dispute.is_seller = False       

    elif user.id == trade.seller and user.id != trade.buyer:
        dispute.is_buyer = False
        dispute.is_seller = True

    else:
        dispute.is_seller = False
        dispute.is_buyer = False

    session.add(dispute)
    session.add(trade)
    session.commit()

    return dispute

def add_complaint(dispute, text):
    "Add Complaint Message"

    dispute.complaint = text
    session.add(dispute)
    session.commit()