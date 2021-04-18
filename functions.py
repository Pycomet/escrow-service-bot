from config import *
from model import User, Trade, Dispute, Affiliate

import random
import string
from datetime import datetime
import cryptocompare

client = Client(API_KEY, API_SECRET)
accounts = client.get_accounts()


def send_invoice(trade):
    """
    Create invoice and extract url
    """
    agent = get_agent(trade)
    u_id = client.create_invoice(trade, agent)

    trade.invoice = u_id
    session.add(trade)
    session.commit()

    url = client.get_payment_url(trade, agent)
    return url



def get_user(msg):
    "Returns or creates a new user"

    chat = msg.message.chat.id
    id = msg.from_user.id

    user = session.query(User).filter_by(id=id).first()
    if user:
        return user
    else:
        user = User(id=id, chat=chat)
        db.session.add(user)
        db.session.commit()
        return user


def get_agent(trade):
    if trade.agent_id is not None:
        agent: Agent = session.query(Agent).filter_by(
            id=trade.agent_id).first()
        return agent
    return None


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
        trade = db.session.query(Trade).filter(Trade.id == id).first()
        return trade

    except:
        return "Not Found"


def get_recent_trade(user):
    """
    Return a trade matching a seller
    """
    trades = db.session.query(Trade).filter(Trade.seller == user['_id'])
    if trades.count() != 0:
        dates = [trade.updated_at for trade in trades]
        position = dates.index(max(dates))

        return trades[position]

    else:
        trades = db.session.query(Trade).filter(Trade.buyer == user['_id'])

        dates = [trade.updated_at for trade in trades]
        position = dates.index(max(dates))

        return trades[position]

<<<<<<< HEAD

=======
<<<<<<< HEAD
>>>>>>> 1a5cda1c (fix payout bug)
def create_affiliate(user, id):
=======

def create_affiliate(agent, id):
>>>>>>> d3be1722 (fix payout bug)
    "Return a newly created affilate object"
    check = Affiliate().check_affiliate(id)

    if check == None:
        affiliate = Affiliate(
<<<<<<< HEAD
            id=id,
            admin=user,
=======
<<<<<<< HEAD
            id = id,
            admin = user,
=======
            id=id,
            agent_id=agent.id,
            agent=agent
>>>>>>> d3be1722 (fix payout bug)
>>>>>>> 1a5cda1c (fix payout bug)
        )
        db.session.add(affiliate)
        db.session.commit()
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
    affiliate = db.session.query(Affiliate).filter_by(id=id).first()
    affiliate.btc_wallet = wallet
    db.session.add(affiliate)


def add_affiliate_eth(id, wallet):
    affiliate = db.session.query(Affiliate).filter_by(id=id).first()
    affiliate.eth_wallet = wallet
    db.session.add(affiliate)
    # db.session.commit()


def add_affiliate_ltc(id, wallet):
    affiliate = db.session.query(Affiliate).filter_by(id=id).first()
    affiliate.ltc_wallet = wallet
    db.session.add(affiliate)


def add_affiliate_xrp(id, wallet):
    affiliate = db.session.query(Affiliate).filter_by(id=id).first()
    affiliate.xrp_wallet = wallet
    db.session.add(affiliate)


def add_affiliate_bch(id, wallet):
    affiliate = db.session.query(Affiliate).filter_by(id=id).first()
    affiliate.bch_wallet = wallet
    db.session.add(affiliate)
    db.session.commit()

def open_new_trade(user, currency):
    """
    Returns a new trade
    """
    user = get_user(msg=user)

    affiliate = get_affiliate(user.chat)
    if affiliate != None:
        affiliate = affiliate.id

    trade = Trade(
<<<<<<< HEAD
        id=generate_id(),
        seller=user['_id'],
=======
<<<<<<< HEAD
        id =  generate_id(),
        seller = user.id,
        currency = currency,
        payment_status = False,
        created_at = str(datetime.now()),
        updated_at = str(datetime.now()),
        is_open = True,
        affiliate_id = affiliate,
        )
