import logging
from typing import Optional

from config import *
from database import *
from functions import *
from payments import BtcPayAPI

from .user import UserClient
from .utils import generate_id
from .wallet import WalletManager

logger = logging.getLogger(__name__)

client = BtcPayAPI()


class TradeClient:
    """
    Handles all trade-related database operations and business logic.

    This class manages the complete lifecycle of escrow trades including:
    - Trade creation and management
    - Payment processing and verification
    - Crypto deposit/release operations
    - Broker integration
    - Fee calculations
    """

    @staticmethod
    def open_new_trade(
        msg,
        currency: str = "USD",
        chat: str | None = None,
        trade_type: str = "CryptoToCrypto",
    ) -> TradeType:
        """
        Returns a new trade without Agent
        """
        user: UserType = UserClient.get_user(msg)
        logger.debug(
            f"open_new_trade for user {user.get('_id')} with keys: {list(user.keys())}"
        )

        trade: TradeType = {
            "_id": generate_id(),
            "seller_id": user["_id"],
            "buyer_id": "",
            "currency": currency,
            "is_active": False,
            "is_paid": False,
            "price": 0,
            "invoice_id": None,
            "is_completed": False,
            "chat": chat,
            "trade_type": trade_type,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            # Initialize wallet fields
            "receiving_address": "",
            "seller_wallet_id": "",
            "is_wallet_trade": False,
            # Initialize broker fields
            "broker_id": "",
            "broker_enabled": False,
            "broker_commission": 0.0,
            "broker_approved_seller": False,
            "broker_approved_buyer": False,
            "seller_broker_rating": 0,
            "buyer_broker_rating": 0,
            "broker_notes": "",
        }

        db.trades.insert_one(trade)
        return trade

    @staticmethod
    def get_most_recent_trade(user: UserType) -> TradeType | None:
        "Get the most recent trade created by this user"
        most_recent_trade_cursor = (
            db.trades.find(
                {
                    "$or": [
                        {"seller_id": str(user["_id"])},
                        {"buyer_id": str(user["_id"])},
                    ]
                }
            )
            .sort([("created_at", -1)])
            .limit(1)
        )

        # Convert cursor to list to safely check if it has items
        most_recent_trades = list(most_recent_trade_cursor)
        return most_recent_trades[0] if most_recent_trades else None

    @staticmethod
    def get_active_trade_by_user_id(user_id: str) -> Optional[TradeType]:
        "Get the most recent active trade created by this user"
        active_trade_cursor = (
            db.trades.find(
                {
                    "$or": [
                        {"seller_id": user_id},
                        {"buyer_id": user_id},
                    ],
                    "is_active": True,
                }
            )
            .sort([("created_at", -1)])
            .limit(1)
        )

        active_trades = list(active_trade_cursor)
        logging.info(f"Active trades: {active_trades}")
        return active_trades[0] if active_trades else None

    @staticmethod
    def get_trade(id: str) -> TradeType or None:  # type: ignore
        trade: TradeType = db.trades.find_one({"_id": id})
        logger.debug(f"Fetched trade in get_trade: {trade}")
        return trade

    @staticmethod
    def get_trade_by_invoice_id(id: str) -> TradeType or None:  # type: ignore
        trade: TradeType = db.trades.find_one({"invoice_id": id})
        return trade

    @staticmethod
    def add_price(
        *, price: float, user: Optional[UserType] = None, trade_id: Optional[str] = None
    ) -> TradeType | None:
        if not trade_id and not user:
            raise ValueError("Either user or trade_id must be provided to add_price")

        trade: Optional[TradeType] = None
        if trade_id:
            trade = TradeClient.get_trade(trade_id)
        elif user:  # user is not None
            trade = TradeClient.get_most_recent_trade(user)

        if trade is not None:
            db.trades.update_one(
                {"_id": trade["_id"]},
                {"$set": {"price": price, "updated_at": datetime.now()}},
            )
            return TradeClient.get_trade(trade["_id"])  # Return fresh trade data
        return None

    @staticmethod
    def add_terms(
        *, terms: str, user: Optional[UserType] = None, trade_id: Optional[str] = None
    ) -> TradeType | None:
        """
        Update terms of contract
        """
        if not trade_id and not user:
            raise ValueError("Either user or trade_id must be provided to add_terms")

        trade: Optional[TradeType] = None
        if trade_id:
            trade = TradeClient.get_trade(trade_id)
        elif user:  # user is not None
            trade = TradeClient.get_most_recent_trade(user)

        if trade is not None:
            db.trades.update_one(
                {"_id": trade["_id"]},
                {"$set": {"terms": terms, "updated_at": datetime.now()}},
            )
            return TradeClient.get_trade(trade["_id"])  # Return fresh trade data
        return None

    @staticmethod
    def add_invoice_id(trade: TradeType, invoice_id: str):
        """
        Update trade instance with invoice_id
        """
        # Validate invoice_id is not empty
        if not invoice_id or invoice_id.strip() == "":
            logger.error(f"Cannot set empty invoice_id for trade {trade['_id']}")
            return trade

        db.trades.update_one(
            {"_id": trade["_id"]}, {"$set": {"invoice_id": invoice_id}}
        )
        return trade

    @staticmethod
    def add_buyer(trade: TradeType, buyer_id: str):
        "Add Buyer To Trade"
        db.trades.update_one(
            {"_id": trade["_id"]},
            {"$set": {"buyer_id": buyer_id, "updated_at": datetime.now()}},
        )
        return trade

    @staticmethod
    def get_invoice_status(trade: TradeType) -> Optional[str]:  # type: ignore
        "Get Payment Url"
        status = client.get_invoice_status(trade["invoice_id"])
        if status is not None:
            return status
        return None

    @staticmethod
    def get_invoice_url(trade: TradeType) -> str:
        "Get Payment Url - supports both BTCPay (BTC/LTC) and wallet-based (ETH/USDT)"
        active_trade: TradeType = db.trades.find_one({"_id": trade["_id"]})

        # Determine if this is a wallet-based trade (ETH/USDT)
        is_wallet_currency = active_trade.get("currency") in ["ETH", "USDT"]

        if is_wallet_currency:
            # Handle ETH/USDT trades with wallet integration
            return TradeClient._get_wallet_based_payment_info(active_trade)
        else:
            # Handle BTC/LTC trades with BTCPay
            if active_trade["invoice_id"] is None or active_trade["invoice_id"] == "":
                try:
                    url, invoice_id = client.create_invoice(active_trade)
                    if url is not None:
                        TradeClient.add_invoice_id(trade, str(invoice_id))
                        return url
                except Exception as e:
                    app.logger.error(
                        f"Error creating invoice for trade {trade['_id']}: {e}"
                    )
            else:
                return f"{BTCPAY_URL}/i/{trade['invoice_id']}"

            return None

    @staticmethod
    def _get_wallet_based_payment_info(trade: TradeType) -> str:
        """Generate wallet-based payment info for ETH/USDT trades"""
        try:
            logger.info(
                f"Generating wallet payment info for trade {trade['_id']} with currency {trade['currency']}"
            )

            # Get seller's wallet or create one if it doesn't exist
            seller_wallet = WalletManager.get_user_wallet(trade["seller_id"])
            if not seller_wallet:
                logger.info(f"Creating new wallet for seller {trade['seller_id']}")
                seller_wallet = WalletManager.create_wallet_for_user(trade["seller_id"])
                if not seller_wallet:
                    logger.error(
                        f"Failed to create wallet for seller {trade['seller_id']}"
                    )
                    return None

            logger.info(
                f"Found/created wallet {seller_wallet['_id']} for seller {trade['seller_id']}"
            )

            # Get the appropriate address for the trade currency
            coin_symbol = trade["currency"]
            coin_address = WalletManager.get_wallet_coin_address(
                seller_wallet["_id"], coin_symbol
            )

            if not coin_address:
                logger.error(
                    f"No {coin_symbol} address found for seller's wallet {seller_wallet['_id']}"
                )
                return None

            logger.info(f"Found {coin_symbol} address: {coin_address['address']}")

            # Update trade with wallet information
            db.trades.update_one(
                {"_id": trade["_id"]},
                {
                    "$set": {
                        "receiving_address": coin_address["address"],
                        "seller_wallet_id": seller_wallet["_id"],
                        "is_wallet_trade": True,
                        "updated_at": datetime.now(),
                    }
                },
            )

            logger.info(f"Updated trade {trade['_id']} with wallet info")

            # Return the receiving address (for now, later we can create a custom payment page)
            return coin_address["address"]

        except Exception as e:
            logger.error(f"Error generating wallet payment info: {e}")
        return None

    @staticmethod
    def check_trade(user: UserType, trade_id: str) -> str | TradeType:
        "Return trade info"
        trade: TradeType = db.trades.find_one({"_id": trade_id})
        logger.debug(f"Fetched trade in check_trade: {trade}")

        if trade == None:
            return "Not Found"

        # elif trade['buyer_id'] != "":
        #     return "Both parties already exists"

        elif str(trade["seller_id"]) == str(user["_id"]):
            return "Not Permitted"

        else:
            TradeClient.add_buyer(trade=trade, buyer_id=user["_id"])
            return trade

    @staticmethod
    def get_trades(user_id: str):
        "Retrun list of trades the user is in"
        sells_cursor = db.trades.find({"seller_id": user_id})
        buys_cursor = db.trades.find({"buyer_id": user_id})

        sells = list(sells_cursor)
        buys = list(buys_cursor)

        logger.info(f"Sells: {sells}")
        logger.info(f"Buys: {buys}")

        return sells + buys

    @staticmethod
    def get_trades_report(sells: list, buys: list):
        "Return aggregated data of trades"
        purchases = len(buys)
        sales = len(sells)

        active_buys = [i for i in buys if i["is_active"] is True]
        active_sells = [i for i in sells if i["is_active"] is True]
        active = len(active_buys) + len(active_sells)

        trades = purchases + sales

        # r_buys = [i for i in buys if i["dispute"] != []]
        # r_sells = [i for i in sells if i["dispute"] != []]
        # reports = len(r_buys) + len(r_sells)
        reports = []
        for trade in buys + sells:
            trade_report = db.disputes.find({"trade_id": trade["_id"]})
            [reports.append(i) for i in trade_report]

        return purchases, sales, trades, active, len(reports)

    @staticmethod
    def delete_trade(trade_id: str):
        "Delete Trade"
        trade = db.trades.find_one({"_id": trade_id})

        if trade is None:
            return "Not Found!"
        else:
            db.trades.delete_one({"_id": trade_id})
            return "Complete!"

    @staticmethod
    def seller_delete_trade(user_id, trade_id):
        "Delete Trade"
        trade = db.trades.find_one({"_id": trade_id})

        if trade is None:
            return "Trade Not Found"

        elif trade["is_active"] is True:
            return (
                "You are not authorized to close an active trade, close the deal first."
            )

        elif trade["seller_id"] == user_id and trade["is_active"] is False:
            TradeClient.delete_trade(trade_id)
            return "Trade Deleted Successfully"

        else:
            return "You are not authorized to take this action. Please contact support!"

    # WEBHOOK FUNCTIONS TO HANDLE TRANSACTION RESPONSE FROM BTCPAY SERVER #
    @staticmethod
    def handle_invoice_paid(invoice_id: str) -> bool:
        trade = TradeClient.get_trade_by_invoice_id(invoice_id)
        if trade is not None:
            trade_id = trade["_id"]
            db.trades.update_one({"_id": trade_id}, {"$set": {"is_paid": True}})
            return True
        return False

    @staticmethod
    def handle_invoice_expired(invoice_id: str) -> bool:
        trade = TradeClient.get_trade_by_invoice_id(invoice_id)
        if trade is not None:
            trade_id = trade["_id"]
            db.trades.update_one(
                {"_id": trade_id}, {"$set": {"is_paid": False, "is_active": False}}
            )
            return True
        return False

    @staticmethod
    def reset_all_active_trades() -> int:
        """Reset all active trades to inactive state

        Returns the number of trades that were reset
        """
        result = db.trades.update_many(
            {"is_active": True},
            {"$set": {"is_active": False, "updated_at": datetime.now()}},
        )
        return result.modified_count

    @staticmethod
    def get_all_active_trades():
        """Get all active trades in the database

        Returns a list of all active trades
        """
        active_trades_cursor = db.trades.find({"is_active": True})
        return list(active_trades_cursor)

    @staticmethod
    def get_active_market_shops():
        """Get all active market shops"""
        shops = db.trades.find(
            {
                "trade_type": "MarketShop",
                "is_active": True,
                "buyer_id": "",  # No buyer yet
            }
        ).sort([("created_at", -1)])
        return list(shops)

    @staticmethod
    def get_trade_by_invoice_id(invoice_id: str) -> TradeType | None:
        """Get trade by invoice ID"""
        trade = db.trades.find_one({"invoice_id": invoice_id})
        return trade

    @staticmethod
    def update_trade_status(trade_id: str, status: str) -> bool:
        """Update trade status and deactivate if terminal status"""
        try:
            # Define terminal statuses that should deactivate the trade
            terminal_statuses = [
                "completed",
                "cancelled",
                "expired",
                "failed",
                "crypto_released",
            ]

            update_data = {"status": status, "updated_at": datetime.now()}

            # If it's a terminal status, also deactivate the trade
            if status.lower() in terminal_statuses:
                update_data["is_active"] = False
                logger.info(
                    f"Deactivating trade {trade_id} due to terminal status: {status}"
                )

            db.trades.update_one({"_id": trade_id}, {"$set": update_data})
            return True
        except Exception as e:
            logger.error(f"Error updating trade status: {e}")
            return False

    @staticmethod
    def confirm_crypto_deposit(trade_id: str) -> bool:
        """Confirm crypto deposit for a trade"""
        try:
            db.trades.update_one(
                {"_id": trade_id},
                {
                    "$set": {
                        "is_crypto_deposited": True,
                        "crypto_deposit_time": datetime.now(),
                        "updated_at": datetime.now(),
                    }
                },
            )
            return True
        except Exception as e:
            logger.error(f"Error confirming crypto deposit: {e}")
            return False

    @staticmethod
    def confirm_fiat_payment(trade_id: str) -> bool:
        """Confirm fiat payment for a trade"""
        try:
            db.trades.update_one(
                {"_id": trade_id},
                {
                    "$set": {
                        "is_fiat_paid": True,
                        "fiat_payment_time": datetime.now(),
                        "updated_at": datetime.now(),
                    }
                },
            )
            return True
        except Exception as e:
            logger.error(f"Error confirming fiat payment: {e}")
            return False

    @staticmethod
    def add_fiat_payment_proof(
        trade_id: str, file_id: str, file_type: str, buyer_id: str
    ) -> bool:
        """Add fiat payment proof to a trade"""
        try:
            db.trades.update_one(
                {"_id": trade_id},
                {
                    "$set": {
                        "fiat_payment_proof": {
                            "file_id": file_id,
                            "file_type": file_type,
                            "submitted_by": buyer_id,
                            "submitted_at": datetime.now(),
                        },
                        "updated_at": datetime.now(),
                    }
                },
            )
            return True
        except Exception as e:
            logger.error(f"Error adding fiat payment proof: {e}")
            return False

    @staticmethod
    def approve_fiat_payment(trade_id: str, seller_id: str) -> bool:
        """Approve fiat payment and mark trade as ready for crypto release"""
        try:
            db.trades.update_one(
                {"_id": trade_id},
                {
                    "$set": {
                        "is_fiat_paid": True,
                        "fiat_payment_approved": True,
                        "fiat_approved_by": seller_id,
                        "fiat_approved_at": datetime.now(),
                        "status": "fiat_approved",
                        "updated_at": datetime.now(),
                    }
                },
            )
            return True
        except Exception as e:
            logger.error(f"Error approving fiat payment: {e}")
            return False

    @staticmethod
    def reject_fiat_payment(trade_id: str, seller_id: str, reason: str = None) -> bool:
        """Reject fiat payment proof"""
        try:
            update_data = {
                "fiat_payment_rejected": True,
                "fiat_rejected_by": seller_id,
                "fiat_rejected_at": datetime.now(),
                "status": "fiat_rejected",
                "updated_at": datetime.now(),
            }
            if reason:
                update_data["fiat_rejection_reason"] = reason

            db.trades.update_one({"_id": trade_id}, {"$set": update_data})
            return True
        except Exception as e:
            logger.error(f"Error rejecting fiat payment: {e}")
            return False

    @staticmethod
    def complete_trade(trade_id: str) -> bool:
        """Mark trade as completed and deactivate it"""
        try:
            db.trades.update_one(
                {"_id": trade_id},
                {
                    "$set": {
                        "is_completed": True,
                        "is_active": False,  # Deactivate the trade when completed
                        "status": "completed",
                        "completed_at": datetime.now(),
                        "updated_at": datetime.now(),
                    }
                },
            )
            return True
        except Exception as e:
            logger.error(f"Error completing trade: {e}")
            return False

    @staticmethod
    def calculate_trade_fee(amount: float) -> tuple[float, float]:
        """Calculate bot fee and total deposit amount for trade (legacy method)
        
        DEPRECATED: Use calculate_trade_fee_with_gas for wallet-based trades

        Args:
            amount: The amount the buyer will receive

        Returns:
            tuple: (fee_amount, total_deposit_required)
        """
        from config import BOT_FEE_PERCENTAGE

        fee_amount = amount * (BOT_FEE_PERCENTAGE / 100)
        total_deposit_required = amount + fee_amount
        return fee_amount, total_deposit_required

    @staticmethod
    def calculate_trade_fee_with_gas(amount: float, currency: str) -> dict:
        """Calculate comprehensive fee breakdown including gas costs
        
        Args:
            amount: The amount the buyer will receive
            currency: Currency symbol (ETH, USDT, etc.)
            
        Returns:
            dict: {
                'bot_fee': float,
                'gas_fee_user_payout': float,      # Gas for sending to buyer
                'gas_fee_bot_payout': float,       # Gas for bot fee payout
                'total_gas_fees': float,           # Sum of all gas fees
                'total_deposit_required': float,   # Total amount seller must deposit
                'breakdown': dict                  # Detailed breakdown for display
            }
        """
        from config import BOT_FEE_PERCENTAGE
        
        # Bot fee calculation
        bot_fee = amount * (BOT_FEE_PERCENTAGE / 100)
        
        # Gas fee estimation based on current network conditions
        gas_fees = TradeClient._estimate_gas_fees(currency)
        
        # For ETH trades: user payout + bot payout both use ETH gas
        # For USDT trades: user payout uses ETH gas, bot payout uses ETH gas
        gas_fee_user_payout = gas_fees['user_payout']
        gas_fee_bot_payout = gas_fees['bot_payout']
        total_gas_fees = gas_fee_user_payout + gas_fee_bot_payout
        
        # Total deposit calculation
        if currency == "ETH":
            # For ETH: amount + bot_fee + gas_fees (all in ETH)
            total_deposit_required = amount + bot_fee + total_gas_fees
        else:
            # For USDT: amount + bot_fee (in USDT) + gas_fees (in ETH, separate requirement)
            total_deposit_required = amount + bot_fee  # USDT amount
            # Note: gas fees will be required separately in ETH
        
        return {
            'bot_fee': bot_fee,
            'gas_fee_user_payout': gas_fee_user_payout,
            'gas_fee_bot_payout': gas_fee_bot_payout,
            'total_gas_fees': total_gas_fees,
            'total_deposit_required': total_deposit_required,
            'breakdown': {
                'amount_to_buyer': amount,
                'bot_fee': bot_fee,
                'bot_fee_percentage': BOT_FEE_PERCENTAGE,
                'gas_for_buyer_payout': gas_fee_user_payout,
                'gas_for_bot_payout': gas_fee_bot_payout,
                'total_gas_required': total_gas_fees,
                'currency': currency
            }
        }
    
    @staticmethod
    def _estimate_gas_fees(currency: str) -> dict:
        """Estimate gas fees for both user and bot payouts
        
        Returns:
            dict: {'user_payout': float, 'bot_payout': float}  # Both in ETH
        """
        try:
            from functions.wallet import WalletManager
            from web3 import Web3
            
            # Get current gas price from network
            if currency in ["ETH", "USDT"]:
                web3 = WalletManager._get_web3_connection(
                    WalletManager.SUPPORTED_COINS.get(currency, WalletManager.SUPPORTED_COINS["ETH"])
                )
                if web3:
                    current_gas_price = web3.eth.gas_price
                    
                    if currency == "ETH":
                        # ETH transfers: 21,000 gas each
                        user_payout_gas = 21000
                        bot_payout_gas = 21000
                    else:  # USDT
                        # USDT transfers: ~64,000 gas each
                        user_payout_gas = 65000
                        bot_payout_gas = 65000
                    
                    # Convert to ETH with 20% buffer for price fluctuations
                    user_payout_fee = float(web3.from_wei(user_payout_gas * current_gas_price * 1.2, 'ether'))
                    bot_payout_fee = float(web3.from_wei(bot_payout_gas * current_gas_price * 1.2, 'ether'))
                    
                    return {
                        'user_payout': user_payout_fee,
                        'bot_payout': bot_payout_fee
                    }
        except Exception as e:
            logger.warning(f"Could not get real-time gas prices: {e}")
        
        # Fallback to conservative estimates if network unavailable
        if currency == "ETH":
            return {
                'user_payout': 0.001,  # ~21k gas at 47 gwei
                'bot_payout': 0.001
            }
        else:  # USDT and other tokens
            return {
                'user_payout': 0.003,  # ~65k gas at 47 gwei
                'bot_payout': 0.003
            }
    
    @staticmethod
    def get_gas_requirements_for_currency(currency: str) -> dict:
        """Get gas requirements explanation for a specific currency
        
        Returns:
            dict: Information about gas requirements for user display
        """
        if currency == "ETH":
            return {
                'requires_separate_eth': False,
                'explanation': 'Gas fees are included in the total ETH deposit amount',
                'gas_used_for': ['Transfer to buyer', 'Bot fee payout'],
                'combined_deposit': True
            }
        elif currency == "USDT":
            return {
                'requires_separate_eth': True,
                'explanation': 'ETH is required for gas fees in addition to USDT amount',
                'gas_used_for': ['Transfer USDT to buyer', 'Bot fee payout'],
                'combined_deposit': False,
                'eth_required_reason': 'USDT runs on Ethereum network and requires ETH for transaction fees'
            }
        else:
            return {
                'requires_separate_eth': True,
                'explanation': f'ETH is required for gas fees in addition to {currency} amount',
                'gas_used_for': [f'Transfer {currency} to buyer', 'Bot fee payout'],
                'combined_deposit': False
            }

    @staticmethod
    def set_buyer_address(
        trade_id: str, buyer_address: str, network: str = None
    ) -> bool:
        """Set buyer's crypto address for receiving funds"""
        try:
            update_data = {"buyer_address": buyer_address, "updated_at": datetime.now()}
            if network:
                update_data["buyer_network"] = network

            db.trades.update_one({"_id": trade_id}, {"$set": update_data})
            return True
        except Exception as e:
            logger.error(f"Error setting buyer address: {e}")
            return False

    @staticmethod
    def initiate_crypto_release(trade_id: str) -> bool:
        """Initiate crypto release process - transfer from seller wallet to buyer"""
        try:
            trade = TradeClient.get_trade(trade_id)
            if not trade:
                logger.error(f"Trade {trade_id} not found for crypto release")
                return False

            # Check if trade is approved and has buyer address
            if not trade.get("fiat_payment_approved"):
                logger.error(f"Trade {trade_id} payment not approved")
                return False

            buyer_address = trade.get("buyer_address")
            if not buyer_address:
                logger.error(f"Trade {trade_id} missing buyer address")
                return False

            # Calculate fee and gas amounts using gas-aware calculation
            original_amount = float(trade.get("price", 0))
            currency = trade.get("currency")
            
            # Use gas-inclusive calculation for wallet-based trades
            if trade.get("is_wallet_trade"):
                fee_data = TradeClient.calculate_trade_fee_with_gas(original_amount, currency)
                fee_amount = fee_data['bot_fee']
                total_gas_fees = fee_data['total_gas_fees']
                logger.info(f"Gas-aware release: Bot fee={fee_amount}, Gas fees={total_gas_fees}")
            else:
                # Legacy calculation for BTCPay trades
                fee_amount, _ = TradeClient.calculate_trade_fee(original_amount)
                total_gas_fees = 0
                logger.info(f"Legacy release: Bot fee={fee_amount}")
            
            available_for_bot = fee_amount  # Bot gets the full fee since gas was pre-calculated

            # For wallet-based trades (ETH/USDT), initiate transfer
            if trade.get("is_wallet_trade"):
                from functions.wallet import WalletManager

                seller_wallet_id = trade.get("seller_wallet_id")
                currency = trade.get("currency")

                if not seller_wallet_id:
                    logger.error(f"Trade {trade_id} missing seller wallet ID")
                    return False

                # Transfer the original amount to buyer (seller deposited original + fee)
                success = WalletManager.transfer_crypto(
                    from_wallet_id=seller_wallet_id,
                    to_address=buyer_address,
                    amount=original_amount,  # Buyer gets the original amount
                    currency=currency,
                    trade_id=trade_id,
                )

                if success:
                    # Update trade with release information including gas fee accounting
                    update_data = {
                        "crypto_released": True,
                        "crypto_release_amount": original_amount,  # Record what was sent to buyer
                        "bot_fee_amount": available_for_bot,  # Bot fee after gas accounting
                        "crypto_release_time": datetime.now(),
                        "status": "crypto_released",
                        "updated_at": datetime.now(),
                    }
                    
                    # Add gas fee information for wallet-based trades
                    if trade.get("is_wallet_trade"):
                        update_data.update({
                            "gas_fees_reserved": total_gas_fees,
                            "total_deposit_with_gas": fee_data['total_deposit_required'],
                            "gas_fee_breakdown": {
                                "user_payout_gas": fee_data['gas_fee_user_payout'],
                                "bot_payout_gas": fee_data['gas_fee_bot_payout']
                            }
                        })
                    
                    db.trades.update_one({"_id": trade_id}, {"$set": update_data})
                    logger.info(
                        f"Crypto released for trade {trade_id}: {original_amount} {currency} to {buyer_address}"
                    )
                    return True
                else:
                    logger.error(f"Failed to transfer crypto for trade {trade_id}")
                    return False
            else:
                # For BTCPay trades, handle differently (if needed)
                logger.warning(
                    f"Crypto release not implemented for non-wallet trade {trade_id}"
                )
                return False

        except Exception as e:
            logger.error(f"Error initiating crypto release for trade {trade_id}: {e}")
            return False

    @staticmethod
    def request_buyer_address(trade_id: str) -> bool:
        """Mark trade as waiting for buyer address"""
        try:
            db.trades.update_one(
                {"_id": trade_id},
                {
                    "$set": {
                        "status": "awaiting_buyer_address",
                        "updated_at": datetime.now(),
                    }
                },
            )
            return True
        except Exception as e:
            logger.error(f"Error requesting buyer address: {e}")
            return False

    @staticmethod
    def cancel_trade(trade_id: str, user_id: str) -> bool:
        """Cancel a trade"""
        try:
            # Get the trade to verify it exists and user has permission
            trade = TradeClient.get_trade(trade_id)
            if not trade:
                logger.error(f"Trade {trade_id} not found for cancellation")
                return False

            # Check if user is authorized (seller or buyer)
            seller_id = str(trade.get("seller_id", ""))
            buyer_id = str(trade.get("buyer_id", ""))

            if user_id not in [seller_id, buyer_id]:
                logger.error(
                    f"User {user_id} not authorized to cancel trade {trade_id}"
                )
                return False

            # Update trade to cancelled status
            result = db.trades.update_one(
                {"_id": trade_id},
                {
                    "$set": {
                        "is_active": False,
                        "is_cancelled": True,
                        "cancelled_by": user_id,
                        "cancelled_at": datetime.now(),
                        "updated_at": datetime.now(),
                    }
                },
            )

            if result.modified_count > 0:
                logger.info(
                    f"Trade {trade_id} cancelled successfully by user {user_id}"
                )
                return True
            else:
                logger.error(f"Failed to update trade {trade_id} to cancelled status")
                return False

        except Exception as e:
            logger.error(f"Error cancelling trade {trade_id}: {e}")
            return False

    @staticmethod
    def join_trade(trade_id: str, user_id: str) -> bool:
        """Allow a buyer to join an active trade"""
        try:
            # Get the trade to verify it exists and is available
            trade = TradeClient.get_trade(trade_id)
            if not trade:
                logger.error(f"Trade {trade_id} not found for joining")
                return False

            # Check if trade is active and available for joining
            if not trade.get("is_active", False):
                logger.error(f"Trade {trade_id} is not active")
                return False

            # Check if trade already has a buyer
            if trade.get("buyer_id") and trade.get("buyer_id") != "":
                logger.error(f"Trade {trade_id} already has a buyer")
                return False

            # Check if user is not the seller
            seller_id = str(trade.get("seller_id", ""))
            if str(user_id) == seller_id:
                logger.error(f"User {user_id} cannot join their own trade {trade_id}")
                return False

            # Add the buyer to the trade
            result = db.trades.update_one(
                {"_id": trade_id},
                {"$set": {"buyer_id": str(user_id), "updated_at": datetime.now()}},
            )

            if result.modified_count > 0:
                logger.info(f"User {user_id} successfully joined trade {trade_id}")
                return True
            else:
                logger.error(f"Failed to add user {user_id} to trade {trade_id}")
                return False

        except Exception as e:
            logger.error(f"Error joining trade {trade_id}: {e}")
            return False

    # ========== BROKER-RELATED METHODS ==========

    @staticmethod
    def add_broker_to_trade(trade_id: str, broker_id: str) -> bool:
        """Add a broker to a trade"""
        try:
            from .broker import BrokerClient

            trade = TradeClient.get_trade(trade_id)
            if not trade:
                logger.error(f"Trade {trade_id} not found")
                return False

            # Validate broker for this trade
            validation = BrokerClient.validate_broker_for_trade(
                broker_id,
                trade.get("trade_type"),
                trade.get("seller_id"),
                trade.get("buyer_id"),
            )

            if not validation.get("valid"):
                logger.error(f"Broker validation failed: {validation.get('reason')}")
                return False

            broker = validation.get("broker")

            result = db.trades.update_one(
                {"_id": trade_id},
                {
                    "$set": {
                        "broker_id": broker_id,
                        "broker_enabled": True,
                        "broker_commission": broker.get("commission_rate", 1.0),
                        "updated_at": datetime.now(),
                    }
                },
            )

            if result.modified_count > 0:
                logger.info(f"Broker {broker_id} added to trade {trade_id}")
                return True
            return False

        except Exception as e:
            logger.error(f"Error adding broker to trade: {e}")
            return False

    @staticmethod
    def broker_approve_participant(
        trade_id: str, broker_id: str, participant_type: str, notes: str = ""
    ) -> bool:
        """Broker approves seller or buyer for the trade"""
        try:
            if participant_type not in ["seller", "buyer"]:
                logger.error(f"Invalid participant type: {participant_type}")
                return False

            trade = TradeClient.get_trade(trade_id)
            if not trade or trade.get("broker_id") != broker_id:
                logger.error(f"Broker {broker_id} not authorized for trade {trade_id}")
                return False

            field_name = f"broker_approved_{participant_type}"
            update_data = {field_name: True, "updated_at": datetime.now()}

            if notes:
                update_data["broker_notes"] = notes

            result = db.trades.update_one({"_id": trade_id}, {"$set": update_data})

            if result.modified_count > 0:
                logger.info(
                    f"Broker {broker_id} approved {participant_type} for trade {trade_id}"
                )
                return True
            return False

        except Exception as e:
            logger.error(f"Error in broker approval: {e}")
            return False

    @staticmethod
    def check_broker_approvals(trade_id: str) -> dict:
        """Check if broker has approved both participants"""
        trade = TradeClient.get_trade(trade_id)
        if not trade or not trade.get("broker_enabled"):
            return {"broker_enabled": False}

        return {
            "broker_enabled": True,
            "broker_id": trade.get("broker_id"),
            "seller_approved": trade.get("broker_approved_seller", False),
            "buyer_approved": trade.get("broker_approved_buyer", False),
            "both_approved": trade.get("broker_approved_seller", False)
            and trade.get("broker_approved_buyer", False),
        }

    @staticmethod
    def rate_trade_broker(trade_id: str, user_id: str, rating: int) -> bool:
        """Allow seller or buyer to rate the broker after trade completion"""
        try:
            trade = TradeClient.get_trade(trade_id)
            if not trade or not trade.get("broker_enabled"):
                logger.error(f"Trade {trade_id} has no broker to rate")
                return False

            # Determine if user is seller or buyer
            seller_id = str(trade.get("seller_id", ""))
            buyer_id = str(trade.get("buyer_id", ""))

            if str(user_id) == seller_id:
                field_name = "seller_broker_rating"
            elif str(user_id) == buyer_id:
                field_name = "buyer_broker_rating"
            else:
                logger.error(f"User {user_id} not part of trade {trade_id}")
                return False

            # Update trade with rating
            result = db.trades.update_one(
                {"_id": trade_id},
                {"$set": {field_name: rating, "updated_at": datetime.now()}},
            )

            if result.modified_count > 0:
                # Update broker's overall rating
                from .broker import BrokerClient

                BrokerClient.rate_broker(trade.get("broker_id"), rating, trade_id)
                logger.info(
                    f"User {user_id} rated broker {rating} stars for trade {trade_id}"
                )
                return True
            return False

        except Exception as e:
            logger.error(f"Error rating broker: {e}")
            return False

    @staticmethod
    def complete_brokered_trade(trade_id: str) -> bool:
        """Complete a trade with broker involvement"""
        try:
            trade = TradeClient.get_trade(trade_id)
            if not trade:
                return False

            # Standard trade completion
            success = TradeClient.complete_trade(trade_id)

            if success and trade.get("broker_enabled"):
                # Increment broker's trade counter
                from .broker import BrokerClient

                BrokerClient.increment_broker_trades(
                    trade.get("broker_id"), successful=True
                )
                logger.info(f"Completed brokered trade {trade_id}")

            return success

        except Exception as e:
            logger.error(f"Error completing brokered trade: {e}")
            return False
