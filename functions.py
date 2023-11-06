from config import *
from source import BitcoinApi
from model import Agent, User, Trade, Dispute, Affiliate, session

import random
import requests
import string
from datetime import datetime
import cryptocompare

client = BitcoinApi()

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
    id = str(msg.from_user.id)
    
    user = session.query(User).filter_by(id=id).first()
    if user:
        return user
    else:
        user = User(id=id, chat=chat, verified=False)
        session.add(user)
        session.commit()
        return user
    
def get_agent(trade):
    if trade.agent_id is not None:
        agent: Agent = session.query(Agent).filter_by(id=trade.agent_id).first()
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
        trade = session.query(Trade).filter(Trade.id == id).first()
        return trade

    except:
        return "Not Found"

def get_recent_trade(user):
    """
    Return a trade matching a seller
    """
    trades = session.query(Trade).filter(Trade.seller == str(user.id))
    if trades.count() != 0:
        dates = [trade.updated_at for trade in trades]
        position = dates.index(max(dates))

        return trades[position]
    
    else:
        trades = session.query(Trade).filter(Trade.buyer == user.id)

        dates = [trade.updated_at for trade in trades]
        position = dates.index(max(dates))

        return trades[position]

def create_affiliate(agent, id):
    "Return a newly created affilate object"
    check = Affiliate().check_affiliate(id)

    if check == None:
        # import pdb; pdb.set_trace()
        affiliate = Affiliate(
            id = id,
            agent_id = agent.id,
            agent = agent
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



def open_new_trade(user, currency):
    """
    Returns a new trade without Agent
    """
    user = get_user(msg=user)

    affiliate = get_affiliate(user.chat)
    # import pdb; pdb.set_trace()
    if affiliate != None:
        affiliate = affiliate.id

    # Create bot trade
    trade = Trade(
        id =  generate_id(),
        seller = user.id,
        currency = currency,
        payment_status = False,
        created_at = str(datetime.now()),
        updated_at = str(datetime.now()),
        is_open = True,
        agent_id = None,
        address=FORGING_BLOCK_ADDRESS,
        invoice=""
        )

    session.add(trade)
    session.commit()

    return "Trade Created!"

def add_coin(user, coin):
    """
    Update trade instance with coin preference
    """
    trade = get_recent_trade(user)
    trade.coin = str(coin)

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
    return trade.address

def delete_trade(trade_id):
    "Delete Trade"
    trade = session.query(Trade).filter(Trade.id == trade_id).delete()
    
    if trade == None:
        return "Not Found!"
    else:
        session.commit()
        return "Complete!"

def seller_delete_trade(user_id, trade_id):
    "Delete Trade"
    trade = session.query(Trade).filter_by(id= trade_id).one_or_none()

    if trade is None:
        return "Trade Not Found"
    elif trade.seller is not str(user_id): 
        return "You are not authorized to take this action. Please contact support!"
    else:
        session.commit()
        return "Trade Deleted Successfully"


def check_trade(user, trade_id):
    "Return trade info"

    trade = session.query(Trade).filter(Trade.id == trade_id).first()
    
    if trade == None:

        return "Not Found"

    elif str(trade.buyer) == trade.seller:

        return "Not Permitted"
    
    else:
        add_buyer(
            trade=trade,
            buyer=user
        )
        return trade


def get_trades(user):
    "Retrun list of trades the user is in"
    
    sells = session.query(Trade).filter(Trade.seller == str(user.id)).all()
    buys = session.query(Trade).filter(Trade.buyer == user.id).all()

    return sells, buys

def get_trades_report(sells:list, buys:list):
    "Return aggregated data of trades"
    purchases = len(buys)
    sales = len(sells)
    
    active_buys = [ i for i in buys if i.is_open == False ]
    active_sells = [ i for i in sells if i.is_open == False ]
    active = len(active_buys) + len(active_sells)

    trades = purchases + sales

    r_buys = [ i for i in buys if i.dispute is not [] ]
    r_sells = [ i for i in sells if i.dispute is not [] ]
    reports = len(r_buys) + len(r_sells)

    return purchases, sales, trades, active, reports

def confirm_pay(trade):
    "Confirm Payment"
    trade.payment_status = True
    trade.updated_at = str(datetime.now())
    session.add(trade)
    session.commit()

def check_payment(trade):
    "Returns Status Of Payment"
    agent = get_agent(trade)
    status = client.check_status(trade, agent)
    # import pdb; pdb.set_trace()

    if status in ('confirmed', 'paid', 'completed', 'complete'):
        trade.payment_status = True
        session.add(trade)
        session.commit()
        return "Approved"
    else:
        return "Pending"


def pay_funds_to_seller(trade:Trade):
    "Calculate Fees And Send Funds To Seller"
    # affiliate = Affiliate().check_affiliate(trade.affiliate_id)
    
    # GET TRADE BALANCE
    coin_price = get_coin_price(
        coin_code=trade.coin,
        currency_code=trade.currency
    )
    
    value = float(trade.price)/float(coin_price)
    # CONDITION ON COIN ATTACH TO TRADE

    service_charge = 0.05 * value
    payout_price = float(value) - float(service_charge)
    
    if trade.agent_id != None:
        
        agent = get_agent(trade)
        
        if trade.coin == "BTC":
            txid = client.send_btc(
                mnemonic= agent.mnemonic,
                sender= agent.btc_address,
                amount= float(payout_price),
                address= trade.wallet
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


def close_trade(trade):
    "Closing The Trade"
    trade.is_open = False
    trade.updated_at = str(datetime.now())
    session.add(trade)
    session.commit()


def pay_to_buyer(trade, wallet):
    "Send Funds To Buyer"

    coin_price = get_coin_price(
        coin_code=trade.coin,
        currency_code=trade.currency
    )

    value = float(trade.price)/float(coin_price)
    # CONDITION ON COIN ATTACH TO TRADE

    service_charge = 0.05 * value
    payout_price = float(value) - float(service_charge)
    
    if trade.agent_id != None:
        
        agent = get_agent(trade)
        
        if trade.coin == "BTC":
            txid = client.send_btc(
                mnemonic= agent.mnemonic,
                sender= agent.btc_address,
                amount= float(payout_price),
                address= wallet
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

    if str(user.id) == trade.seller and user.id == trade.buyer:
        dispute.is_buyer = True
        dispute.is_seller = True

    elif str(user.id) != trade.seller and user.id == trade.buyer:
        dispute.is_buyer = True
        dispute.is_seller = False       

    elif str(user.id)== trade.seller and user.id != trade.buyer:
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
    
    
def verify_user(user):
    user.verified

#######################AGENT FUNCTIONS############################

class AgentAction(object):

    def __init__(self) -> None:
        super().__init__()
    
    def check_agent(self, id:int) -> bool:
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

            ### FETCH ETH ADDRESS

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
            id = generate_id(),
            payment_status = False,
            created_at = str(datetime.now()),
            is_open = True,
            agent_id = agent.id,
            seller = agent.affiliate[0].id,
            price = price,
            currency = "USD",
            coin = "BTC",
            wallet =  wallet,
            address = agent.btc_address,
            invoice = ""
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

        if  self.btc == "Failed":
            return None, None

        else:
            return float(self.btc), float(self.eth)


    def get_trades(self, id) -> list:
        "Ftech All Agent Related Trade"
        all_trades = session.query(Trade).all()
        trades = []
        [trades.append(each) for each in all_trades if int(each.agent_id) == id]
        # import pdb; pdb.set_trace()
        return trades

    def pay_btc(self, agent, price, wallet):
        try:
            txid = client.send_btc(
                mnemonic= agent.mnemonic,
                sender= agent.btc_address,
                amount= price,
                address= wallet
            )
            return txid
            
        except Exception as e:
            return None