=======
        id=generate_id(),
        seller=user.id,
>>>>>>> 1a5cda1c (fix payout bug)
        currency=currency,
        payment_status=False,
        created_at=str(datetime.now()),
        updated_at=str(datetime.now()),
        is_open=True,
<<<<<<< HEAD
        affiliate_id=affiliate,
    )
=======
        agent_id=None,
        address=FORGING_BLOCK_ADDRESS,
        invoice=""
    )
>>>>>>> d3be1722 (fix payout bug)
>>>>>>> 1a5cda1c (fix payout bug)

    db.session.add(trade)
    db.session.commit()



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

    db.session.add(trade)



def add_price(user, price):
    """
    Update trade instance with price of service
    """
    trade = get_recent_trade(user)
    trade.price = float(price)
    db.session.add(trade)



def add_wallet(user, address):
    """
    Update trade instance with wallet for seller
    """
    trade = get_recent_trade(user)
    trade.wallet = str(address)
    trade.updated_at = str(datetime.now())
    db.session.add(trade)
    db.session.commit()



def add_buyer(trade, buyer):
    "Add Buyer To Trade"
    trade.buyer = buyer.id
    trade.updated_at = str(datetime.now())
    db.session.add(trade)
    db.session.commit()



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
<<<<<<< HEAD
    trade = db.session.query(Trade).filter(Trade.id == trade_id).delete()
=======
    trade = session.query(Trade).filter(Trade.id == trade_id).delete()
>>>>>>> 1a5cda1c (fix payout bug)

    if trade == None:
        return "Not Found!"
    else:
        db.session.commit()
        return "Complete!"

<<<<<<< HEAD
=======

def seller_delete_trade(user_id, trade_id):
    "Delete Trade"
    trade = session.query(Trade).filter_by(id=trade_id).one_or_none()

    if trade is None:
        return "Trade Not Found"
    elif trade.seller is not str(user_id):
        return "You are not authorized to take this action. Please contact support!"
    else:
        session.commit()
        return "Trade Deleted Successfully"

>>>>>>> d3be1722 (fix payout bug)

def check_trade(user, trade_id):
    "Return trade info"

<<<<<<< HEAD
    trade = db.session.query(Trade).filter(Trade.id == trade_id).first()
=======
    trade = session.query(Trade).filter(Trade.id == trade_id).first()
<<<<<<< HEAD
=======

>>>>>>> d3be1722 (fix payout bug)
>>>>>>> 1a5cda1c (fix payout bug)
    if trade == None:

        return "Not Found"

    elif trade.buyer == trade.seller:

        return "Not Permitted"

    else:
        add_buyer(trade=trade, buyer=user)
        return trade


def get_trades(user):
    "Retrun list of trades the user is in"
<<<<<<< HEAD

    sells = db.session.query(Trade).filter(Trade.seller == user['_id']).all()
    buys = db.session.query(Trade).filter(Trade.buyer == user['_id']).all()

    return sells, buys


=======
<<<<<<< HEAD
    
    sells = session.query(Trade).filter(Trade.seller == user.id).all()
=======

    sells = session.query(Trade).filter(Trade.seller == str(user.id)).all()
>>>>>>> d3be1722 (fix payout bug)
    buys = session.query(Trade).filter(Trade.buyer == user.id).all()

    return sells, buys

<<<<<<< HEAD
=======

def get_trades_report(sells: list, buys: list):
    "Return aggregated data of trades"
    purchases = len(buys)
    sales = len(sells)

    active_buys = [i for i in buys if i.is_open == False]
    active_sells = [i for i in sells if i.is_open == False]
    active = len(active_buys) + len(active_sells)

    trades = purchases + sales

    r_buys = [i for i in buys if i.dispute is not []]
    r_sells = [i for i in sells if i.dispute is not []]
    reports = len(r_buys) + len(r_sells)

    return purchases, sales, trades, active, reports


>>>>>>> d3be1722 (fix payout bug)
>>>>>>> 1a5cda1c (fix payout bug)
def confirm_pay(trade):
    "Confirm Payment"
    trade.payment_status = True
    trade.updated_at = str(datetime.now())
    db.session.add(trade)
    db.session.commit()


<<<<<<< HEAD
def check_payment(trade, hash):
=======

def check_payment(trade):
>>>>>>> d3be1722 (fix payout bug)
    "Returns Status Of Payment"

    try:
        tx = blockexplorer.get_tx(hash)

        # Check if it is the same
        if trade.coin == "BTC":
            transaction_hash = (
                btc_account.get_address_transactions(trade.receive_address_id)
                .data[-1]
                .network.hash
            )
        elif trade.coin == "ETH":
            transaction_hash = (
                eth_account.get_address_transactions(trade.receive_address_id)
                .data[-1]
                .network.hash
            )
        elif trade.coin == "LTC":
            transaction_hash = (
                ltc_account.get_address_transactions(trade.receive_address_id)
                .data[-1]
                .network.hash
            )
        elif trade.coin == "XRP":
            transaction_hash = (
                xrp_account.get_address_transactions(trade.receive_address_id)
                .data[-1]
                .network.hash
            )
        elif trade.coin == "BCH":
            transaction_hash = (
                bch_account.get_address_transactions(trade.receive_address_id)
                .data[-1]
                .network.hash
            )
        else:
            transaction_hash = ""

        if transaction_hash == tx.hash:
            confirm_pay(trade)
            return "Approved"

    except:
        return "Pending"

<<<<<<< HEAD

def pay_funds_to_seller(trade):
    "Calculate Fees And Send Funds To Seller"
    affiliate = Affiliate().check_affiliate(trade.affiliate_id)
=======
<<<<<<< HEAD
def pay_funds_to_seller(trade):
    "Calculate Fees And Send Funds To Seller"
    affiliate = Affiliate().check_affiliate(trade.affiliate_id)
    
=======

def pay_funds_to_seller(trade: Trade):
    "Calculate Fees And Send Funds To Seller"
    # affiliate = Affiliate().check_affiliate(trade.affiliate_id)

    # GET TRADE BALANCE
>>>>>>> d3be1722 (fix payout bug)
    coin_price = get_coin_price(
        coin_code=trade.coin,
        currency_code=trade.currency
    )
<<<<<<< HEAD
>>>>>>> 1a5cda1c (fix payout bug)

    coin_price = get_coin_price(coin_code=trade.coin, currency_code=trade.currency)

    value = float(trade.price) / float(coin_price)

=======

    value = float(trade.price)/float(coin_price)
    # CONDITION ON COIN ATTACH TO TRADE

>>>>>>> d3be1722 (fix payout bug)
    service_charge = 0.01 * float(value)
    fees = 0.0149 * value

    pay_price = float(value) - service_charge + fees

    price = "%.4f" % pay_price

<<<<<<< HEAD
    a_price = "%.4f" % service_charge  # Affiliate pay
    if trade.coin == "BTC":

        btc_account.send_money(to=trade.wallet, amount=str(price), currency="BTC")
        if affiliate != None:

            btc_account.send_money(
                to=affiliate.btc_wallet, amount=str(a_price), currency="BTC"
            )
=======
<<<<<<< HEAD
    a_price = "%.4f" % service_charge # Affiliate pay
    if trade.coin == "BTC":

        btc_account.send_money(
            to = trade.wallet,
            amount = str(price),
            currency = "BTC"
=======
    a_price = "%.4f" % service_charge  # Affiliate pay
    if trade.coin == "BTC":

        btc_account.send_money(
            to=trade.wallet,
            amount=str(price),
            currency="BTC"
>>>>>>> d3be1722 (fix payout bug)
        )
        if affiliate != None:

            btc_account.send_money(
<<<<<<< HEAD
                to = affiliate.btc_wallet,
                amount = str(a_price),
                currency = "BTC"
            )   
>>>>>>> 1a5cda1c (fix payout bug)

        close_trade(trade)

    elif trade.coin == "ETH":
        eth_account.send_money(
            to=trade.wallet,
            amount=str(price),
            currency="ETH",
        )

        if affiliate != None:

            eth_account.send_money(
<<<<<<< HEAD
                to=affiliate.eth_wallet, amount=str(a_price), currency="ETH"
=======
                to = affiliate.eth_wallet,
                amount = str(a_price),
                currency = "ETH"
=======
                to=affiliate.btc_wallet,
                amount=str(a_price),
                currency="BTC"
>>>>>>> d3be1722 (fix payout bug)
>>>>>>> 1a5cda1c (fix payout bug)
            )

        close_trade(trade)

    elif trade.coin == "LTC":
        ltc_account.send_money(
<<<<<<< HEAD
            to=trade.wallet,
            amount=str(price),
            currency="LTC",
=======
<<<<<<< HEAD
            to = trade.wallet,
            amount = str(price),
            currency = "LTC",
>>>>>>> 1a5cda1c (fix payout bug)
        )

        if affiliate != None:

            ltc_account.send_money(
<<<<<<< HEAD
                to=affiliate.ltc_wallet, amount=str(a_price), currency="LTC"
=======
                to = affiliate.ltc_wallet,
                amount = str(a_price),
                currency = "LTC"
=======
            to=trade.wallet,
            amount=str(price),
            currency="LTC",
        )

        if affiliate != None:

            ltc_account.send_money(
                to=affiliate.ltc_wallet,
                amount=str(a_price),
                currency="LTC"
>>>>>>> d3be1722 (fix payout bug)
>>>>>>> 1a5cda1c (fix payout bug)
            )

        close_trade(trade)

    elif trade.coin == "XRP":
        xrp_account.send_money(
<<<<<<< HEAD
            to=trade.wallet,
            amount=str(price),
            currency="XRP",
=======
<<<<<<< HEAD
            to = trade.wallet,
            amount = str(price),
            currency = "XRP",
>>>>>>> 1a5cda1c (fix payout bug)
        )

        if affiliate != None:

            xrp_account.send_money(
<<<<<<< HEAD
                to=affiliate.xrp_wallet, amount=str(a_price), currency="XRP"
=======
                to = affiliate.xrp_wallet,
                amount = str(a_price),
                currency = "XRP"
=======
            to=trade.wallet,
            amount=str(price),
            currency="XRP",
        )

        if affiliate != None:

            xrp_account.send_money(
                to=affiliate.xrp_wallet,
                amount=str(a_price),
                currency="XRP"
>>>>>>> d3be1722 (fix payout bug)
>>>>>>> 1a5cda1c (fix payout bug)
            )

        close_trade(trade)

    elif trade.coin == "BCH":
        bch_account.send_money(
<<<<<<< HEAD
            to=trade.wallet,
            amount=str(price),
            currency="BCH",
=======
<<<<<<< HEAD
            to = trade.wallet,
            amount = str(price),
            currency = "BCH",
>>>>>>> 1a5cda1c (fix payout bug)
        )

        if affiliate != None:

            bch_account.send_money(
<<<<<<< HEAD
                to=affiliate.bch_wallet, amount=str(a_price), currency="BCH"
=======
                to = affiliate.bch_wallet,
                amount = str(a_price),
                currency = "BCH"
=======
            to=trade.wallet,
            amount=str(price),
            currency="BCH",
        )

        if affiliate != None:

            bch_account.send_money(
                to=affiliate.bch_wallet,
                amount=str(a_price),
                currency="BCH"
>>>>>>> d3be1722 (fix payout bug)
>>>>>>> 1a5cda1c (fix payout bug)
            )

        close_trade(trade)
<<<<<<< HEAD

<<<<<<< HEAD
    else:
        pass
=======

>>>>>> > 13883c85(fix payout bug)
   else:
=======
    else:
>>>>>>> 9a6a6367 (new debug mode)

        # SEND A MESSAGE TO ADMIN TO PAY MANUALLY
        return None, payout_price

    return "Done", None
>>>>>>> d3be1722 (fix payout bug)


def close_trade(trade):
    "Closing The Trade"
    trade.is_open = False
    trade.updated_at = str(datetime.now())
    db.session.add(trade)
    db.session.commit()


def pay_to_buyer(trade, wallet):
    "Send Funds To Buyer"
    affiliate = Affiliate().check_affiliate(trade.affiliate_id)

    coin_price = get_coin_price(coin_code=trade.coin, currency_code=trade.currency)

    value = float(trade.price) / float(coin_price)

<<<<<<< HEAD
    service_charge = 0.01 * float(value)
    fees = 0.0149 * value

    pay_price = float(value) - service_charge + fees

    price = "%.4f" % pay_price

    a_price = "%.4f" % service_charge  # Affiliate pay

    if trade.coin == "BTC":
        btc_account.send_money(to=wallet, amount=str(price), currency="BTC")

        if affiliate != None:

            btc_account.send_money(
                to=affiliate.btc_wallet, amount=str(a_price), currency="BTC"
            )
        close_trade(trade)

    elif trade.coin == "ETH":
        eth_account.send_money(
            to=wallet,
            amount=str(price),
            currency="ETH",
        )

        if affiliate != None:

            eth_account.send_money(
                to=affiliate.eth_wallet, amount=str(a_price), currency="ETH"
            )
        close_trade(trade)

    elif trade.coion == "LTC":
        ltc_account.send_money(
            to=trade.wallet,
            amount=str(price),
            currency="LTC",
        )

        if affiliate != None:

            ltc_account.send_money(
                to=affiliate.ltc_wallet, amount=str(a_price), currency="LTC"
            )

        close_trade(trade)

    elif trade.coion == "XRP":
        xrp_account.send_money(
            to=trade.wallet,
            amount=str(price),
            currency="XRP",
        )

        if affiliate != None:

            xrp_account.send_money(
                to=affiliate.xrp_wallet, amount=str(a_price), currency="XRP"
            )

        close_trade(trade)

    elif trade.coion == "BCH":
        bch_account.send_money(
            to=trade.wallet,
            amount=str(price),
            currency="BCH",
        )

        if affiliate != None:

            bch_account.send_money(
                to=affiliate.bch_wallet, amount=str(a_price), currency="BCH"
            )

        close_trade(trade)

    else:
        pass


<<<<<<< HEAD
=======
=======
    service_charge = 0.05 * value
    payout_price = float(value) - float(service_charge)

    if trade.agent_id != None:

        agent = get_agent(trade)

        if trade.coin == "BTC":
            txid = client.send_btc(
                mnemonic=agent.mnemonic,
                sender=agent.btc_address,
                amount=float(payout_price),
                address=wallet
            )
            close_trade(trade)

            return txid, None

        elif trade.currency == "ETH":

            # SEND TO ETHEREUM WALLET
            pass

        else:
            pass

    else:

        # SEND A MESSAGE TO ADMIN TO PAY MANUALLY
        return None, payout_price

    return "Done", None
>>>>>>> d3be1722 (fix payout bug)


>>>>>>> 1a5cda1c (fix payout bug)
#######################DISPUTE############################
def get_dispute(id):
    "Returns the dispute on attached to this user"

    user_id = id
    dispute = db.session.query(Dispute).filter(Dispute.user == user_id)
    if dispute == None:
        return "No Dispute"

    elif dispute.count() >= 1:
        return dispute[-1]
    else:
        return dispute


def get_dispute_by_id(id):
    "Return The Dispute By ID"
    dispute = db.session.query(Dispute).filter(Dispute.id == id).first()
    return dispute


def create_dispute(user, trade):
    "Returns a newly created disput to a trade"

    dispute = Dispute(
<<<<<<< HEAD
        id=generate_id(),
        user=user['_id'],
        created_on=str(datetime.now()),
        trade=trade,
=======
        id= generate_id(),
        user= user.id,
        created_on= str(datetime.now()),
        trade= trade,
>>>>>>> 1a5cda1c (fix payout bug)
    )
    trade.dispute.append(dispute)

    if user['_id'] == trade.seller and user['_id'] == trade.buyer:
        dispute.is_buyer = True
        dispute.is_seller = True

    elif user['_id'] != trade.seller and user['_id'] == trade.buyer:
        dispute.is_buyer = True
        dispute.is_seller = False

<<<<<<< HEAD
    elif user['_id'] == trade.seller and user['_id'] != trade.buyer:
=======
<<<<<<< HEAD
    elif user.id == trade.seller and user.id != trade.buyer:
=======
    elif str(user.id) == trade.seller and user.id != trade.buyer:
>>>>>>> d3be1722 (fix payout bug)
>>>>>>> 1a5cda1c (fix payout bug)
        dispute.is_buyer = False
        dispute.is_seller = True

    else:
        dispute.is_seller = False
        dispute.is_buyer = False

    db.session.add(dispute)
    db.session.add(trade)
    db.session.commit()

    return dispute


def add_complaint(dispute, text):
    "Add Complaint Message"

    dispute.complaint = text
<<<<<<< HEAD
    db.session.add(dispute)
    db.session.commit()
=======
    session.add(dispute)
<<<<<<< HEAD
    session.commit()
=======
    session.commit()


def verify_user(user):
    user.verified

#######################AGENT FUNCTIONS############################


class AgentAction(object):

    def __init__(self) -> None:
        super().__init__()

    def check_agent(self, id: int) -> bool:
        agent = session.query(Agent).filter_by(id=id).first()
        if agent is None:
            return False, None
        else:
            return True, agent

    def create_agent(cls, user_id) -> Agent:
        "Creates agent entity"
        agent = session.query(Agent).filter_by(id=user_id).first()

        if agent is None:

            # Create wallet and store
            mnemonic, address = client.create_wallet()
            xpub = client.get_xpub()
            trade, token, store = client.create_store(name=f'{xpub}-{address}')
            client.connect_store()

            # FETCH ETH ADDRESS

            agent = Agent(
                id=user_id,
                mnemonic=mnemonic,
                xpub=xpub,
                trade=trade,
                token=token,
                store=store,
                btc_address=address,
                eth_address=""
            )

            session.add(agent)
            session.commit()

        return agent

    def create_trade(self, id, price, wallet) -> Trade:
        "Create a new trade and post to group"
        agent = self.create_agent(id)

        trade = Trade(
            id= generate_id(),
            payment_status= False,
            created_at= str(datetime.now()),
            is_open= True,
            agent_id= agent.id,
            seller= agent.affiliate[0].id,
            price= price,
            currency= "USD",
            coin= "BTC",
            wallet=  wallet,
            address= agent.btc_address,
            invoice= ""
        )

        trade = self.get_invoice(trade, agent)

        session.add(trade)
        session.commit()
        return trade

    def get_invoice(self, trade, agent):
        "Cretae and add the invoice to the trade"
        u_id = client.create_invoice(trade, agent)
        trade.invoice = u_id
        return trade

    def get_balance(self, agent) -> float:
        "Fetch bitcoin and ethereum balance"
        # import pdb; pdb.set_trace()
        self.btc = client.get_btc_balance(agent.btc_address)

        # self.eth = client.get_eth_balance(agent.eth_address)
        self.eth = 0.0

        if self.btc == "Failed":
            return None, None

        else:
            return float(self.btc), float(self.eth)

    def get_trades(self, id) -> list:
        "Ftech All Agent Related Trade"
        all_trades = session.query(Trade).all()
        trades = []
        [trades.append(each)
                       for each in all_trades if int(each.agent_id) == id]
        # import pdb; pdb.set_trace()
        return trades

    def pay_btc(self, agent, price, wallet):
        try:
            txid = client.send_btc(
                mnemonic=agent.mnemonic,
                sender=agent.btc_address,
                amount=price,
                address=wallet
            )
            return txid

        except Exception as e:
            return None
>>>>>>> d3be1722 (fix payout bug)
>>>>>>> 1a5cda1c (fix payout bug)
