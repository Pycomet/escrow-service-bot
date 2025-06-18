import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from config import *
from functions.wallet import WalletManager
from functions.user import UserClient
from functions.trade import TradeClient
from utils.enums import EmojiEnums
from typing import Optional
import asyncio
from decimal import Decimal
from datetime import datetime
import os
import sys

logger = logging.getLogger(__name__)

class AdminWalletManager:
    """Admin functions for wallet management"""
    
    # Fee constants (in respective currencies) - REALISTIC VALUES
    FEES = {
        'SOL': Decimal('0.000005'),  # ~$0.001 - SOL fees are very low
        'BNB': Decimal('0.001'),     # ~$0.50 - BSC fees  
        'LTC': Decimal('0.0001'),    # ~$0.01 - LTC fees
        'DOGE': Decimal('1.0'),      # ~$0.40 - DOGE fees
        'BTC': Decimal('0.0001'),    # ~$7 - Conservative BTC fee 
        'ETH': Decimal('0.003'),     # ~$10 - ETH fees (can vary widely)
        'USDT': {
            'solana': Decimal('0.000005'),  # SOL fee for USDT on Solana (~$0.001)
            'binance': Decimal('0.001'),    # BNB fee for USDT on BSC (~$0.50)
            'tron': Decimal('15'),          # TRX fee for USDT on Tron (~$4.50)
            'ethereum': Decimal('0.002')    # ETH fee for USDT on Ethereum (~$10)
        }
    }
    
    @staticmethod
    async def is_admin(user_id: int) -> bool:
        """Check if user is admin"""
        return user_id == ADMIN_ID
    
    @staticmethod
    async def get_user_wallet_info(user_id: str) -> Optional[dict]:
        """Get comprehensive wallet info for a user"""
        try:
            logger.info(f"=== GETTING WALLET INFO FOR USER {user_id} ===")
            
            # Get user wallet
            wallet = WalletManager.get_user_wallet(user_id)
            if not wallet:
                logger.warning(f"No wallet found for user {user_id}")
                return None
            
            logger.info(f"Found wallet {wallet['_id']} for user {user_id}")
            
            # Get coin addresses
            coin_addresses = WalletManager.get_wallet_coin_addresses(wallet['_id'])
            logger.info(f"Found {len(coin_addresses)} coin addresses for wallet {wallet['_id']}")
            
            # Get balances and calculate totals
            wallet_manager = WalletManager()
            total_coins = len(coin_addresses)
            coins_with_balance = 0
            
            coin_balances = []
            for coin_address in coin_addresses:
                try:
                    balance = float(coin_address.get('balance', 0))
                    if balance > 0:
                        coins_with_balance += 1
                    
                    coin_balances.append({
                        'symbol': coin_address['coin_symbol'],
                        'address': coin_address['address'],
                        'balance': balance,
                        'private_key_encrypted': coin_address.get('private_key_encrypted', ''),
                        'network': coin_address.get('network', '')
                    })
                    
                    logger.debug(f"Coin {coin_address['coin_symbol']}: {balance} balance")
                except Exception as e:
                    logger.error(f"Error processing coin {coin_address.get('coin_symbol', 'unknown')}: {e}")
                    continue
            
            logger.info(f"Processed {len(coin_balances)} coin balances, {coins_with_balance} with positive balance")
            
            return {
                'wallet': wallet,
                'coin_addresses': coin_balances,
                'stats': {
                    'total_coins': total_coins,
                    'coins_with_balance': coins_with_balance
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting wallet info for user {user_id}: {e}")
            return None
    
    @staticmethod
    def get_transaction_fee(coin_symbol: str, network: str = None) -> tuple[Decimal, str]:
        """Get estimated transaction fee for a coin - returns (amount, currency)"""
        try:
            if coin_symbol == 'USDT':
                if network == 'ethereum':
                    return Decimal('8'), 'USDT'  # USDT fee for USDT on Ethereum (~$10)
                elif network == 'solana':
                    return Decimal('0.000005'), 'SOL'  # SOL fee for USDT on Solana
                elif network == 'binance':
                    return Decimal('0.001'), 'BNB'  # BNB fee for USDT on BSC
                elif network == 'tron':
                    return Decimal('15'), 'TRX'  # TRX fee for USDT on Tron
                else:
                    return Decimal('8'), 'USDT'  # Default to USDT fee
            else:
                # For native currencies, fee is in same currency
                fee_amount = AdminWalletManager.FEES.get(coin_symbol, Decimal('0.001'))
                return fee_amount, coin_symbol
        except Exception as e:
            logger.error(f"Error getting fee for {coin_symbol} on {network}: {e}")
            return Decimal('0.001'), coin_symbol  # Default fee
    
    @staticmethod
    def check_sufficient_balance_for_token(token_balance: Decimal, token_amount: Decimal, 
                                         gas_balance: Decimal, gas_fee: Decimal, 
                                         token_symbol: str, gas_symbol: str) -> tuple[bool, str]:
        """Check if balances are sufficient for token transfer (token amount + gas fee)"""
        
        logger.info(f"=== TOKEN BALANCE CHECK ===")
        logger.info(f"Token ({token_symbol}) balance: {token_balance}")
        logger.info(f"Token amount to send: {token_amount}")
        logger.info(f"Gas ({gas_symbol}) balance: {gas_balance}")
        logger.info(f"Gas fee required: {gas_fee}")
        
        # Check token balance
        if token_balance < token_amount:
            token_shortfall = token_amount - token_balance
            error_msg = f"Insufficient {token_symbol}. Has {token_balance}, need {token_amount}. Shortfall: {token_shortfall} {token_symbol}"
            logger.warning(error_msg)
            return False, error_msg
        
        # Check gas balance
        if gas_balance < gas_fee:
            gas_shortfall = gas_fee - gas_balance
            error_msg = f"Insufficient {gas_symbol} for gas. Has {gas_balance}, need {gas_fee}. Shortfall: {gas_shortfall} {gas_symbol}"
            logger.warning(error_msg)
            return False, error_msg
        
        logger.info("✅ Token and gas balance checks passed")
        return True, "Sufficient balance"
    
    @staticmethod
    def simple_log_message(message: str, log_file: str):
        """Simple logging utility for transaction scripts"""
        try:
            logger.info(f"[{log_file}] {message}")
        except Exception as e:
            logger.error(f"Error logging message: {e}")
    
    @staticmethod
    def check_sufficient_balance(balance: Decimal, amount: Decimal, fee: Decimal) -> tuple[bool, str]:
        """Check if balance is sufficient for amount + fee"""
        required_total = amount + fee
        
        logger.info(f"=== BALANCE CHECK ===")
        logger.info(f"Current balance: {balance}")
        logger.info(f"Amount to send: {amount}")
        logger.info(f"Estimated fee: {fee}")
        logger.info(f"Required total: {required_total}")
        
        if balance < required_total:
            shortfall = required_total - balance
            error_msg = f"Insufficient balance. Has {balance}, need {required_total} (amount: {amount} + fee: {fee}). Shortfall: {shortfall}"
            logger.warning(error_msg)
            return False, error_msg
        
        logger.info("✅ Balance check passed")
        return True, "Sufficient balance"
    
    @staticmethod
    async def send_crypto(sender_wallet_id: str, coin_symbol: str, recipient_address: str, 
                         amount: float, admin_user_id: str) -> dict:
        """Send cryptocurrency from a user's wallet (admin function)"""
        try:
            logger.info(f"=== ADMIN CRYPTO SEND INITIATED ===")
            logger.info(f"Admin ID: {admin_user_id}")
            logger.info(f"Wallet ID: {sender_wallet_id}")
            logger.info(f"Coin: {coin_symbol}")
            logger.info(f"Recipient: {recipient_address}")
            logger.info(f"Amount: {amount}")
            
            # Get the coin address for sending
            coin_address = WalletManager.get_wallet_coin_address(sender_wallet_id, coin_symbol)
            if not coin_address:
                error_msg = f"No {coin_symbol} address found in wallet"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}
            
            logger.info(f"Found coin address: {coin_address['address']}")
            
            # Get current balance - use database balance for consistency with wallet display
            current_balance = Decimal(str(coin_address.get('balance', 0)))
            amount_decimal = Decimal(str(amount))
            network = coin_address.get('network', '')
            
            logger.info(f"Database balance for {coin_symbol}: {current_balance}")
            
            # If balance is zero, try to refresh it
            if current_balance == 0:
                logger.info("Balance is zero, attempting to refresh...")
                wallet_manager = WalletManager()
                await wallet_manager.refresh_wallet_balances(sender_wallet_id)
                
                # Get updated coin address after refresh
                coin_address = WalletManager.get_wallet_coin_address(sender_wallet_id, coin_symbol)
                if coin_address:
                    current_balance = Decimal(str(coin_address.get('balance', 0)))
                    logger.info(f"Refreshed balance for {coin_symbol}: {current_balance}")
                else:
                    logger.error("Failed to get updated coin address after refresh")
                    return {"success": False, "error": "Failed to refresh balance"}
            
            # Get network info
            network = coin_address.get('network', '')
            logger.info(f"Network: {network}")
            
            # Calculate transaction fee
            estimated_fee, fee_currency = AdminWalletManager.get_transaction_fee(coin_symbol, network)
            logger.info(f"Estimated transaction fee: {estimated_fee} {fee_currency}")
            
            # Check if balance is sufficient - different logic for tokens vs native currencies
            if coin_symbol == 'USDT' and fee_currency != coin_symbol:
                # For tokens like USDT on other networks (SOL, BSC, TRON), we need to check both token balance and gas currency balance
                logger.info("Checking token + gas balance for USDT transaction")
                
                # Get gas currency balance (SOL, BNB, TRX)
                gas_coin_address = WalletManager.get_wallet_coin_address(sender_wallet_id, fee_currency)
                if not gas_coin_address:
                    error_msg = f"No {fee_currency} address found for gas fees"
                    logger.error(error_msg)
                    return {"success": False, "error": error_msg}
                
                # Use database balance for gas currency too
                gas_balance = Decimal(str(gas_coin_address.get('balance', 0)))
                logger.info(f"Gas currency ({fee_currency}) database balance: {gas_balance}")
                
                # If gas balance is zero, try to refresh it
                if gas_balance == 0:
                    logger.info("Gas balance is zero, attempting to refresh...")
                    await wallet_manager.refresh_wallet_balances(sender_wallet_id)
                    
                    # Get updated gas coin address after refresh
                    gas_coin_address = WalletManager.get_wallet_coin_address(sender_wallet_id, fee_currency)
                    if gas_coin_address:
                        gas_balance = Decimal(str(gas_coin_address.get('balance', 0)))
                        logger.info(f"Refreshed gas balance for {fee_currency}: {gas_balance}")
                    else:
                        logger.error("Failed to get updated gas coin address after refresh")
                        return {"success": False, "error": "Failed to refresh gas balance"}
                
                # Check both balances
                sufficient, balance_message = AdminWalletManager.check_sufficient_balance_for_token(
                    current_balance, amount_decimal, gas_balance, estimated_fee, coin_symbol, fee_currency
                )
            else:
                # For native currencies and USDT on Ethereum (where fee is also in USDT), use the simple logic
                sufficient, balance_message = AdminWalletManager.check_sufficient_balance(
                    current_balance, amount_decimal, estimated_fee
                )
            
            if not sufficient:
                logger.error(f"Balance check failed: {balance_message}")
                return {"success": False, "error": balance_message}
            
            # Get private key for sending
            private_key_encrypted = coin_address.get('private_key_encrypted', '')
            if not private_key_encrypted:
                error_msg = f"No private key found for {coin_symbol} address"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}
            
            # Decrypt private key - ensure wallet_manager is available
            if 'wallet_manager' not in locals():
                wallet_manager = WalletManager()
            
            logger.info("Decrypting private key...")
            try:
                private_key = wallet_manager._decrypt_data(private_key_encrypted)
                logger.info("✅ Private key decrypted successfully")
            except Exception as decrypt_error:
                logger.error(f"❌ Failed to decrypt private key: {decrypt_error}")
                return {"success": False, "error": f"Private key decryption failed: {str(decrypt_error)}"}
            
            sender_address = coin_address['address']
            
            logger.info(f"=== EXECUTING TRANSACTION ===")
            logger.info(f"From: {sender_address}")
            logger.info(f"To: {recipient_address}")
            logger.info(f"Amount: {amount} {coin_symbol}")
            logger.info(f"Fee: {estimated_fee} {fee_currency}")
            logger.info(f"Network: {network}")
            
            # Execute the actual transaction using the web3 functions
            try:
                tx_hash = None
                logger.info(f"Starting transaction execution for {coin_symbol}...")
                
                if coin_symbol == 'SOL':
                    logger.info("Executing SOL transaction...")
                    # Import and call the SOL sending function
                    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'functions', 'scripts'))
                    from simple_sol_to_sol_sender import send_transaction as sol_send
                    
                    # Create trade details structure for the sender
                    trade_details = {
                        'fee': '0',
                        'broker_fee': '0',
                        'brokerTrade': False,
                        'brokerAddress': None
                    }
                    
                    tx_hash = sol_send(
                        private_key, recipient_address, str(amount), 
                        sender_address, trade_details, os.getenv('SOLANA_FEE_PAYER_SECRET')
                    )
                    
                elif coin_symbol == 'BNB':
                    logger.info("Executing BNB transaction...")
                    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'functions', 'scripts'))
                    from simple_bnb_transaction import send_bnb
                    
                    # Call BNB sending function
                    from utils import private_key_to_bsc_address
                    
                    actual_sender_address = private_key_to_bsc_address(private_key)
                    tx_hash = send_bnb(
                        actual_sender_address, private_key, [recipient_address], [amount], 
                        sender_address, empty_wallet=False
                    )
                    
                elif coin_symbol == 'LTC':
                    logger.info("Executing LTC transaction...")
                    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'functions', 'scripts'))
                    from ltctransactionsender import send_ltc_transaction
                    
                    trade_details = {
                        'fee': '0',
                        'broker_fee': '0',
                        'brokerTrade': False,
                        'brokerAddress': None
                    }
                    
                    tx_hash = send_ltc_transaction(
                        sender_address, private_key, recipient_address, amount,
                        os.getenv('BLOCK_CYPHER_API_TOKEN'), 
                        os.getenv('LTC_FEE_WALLET', sender_address), 
                        trade_details
                    )
                    
                elif coin_symbol == 'DOGE':
                    logger.info("Executing DOGE transaction...")
                    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'functions', 'scripts'))
                    from doge_transaction_sender import send_doge_transaction
                    
                    trade_details = {
                        'fee': '0',
                        'broker_fee': '0',
                        'brokerTrade': False,
                        'brokerAddress': None
                    }
                    
                    tx_hash = send_doge_transaction(
                        sender_address, private_key, recipient_address, amount,
                        os.getenv('BLOCK_CYPHER_API_TOKEN'),
                        os.getenv('DOGE_FEE_WALLET', sender_address),
                        trade_details
                    )
                    
                elif coin_symbol == 'USDT':
                    if network == 'solana':
                        logger.info("Executing USDT-SOL transaction...")
                        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'functions', 'scripts'))
                        from usdt_sol_sender import send_transaction as usdt_sol_send
                        
                        trade_details = {
                            'fee': '0',
                            'broker_fee': '0',
                            'brokerTrade': False,
                            'brokerAddress': None
                        }
                        
                        tx_hash = usdt_sol_send(
                            private_key, os.getenv('SOLANA_FEE_PAYER_SECRET'),
                            recipient_address, amount, sender_address, trade_details, None
                        )
                        
                    elif network == 'binance':
                        logger.info("Executing USDT-BNB transaction...")
                        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'functions', 'scripts'))
                        from usdt_bnb_sender import send_transaction as usdt_bnb_send
                        
                        trade_details = {
                            'fee': '0',
                            'broker_fee': '0',
                            'brokerTrade': False,
                            'brokerAddress': None
                        }
                        
                        tx_hash = usdt_bnb_send(
                            os.getenv('BSC_FEE_PAYER_SECRET'), private_key,
                            recipient_address, amount, sender_address, trade_details
                        )
                        
                    elif network == 'tron':
                        logger.info("Executing USDT-TRON transaction...")
                        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'functions', 'scripts'))
                        from usdt_tron_sender import send_token_tx
                        
                        tx_hash = send_token_tx(
                            private_key, recipient_address, amount,
                            'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t'  # USDT contract on Tron
                        )
                        
                    elif network == 'ethereum':
                        logger.info("Executing USDT-ETH transaction...")
                        logger.info(f"About to import USDT ETH sender...")
                        try:
                            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'functions', 'scripts'))
                            logger.info("Path added to sys.path")
                            
                            from usdt_eth_sender import send_transaction as usdt_eth_send
                            logger.info("✅ USDT ETH sender imported successfully")
                            
                            trade_details = {
                                'fee': '0',
                                'broker_fee': '0',
                                'brokerTrade': False,
                                'brokerAddress': None
                            }
                            logger.info("Trade details prepared")
                            
                            logger.info(f"Calling USDT ETH sender with:")
                            logger.info(f"  - recipient: {recipient_address}")
                            logger.info(f"  - amount: {amount}")
                            logger.info(f"  - sender: {sender_address}")
                            logger.info(f"  - private_key: [REDACTED]")
                            
                            tx_hash = usdt_eth_send(
                                private_key, recipient_address, amount, sender_address, trade_details
                            )
                            
                            logger.info(f"USDT ETH sender returned: {tx_hash}")
                            
                        except ImportError as import_error:
                            logger.error(f"Failed to import USDT ETH sender: {import_error}")
                            return {"success": False, "error": f"Import error: {str(import_error)}"}
                        except Exception as eth_error:
                            logger.error(f"Error in USDT ETH transaction: {eth_error}")
                            return {"success": False, "error": f"USDT ETH transaction error: {str(eth_error)}"}
                        
                    else:
                        error_msg = f"USDT network '{network}' not supported"
                        logger.error(error_msg)
                        return {"success": False, "error": error_msg}
                        
                elif coin_symbol == 'BTC':
                    logger.info("Executing BTC transaction...")
                    # Use the forgingblock API for Bitcoin
                    from payments.forgingblock import BitcoinApi
                    
                    btc_api = BitcoinApi()
                    # Get mnemonic from encrypted wallet data
                    wallet = WalletManager.get_wallet_by_id(sender_wallet_id)
                    if wallet:
                        mnemonic = wallet_manager._decrypt_data(wallet['mnemonic_encrypted'])
                        tx_hash = btc_api.send_btc(mnemonic, sender_address, amount, recipient_address)
                    else:
                        return {"success": False, "error": "Could not retrieve wallet mnemonic for BTC transaction"}
                
                else:
                    error_msg = f"Sending functionality not implemented for {coin_symbol}"
                    logger.error(error_msg)
                    return {"success": False, "error": error_msg}
                
                # Check if transaction was successful
                if tx_hash and tx_hash != "Failed":
                    logger.info(f"Transaction successful with hash: {tx_hash}")
                    
                    # Update the sender's balance in database
                    if coin_symbol == 'USDT' and fee_currency != coin_symbol:
                        # For token transactions where fee is in different currency (SOL, BSC, TRON, ETHEREUM)
                        # Only update the token balance, gas fees are handled separately
                        new_token_balance = current_balance - amount_decimal
                        logger.info(f"Updating {coin_symbol} balance from {current_balance} to {new_token_balance}")
                        
                        db.coin_addresses.update_one(
                            {"_id": coin_address["_id"]},
                            {
                                "$set": {
                                    "balance": str(new_token_balance),
                                    "last_balance_update": datetime.now().isoformat()
                                }
                            }
                        )
                        
                        new_balance = float(new_token_balance)
                    else:
                        # For native currencies where fee is in same currency
                        new_balance = current_balance - amount_decimal - estimated_fee
                        logger.info(f"Updating balance from {current_balance} to {new_balance}")
                        
                        db.coin_addresses.update_one(
                            {"_id": coin_address["_id"]},
                            {
                                "$set": {
                                    "balance": str(new_balance),
                                    "last_balance_update": datetime.now().isoformat()
                                }
                            }
                        )
                        
                        new_balance = float(new_balance)
                    
                    logger.info("✅ Transaction completed successfully")
                    return {
                        "success": True,
                        "tx_hash": str(tx_hash),
                        "amount": amount,
                        "fee": float(estimated_fee),
                        "fee_currency": fee_currency,
                        "recipient": recipient_address,
                        "sender": sender_address,
                        "coin": coin_symbol,
                        "network": network,
                        "new_balance": new_balance,
                        "note": f"✅ Successfully sent {amount} {coin_symbol} (fee: {estimated_fee} {fee_currency})"
                    }
                else:
                    error_msg = f"Transaction failed - received hash: {tx_hash}"
                    logger.error(error_msg)
                    return {"success": False, "error": error_msg}
                    
            except Exception as send_error:
                logger.error(f"Error during {coin_symbol} transaction: {send_error}")
                logger.error(f"Error type: {type(send_error).__name__}")
                logger.error(f"Error args: {send_error.args}")
                import traceback
                logger.error(f"Full traceback: {traceback.format_exc()}")
                return {"success": False, "error": f"Transaction error: {str(send_error)}"}
                
        except Exception as e:
            logger.error(f"Error in send_crypto: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error args: {e.args}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return {"success": False, "error": str(e)}


# Handler functions
async def admin_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main admin menu"""
    user_id = update.effective_user.id
    
    if not await AdminWalletManager.is_admin(user_id):
        await update.message.reply_text("❌ Access denied. Admin privileges required.")
        return
    
    # Clear any cached data when starting admin session
    context.user_data.pop("send_crypto_user_id", None)
    context.user_data.pop("send_crypto_wallet_id", None)
    context.user_data.pop("send_crypto_coin", None)
    context.user_data.pop("send_crypto_recipient", None)
    context.user_data.pop("send_crypto_amount", None)
    context.user_data.pop("admin_action", None)
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👤 User Wallet Info", callback_data="admin_user_wallet"),
            InlineKeyboardButton("💸 Send Crypto", callback_data="admin_send_crypto")
        ],
        [
            InlineKeyboardButton("📊 All Active Trades", callback_data="admin_all_trades"),
            InlineKeyboardButton("🔧 System Status", callback_data="admin_system_status")
        ],
        [
            InlineKeyboardButton("📈 Platform Stats", callback_data="admin_platform_stats"),
            InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
        ]
    ])
    
    await update.message.reply_text(
        f"🛠️ <b>Admin Panel</b>\n\n"
        f"Welcome, Admin! Select an option:",
        parse_mode="HTML",
        reply_markup=keyboard
    )


async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin callback queries"""
    query = update.callback_query
    user_id = query.from_user.id
    
    # Add comprehensive logging
    logger.info(f"=== ADMIN CALLBACK HANDLER TRIGGERED ===")
    logger.info(f"Callback data: {query.data}")
    logger.info(f"User ID: {user_id}")
    logger.info(f"Admin ID from config: {ADMIN_ID}")
    
    await query.answer()
    
    if not await AdminWalletManager.is_admin(user_id):
        logger.warning(f"Non-admin user {user_id} attempted to access admin functionality")
        await query.edit_message_text("❌ Access denied.")
        return
    
    logger.info(f"Admin {user_id} accessing: {query.data}")
    
    if query.data == "admin_user_wallet":
        await admin_user_wallet_handler(update, context)
    elif query.data == "admin_send_crypto":
        await admin_send_crypto_handler(update, context)
    elif query.data == "admin_all_trades":
        await admin_all_trades_handler(update, context)
    elif query.data == "admin_system_status":
        await admin_system_status_handler(update, context)
    elif query.data == "admin_platform_stats":
        await admin_platform_stats_handler(update, context)
    elif query.data == "admin_menu":
        logger.info(f"Admin {user_id} requesting admin menu")
        await show_admin_menu(update, context)
    elif query.data.startswith("admin_select_coin_"):
        await handle_coin_selection_callback(update, context)
    elif query.data.startswith("admin_send_from_"):
        user_id_to_send = query.data.replace("admin_send_from_", "")
        context.user_data["send_crypto_user_id"] = user_id_to_send
        await admin_send_crypto_handler(update, context)
    elif query.data.startswith("admin_refresh_"):
        user_id_to_refresh = query.data.replace("admin_refresh_", "")
        await admin_refresh_user_wallet(update, context, user_id_to_refresh)
    elif query.data.startswith("admin_confirm_send_"):
        await handle_send_confirmation(update, context)
    else:
        logger.warning(f"Unhandled admin callback: {query.data}")
        await query.edit_message_text(
            f"❌ Unknown admin action: {query.data}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
            ]])
        )


async def admin_user_wallet_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user wallet lookup"""
    query = update.callback_query
    await query.answer()
    
    # Clear any cached data to start fresh
    context.user_data.pop("send_crypto_user_id", None)
    context.user_data.pop("send_crypto_wallet_id", None)
    context.user_data.pop("send_crypto_coin", None)
    context.user_data.pop("send_crypto_recipient", None)
    context.user_data.pop("send_crypto_amount", None)
    context.user_data.pop("admin_action", None)
    
    await query.edit_message_text(
        "👤 <b>User Wallet Lookup</b>\n\n"
        "Please enter the User ID (Telegram ID) to lookup their wallet information:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
        ]])
    )
    
    context.user_data["admin_action"] = "lookup_user_wallet"


async def admin_send_crypto_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle crypto sending setup"""
    query = update.callback_query
    await query.answer()
    
    # Clear any cached data to start fresh (except if coming from wallet lookup)
    if not query.data.startswith("admin_send_from_"):
        context.user_data.pop("send_crypto_user_id", None)
        context.user_data.pop("send_crypto_wallet_id", None)
        context.user_data.pop("send_crypto_coin", None)
        context.user_data.pop("send_crypto_recipient", None)
        context.user_data.pop("send_crypto_amount", None)
        context.user_data.pop("admin_action", None)
    
    # Check if user ID is already set (from wallet lookup)
    if context.user_data.get("send_crypto_user_id"):
        await handle_send_crypto_step1_with_user_id(update, context)
        return
    
    await query.edit_message_text(
        "💸 <b>Send Crypto from User Wallet</b>\n\n"
        "Please enter the User ID (Telegram ID) whose wallet you want to send from:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
        ]])
    )
    
    context.user_data["admin_action"] = "send_crypto_step1"


async def admin_all_trades_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all active trades"""
    query = update.callback_query
    await query.answer()
    
    try:
        active_trades = TradeClient.get_all_active_trades()
        
        if not active_trades:
            await query.edit_message_text(
                "📊 <b>Active Trades</b>\n\n"
                "No active trades found.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
                ]])
            )
            return
        
        trades_text = f"📊 <b>Active Trades ({len(active_trades)})</b>\n\n"
        
        for i, trade in enumerate(active_trades[:10]):  # Show first 10
            trade_id = trade.get('_id', 'Unknown')
            seller_id = trade.get('seller_id', 'Unknown')
            buyer_id = trade.get('buyer_id', 'None')
            amount = trade.get('price', 0)
            currency = trade.get('currency', 'Unknown')
            trade_type = trade.get('trade_type', 'Unknown')
            
            trades_text += f"<b>{i+1}. Trade #{trade_id[:8]}...</b>\n"
            trades_text += f"   💰 {amount} {currency}\n"
            trades_text += f"   🔄 Type: {trade_type}\n"
            trades_text += f"   👤 Seller: {seller_id}\n"
            trades_text += f"   🛒 Buyer: {buyer_id if buyer_id != '' else 'Waiting...'}\n\n"
        
        if len(active_trades) > 10:
            trades_text += f"... and {len(active_trades) - 10} more trades\n"
        
        await query.edit_message_text(
            trades_text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
            ]])
        )
        
    except Exception as e:
        logger.error(f"Error getting active trades: {e}")
        await query.edit_message_text(
            f"❌ Error getting active trades: {str(e)}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
            ]])
        )


async def admin_system_status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show system status"""
    query = update.callback_query
    await query.answer()
    
    try:
        # Get basic system stats
        total_users = db.wallets.count_documents({})
        active_trades = len(TradeClient.get_all_active_trades())
        total_trades = db.trades.count_documents({})
        
        status_text = f"🔧 <b>System Status</b>\n\n"
        status_text += f"👥 <b>Total Wallets:</b> {total_users}\n"
        status_text += f"📊 <b>Active Trades:</b> {active_trades}\n"
        status_text += f"📈 <b>Total Trades:</b> {total_trades}\n\n"
        
        # Check database connection
        try:
            db.admin.command('ismaster')
            db_status = "🟢 Connected"
        except Exception:
            db_status = "🔴 Disconnected"
        
        status_text += f"🗄️ <b>Database:</b> {db_status}\n"
        status_text += f"🤖 <b>Bot Status:</b> 🟢 Running\n"
        
        await query.edit_message_text(
            status_text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔄 Refresh", callback_data="admin_system_status"),
                InlineKeyboardButton("🔙 Back", callback_data="admin_menu")
            ]])
        )
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        await query.edit_message_text(
            f"❌ Error getting system status: {str(e)}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
            ]])
        )


async def admin_platform_stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show platform statistics"""
    query = update.callback_query
    await query.answer()
    
    try:
        # Calculate platform statistics
        total_wallets = db.wallets.count_documents({})
        total_trades = db.trades.count_documents({})
        completed_trades = db.trades.count_documents({"is_completed": True})
        active_trades = db.trades.count_documents({"is_active": True})
        
        # Get trade types
        crypto_fiat_trades = db.trades.count_documents({"trade_type": "CryptoToFiat"})
        crypto_crypto_trades = db.trades.count_documents({"trade_type": "CryptoCrypto"})
        
        completion_rate = (completed_trades / total_trades * 100) if total_trades > 0 else 0
        
        stats_text = f"📈 <b>Platform Statistics</b>\n\n"
        stats_text += f"👥 <b>Total Users:</b> {total_wallets}\n"
        stats_text += f"📊 <b>Total Trades:</b> {total_trades}\n"
        stats_text += f"✅ <b>Completed:</b> {completed_trades}\n"
        stats_text += f"🔄 <b>Active:</b> {active_trades}\n"
        stats_text += f"📈 <b>Success Rate:</b> {completion_rate:.1f}%\n\n"
        
        stats_text += f"<b>Trade Types:</b>\n"
        stats_text += f"💰 Crypto→Fiat: {crypto_fiat_trades}\n"
        stats_text += f"💱 Crypto→Crypto: {crypto_crypto_trades}\n\n"
        
        # Most used currencies
        try:
            pipeline = [
                {"$group": {"_id": "$currency", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 5}
            ]
            
            top_currencies = list(db.trades.aggregate(pipeline))
            if top_currencies:
                stats_text += f"<b>Top Currencies:</b>\n"
                for curr in top_currencies:
                    stats_text += f"• {curr['_id']}: {curr['count']} trades\n"
        except Exception as e:
            logger.error(f"Error getting currency stats: {e}")
        
        await query.edit_message_text(
            stats_text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔄 Refresh", callback_data="admin_platform_stats"),
                InlineKeyboardButton("🔙 Back", callback_data="admin_menu")
            ]])
        )
        
    except Exception as e:
        logger.error(f"Error getting platform stats: {e}")
        await query.edit_message_text(
            f"❌ Error getting platform stats: {str(e)}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
            ]])
        )


async def show_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin menu"""
    query = update.callback_query
    await query.answer()
    
    # Clear any cached data when returning to main menu
    context.user_data.pop("send_crypto_user_id", None)
    context.user_data.pop("send_crypto_wallet_id", None)
    context.user_data.pop("send_crypto_coin", None)
    context.user_data.pop("send_crypto_recipient", None)
    context.user_data.pop("send_crypto_amount", None)
    context.user_data.pop("admin_action", None)
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👤 User Wallet Info", callback_data="admin_user_wallet"),
            InlineKeyboardButton("💸 Send Crypto", callback_data="admin_send_crypto")
        ],
        [
            InlineKeyboardButton("📊 All Active Trades", callback_data="admin_all_trades"),
            InlineKeyboardButton("🔧 System Status", callback_data="admin_system_status")
        ],
        [
            InlineKeyboardButton("📈 Platform Stats", callback_data="admin_platform_stats"),
            InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
        ]
    ])
    
    await query.edit_message_text(
        f"🛠️ <b>Admin Panel</b>\n\n"
        f"Welcome, Admin! Select an option:",
        parse_mode="HTML",
        reply_markup=keyboard
    )


async def admin_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin text input"""
    user_id = update.effective_user.id
    
    if not await AdminWalletManager.is_admin(user_id):
        return
    
    admin_action = context.user_data.get("admin_action")
    
    if admin_action == "lookup_user_wallet":
        await handle_user_wallet_lookup(update, context)
    elif admin_action == "send_crypto_step1":
        await handle_send_crypto_step1(update, context)
    elif admin_action == "send_crypto_step3":
        await handle_send_crypto_step3(update, context)
    elif admin_action == "send_crypto_step4":
        await handle_send_crypto_step4(update, context)


async def handle_user_wallet_lookup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user wallet lookup"""
    try:
        lookup_user_id = update.message.text.strip()
        
        # Get wallet info
        wallet_info = await AdminWalletManager.get_user_wallet_info(lookup_user_id)
        
        if not wallet_info:
            await update.message.reply_text(
                f"❌ No wallet found for user ID: {lookup_user_id}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
                ]])
            )
            # Clear the cached action so user can try again
            context.user_data.pop("admin_action", None)
            return
        
        wallet = wallet_info['wallet']
        coin_balances = wallet_info['coin_addresses']
        stats = wallet_info['stats']
        
        # Format wallet information
        wallet_text = f"👤 <b>User Wallet Info</b>\n\n"
        wallet_text += f"🆔 <b>User ID:</b> <code>{lookup_user_id}</code>\n"
        wallet_text += f"💼 <b>Wallet:</b> {wallet['wallet_name']}\n"
        wallet_text += f"🔐 <b>Wallet ID:</b> <code>{wallet['_id']}</code>\n"
        wallet_text += f"🕐 <b>Created:</b> {wallet['created_at'][:16]}\n\n"
        
        wallet_text += f"📊 <b>Statistics:</b>\n"
        wallet_text += f"• Total coins: {stats['total_coins']}\n"
        wallet_text += f"• With balance: {stats['coins_with_balance']}\n\n"
        
        wallet_text += f"💰 <b>Balances:</b>\n"
        for coin in coin_balances:
            status_icon = "🟢" if coin['balance'] > 0 else "⚪"
            coin_emoji = {
                'BTC': EmojiEnums.BITCOIN.value,
                'LTC': EmojiEnums.LITECOIN.value,
                'DOGE': EmojiEnums.DOGECOIN.value,
                'ETH': EmojiEnums.ETHEREUM.value,
                'SOL': EmojiEnums.SOLANA.value,
                'USDT': EmojiEnums.TETHER.value,
                'BNB': EmojiEnums.YELLOW_CIRCLE.value,
                'TRX': EmojiEnums.TRON.value
            }.get(coin['symbol'], '🪙')
            
            wallet_text += f"{status_icon} {coin_emoji} <b>{coin['symbol']}:</b> {coin['balance']}\n"
            if coin['balance'] > 0:
                display_address = f"{coin['address'][:12]}...{coin['address'][-8:]}"
                wallet_text += f"   📍 <code>{display_address}</code>\n"
        
        # Create action buttons
        keyboard = [
            [InlineKeyboardButton(f"💸 Send from this wallet", callback_data=f"admin_send_from_{lookup_user_id}")],
            [InlineKeyboardButton("🔄 Refresh Balances", callback_data=f"admin_refresh_{lookup_user_id}")],
            [InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")]
        ]
        
        await update.message.reply_text(
            wallet_text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        context.user_data.pop("admin_action", None)
        
    except Exception as e:
        logger.error(f"Error in user wallet lookup: {e}")
        await update.message.reply_text(
            f"❌ Error looking up wallet: {str(e)}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
            ]])
        )
        context.user_data.pop("admin_action", None)


async def handle_send_crypto_step1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle send crypto step 1 - user ID input"""
    try:
        sender_user_id = update.message.text.strip()
        context.user_data["send_crypto_user_id"] = sender_user_id
        await handle_send_crypto_step1_with_user_id(update, context)
        
    except Exception as e:
        logger.error(f"Error in send crypto step 1: {e}")
        await update.message.reply_text(
            f"❌ Error: {str(e)}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
            ]])
        )
        context.user_data.pop("admin_action", None)


async def handle_send_crypto_step1_with_user_id(update, context):
    """Handle send crypto with existing user ID"""
    try:
        sender_user_id = context.user_data["send_crypto_user_id"]
        
        # Get wallet info to verify it exists
        wallet_info = await AdminWalletManager.get_user_wallet_info(sender_user_id)
        
        if not wallet_info:
            message_text = f"❌ No wallet found for user ID: {sender_user_id}"
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
            ]])
            
            if hasattr(update, 'message') and update.message:
                await update.message.reply_text(message_text, reply_markup=keyboard)
            elif hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.edit_message_text(message_text, reply_markup=keyboard)
            
            # Clear cached data so user can try again
            context.user_data.pop("admin_action", None)
            context.user_data.pop("send_crypto_user_id", None)
            return
        
        # Store wallet info
        context.user_data["send_crypto_wallet_id"] = wallet_info['wallet']['_id']
        context.user_data["admin_action"] = "send_crypto_step2"
        
        # Show available coins with balances
        coin_buttons = []
        for coin in wallet_info['coin_addresses']:
            if coin['balance'] > 0:
                coin_emoji = {
                    'BTC': EmojiEnums.BITCOIN.value,
                    'LTC': EmojiEnums.LITECOIN.value,
                    'DOGE': EmojiEnums.DOGECOIN.value,
                    'ETH': EmojiEnums.ETHEREUM.value,
                    'SOL': EmojiEnums.SOLANA.value,
                    'USDT': EmojiEnums.TETHER.value,
                    'BNB': EmojiEnums.YELLOW_CIRCLE.value,
                    'TRX': EmojiEnums.TRON.value
                }.get(coin['symbol'], '🪙')
                
                coin_buttons.append([InlineKeyboardButton(
                    f"{coin_emoji} {coin['symbol']} ({coin['balance']})",
                    callback_data=f"admin_select_coin_{coin['symbol']}"
                )])
        
        if not coin_buttons:
            message_text = f"❌ No coins with balance found for user {sender_user_id}"
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
            ]])
            
            if hasattr(update, 'message') and update.message:
                await update.message.reply_text(message_text, reply_markup=keyboard)
            elif hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.edit_message_text(message_text, reply_markup=keyboard)
            
            context.user_data.pop("admin_action", None)
            return
        
        coin_buttons.append([InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")])
        
        message_text = (
            f"💰 <b>Select Coin to Send</b>\n\n"
            f"👤 <b>From User:</b> {sender_user_id}\n\n"
            f"Choose which coin to send:"
        )
        keyboard = InlineKeyboardMarkup(coin_buttons)
        
        if hasattr(update, 'message') and update.message:
            await update.message.reply_text(message_text, parse_mode="HTML", reply_markup=keyboard)
        elif hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(message_text, parse_mode="HTML", reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error in send crypto step 1 with user ID: {e}")
        message_text = f"❌ Error: {str(e)}"
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
        ]])
        
        if hasattr(update, 'message') and update.message:
            await update.message.reply_text(message_text, reply_markup=keyboard)
        elif hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(message_text, reply_markup=keyboard)
        
        # Clear cached data so user can try again
        context.user_data.pop("admin_action", None)
        context.user_data.pop("send_crypto_user_id", None)


async def handle_coin_selection_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle coin selection for sending"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("admin_select_coin_"):
        coin_symbol = query.data.replace("admin_select_coin_", "")
        context.user_data["send_crypto_coin"] = coin_symbol
        context.user_data["admin_action"] = "send_crypto_step3"
        
        await query.edit_message_text(
            f"📍 <b>Enter Recipient Address</b>\n\n"
            f"👤 <b>From User:</b> {context.user_data['send_crypto_user_id']}\n"
            f"💰 <b>Coin:</b> {coin_symbol}\n\n"
            f"Please enter the recipient address for {coin_symbol}:",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
            ]])
        )


async def handle_send_crypto_step3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle send crypto step 3 - recipient address"""
    try:
        recipient_address = update.message.text.strip()
        
        # Basic address validation could be added here
        context.user_data["send_crypto_recipient"] = recipient_address
        context.user_data["admin_action"] = "send_crypto_step4"
        
        await update.message.reply_text(
            f"💸 <b>Enter Amount to Send</b>\n\n"
            f"👤 <b>From User:</b> {context.user_data['send_crypto_user_id']}\n"
            f"💰 <b>Coin:</b> {context.user_data['send_crypto_coin']}\n"
            f"📍 <b>To:</b> <code>{recipient_address[:20]}...</code>\n\n"
            f"Please enter the amount of {context.user_data['send_crypto_coin']} to send:",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
            ]])
        )
        
    except Exception as e:
        logger.error(f"Error in send crypto step 3: {e}")
        await update.message.reply_text(
            f"❌ Error: {str(e)}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
            ]])
        )


async def handle_send_crypto_step4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle send crypto step 4 - amount and confirmation"""
    try:
        amount_str = update.message.text.strip()
        amount = float(amount_str)
        
        if amount <= 0:
            await update.message.reply_text("❌ Amount must be greater than 0. Please try again.")
            return
        
        # Get transaction details for fee calculation
        user_id = context.user_data['send_crypto_user_id']
        coin = context.user_data['send_crypto_coin']
        recipient = context.user_data['send_crypto_recipient']
        wallet_id = context.user_data['send_crypto_wallet_id']
        
        logger.info(f"=== STEP 4: AMOUNT CONFIRMATION ===")
        logger.info(f"User: {user_id}, Coin: {coin}, Amount: {amount}")
        
        # Get wallet and coin info for fee calculation
        coin_address = WalletManager.get_wallet_coin_address(wallet_id, coin)
        if not coin_address:
            await update.message.reply_text(
                "❌ Error: Could not find coin address. Please try again.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
                ]])
            )
            return
        
        # Get current balance - use database balance for consistency with wallet display
        current_balance = Decimal(str(coin_address.get('balance', 0)))
        amount_decimal = Decimal(str(amount))
        network = coin_address.get('network', '')
        
        logger.info(f"Database balance for {coin} in confirmation: {current_balance}")
        
        # If balance is zero, try to refresh it
        if current_balance == 0:
            logger.info("Balance is zero in confirmation, attempting to refresh...")
            wallet_manager = WalletManager()
            await wallet_manager.refresh_wallet_balances(wallet_id)
            
            # Get updated coin address after refresh
            coin_address = WalletManager.get_wallet_coin_address(wallet_id, coin)
            if coin_address:
                current_balance = Decimal(str(coin_address.get('balance', 0)))
                logger.info(f"Refreshed balance for {coin} in confirmation: {current_balance}")
            else:
                logger.error("Failed to get updated coin address after refresh in confirmation")
                await update.message.reply_text(
                    f"❌ Error: Failed to refresh {coin} balance. Please try again.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
                    ]])
                )
                return
        
        # Calculate estimated fee
        estimated_fee, fee_currency = AdminWalletManager.get_transaction_fee(coin, network)
        required_total = amount_decimal + estimated_fee
        
        logger.info(f"Balance check: {current_balance} available, {required_total} required (amount: {amount_decimal} + fee: {estimated_fee})")
        
        # Store amount for confirmation
        context.user_data["send_crypto_amount"] = amount
        
        # Build confirmation message with fee info
        confirmation_text = f"⚠️ <b>Confirm Transaction</b>\n\n"
        confirmation_text += f"👤 <b>From User:</b> {user_id}\n"
        confirmation_text += f"💰 <b>Coin:</b> {coin}"
        
        if network:
            confirmation_text += f" ({network.title()})\n"
        else:
            confirmation_text += "\n"
            
        # Different display logic for tokens vs native currencies
        if coin == 'USDT' and fee_currency != coin:
            # For tokens on other networks (SOL, BSC, TRON), show both token balance and gas balance
            gas_coin_address = WalletManager.get_wallet_coin_address(wallet_id, fee_currency)
            if gas_coin_address:
                gas_balance = Decimal(str(gas_coin_address.get('balance', 0)))
                
                # If gas balance is zero, try to refresh it
                if gas_balance == 0:
                    logger.info(f"Gas balance is zero in confirmation, attempting to refresh {fee_currency}...")
                    await wallet_manager.refresh_wallet_balances(wallet_id)
                    
                    # Get updated gas coin address after refresh
                    gas_coin_address = WalletManager.get_wallet_coin_address(wallet_id, fee_currency)
                    if gas_coin_address:
                        gas_balance = Decimal(str(gas_coin_address.get('balance', 0)))
                        logger.info(f"Refreshed gas balance for {fee_currency} in confirmation: {gas_balance}")
                    else:
                        logger.error("Failed to get updated gas coin address after refresh in confirmation")
                        await update.message.reply_text(
                            f"❌ Error: Failed to refresh {fee_currency} balance. Please try again.",
                            reply_markup=InlineKeyboardMarkup([[
                                InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
                            ]])
                        )
                        return
                
                confirmation_text += f"💳 <b>{coin} Balance:</b> {current_balance} {coin}\n"
                confirmation_text += f"⛽ <b>{fee_currency} Balance (for gas):</b> {gas_balance} {fee_currency}\n"
                confirmation_text += f"💸 <b>Amount to Send:</b> {amount} {coin}\n"
                confirmation_text += f"⚡ <b>Gas Fee:</b> {estimated_fee} {fee_currency}\n\n"
                
                # Check both balances separately
                token_ok = current_balance >= amount_decimal
                gas_ok = gas_balance >= estimated_fee
                
                if token_ok and gas_ok:
                    confirmation_text += f"✅ <b>Token Balance:</b> Sufficient ({current_balance - amount_decimal} {coin} remaining)\n"
                    confirmation_text += f"✅ <b>Gas Balance:</b> Sufficient ({gas_balance - estimated_fee} {fee_currency} remaining)\n"
                    balance_ok = True
                else:
                    if not token_ok:
                        token_shortfall = amount_decimal - current_balance
                        confirmation_text += f"❌ <b>Token Balance:</b> Need {token_shortfall} more {coin}\n"
                    else:
                        confirmation_text += f"✅ <b>Token Balance:</b> Sufficient\n"
                        
                    if not gas_ok:
                        gas_shortfall = estimated_fee - gas_balance
                        confirmation_text += f"❌ <b>Gas Balance:</b> Need {gas_shortfall} more {fee_currency}\n"
                    else:
                        confirmation_text += f"✅ <b>Gas Balance:</b> Sufficient\n"
                        
                    balance_ok = False
            else:
                confirmation_text += f"❌ <b>Error:</b> No {fee_currency} address found for gas fees\n"
                balance_ok = False
        else:
            # For native currencies and USDT on Ethereum (where fee is also in USDT)
            confirmation_text += f"💳 <b>Current Balance:</b> {current_balance} {coin}\n"
            confirmation_text += f"💸 <b>Amount to Send:</b> {amount} {coin}\n"
            confirmation_text += f"⚡ <b>Transaction Fee:</b> {estimated_fee} {fee_currency}\n"
            confirmation_text += f"🔢 <b>Total Required:</b> {amount_decimal + estimated_fee} {fee_currency}\n"
            confirmation_text += f"💰 <b>Remaining Balance:</b> {current_balance - amount_decimal - estimated_fee} {coin}\n\n"
            
            # Balance status
            required_total = amount_decimal + estimated_fee
            if current_balance >= required_total:
                confirmation_text += f"✅ <b>Status:</b> Sufficient balance\n"
                balance_ok = True
            else:
                shortfall = required_total - current_balance
                confirmation_text += f"❌ <b>Status:</b> Insufficient balance (need {shortfall} more {fee_currency})\n"
                balance_ok = False
            
        confirmation_text += f"📍 <b>To Address:</b> <code>{recipient}</code>\n\n"
        
        if balance_ok:
            confirmation_text += f"⚠️ <b>WARNING:</b> This action cannot be undone!\n\n"
            confirmation_text += f"Are you sure you want to proceed with this transaction?"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ Confirm Send", callback_data="admin_confirm_send_yes"),
                    InlineKeyboardButton("❌ Cancel", callback_data="admin_confirm_send_no")
                ],
                [InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")]
            ])
        else:
            confirmation_text += f"❌ <b>Cannot proceed:</b> Insufficient balance to cover amount + fees.\n\n"
            confirmation_text += f"Please reduce the amount or wait for more funds to be deposited."
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")]
            ])
        
        await update.message.reply_text(
            confirmation_text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        
        context.user_data.pop("admin_action", None)
        
    except ValueError:
        await update.message.reply_text("❌ Invalid amount. Please enter a valid number.")
    except Exception as e:
        logger.error(f"Error in send crypto step 4: {e}")
        await update.message.reply_text(
            f"❌ Error: {str(e)}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
            ]])
        )


async def handle_send_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle send confirmation"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "admin_confirm_send_yes":
        # Proceed with the transaction
        await query.edit_message_text(
            f"⏳ <b>Processing Transaction...</b>\n\n"
            f"Please wait while we send the cryptocurrency.\n"
            f"This may take a few moments to complete.",
            parse_mode="HTML"
        )
        
        try:
            # Get transaction details from context
            wallet_id = context.user_data['send_crypto_wallet_id']
            coin_symbol = context.user_data['send_crypto_coin']
            recipient = context.user_data['send_crypto_recipient']
            amount = context.user_data['send_crypto_amount']
            admin_id = query.from_user.id
            
            logger.info(f"=== ADMIN CONFIRMATION PROCESSING ===")
            logger.info(f"Admin {admin_id} confirming send of {amount} {coin_symbol} to {recipient}")
            
            # Perform the transaction
            result = await AdminWalletManager.send_crypto(
                wallet_id, coin_symbol, recipient, amount, str(admin_id)
            )
            
            if result['success']:
                success_text = f"✅ <b>Transaction Successful!</b>\n\n"
                success_text += f"💰 <b>Amount:</b> {amount} {coin_symbol}\n"
                
                fee_currency = result.get('fee_currency', coin_symbol)
                success_text += f"💸 <b>Network Fee:</b> {result.get('fee', 'N/A')} {fee_currency}\n"
                success_text += f"📍 <b>To:</b> <code>{recipient}</code>\n"
                success_text += f"📤 <b>From:</b> <code>{result.get('sender', 'N/A')}</code>\n"
                
                if result.get('network'):
                    success_text += f"🌐 <b>Network:</b> {result['network'].title()}\n"
                
                success_text += f"🔗 <b>TX Hash:</b> <code>{result.get('tx_hash', 'N/A')}</code>\n"
                success_text += f"💳 <b>New {coin_symbol} Balance:</b> {result.get('new_balance', 'N/A')} {coin_symbol}\n\n"
                
                if result.get('note'):
                    success_text += f"ℹ️ <b>Note:</b> {result['note']}\n\n"
                
                success_text += f"The transaction has been completed successfully and the blockchain has been updated."
                
                logger.info(f"✅ Transaction successful for admin {admin_id}")
                
                await query.edit_message_text(
                    success_text,
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
                    ]])
                )
            else:
                error_text = f"❌ <b>Transaction Failed</b>\n\n"
                error_text += f"💰 <b>Attempted Amount:</b> {amount} {coin_symbol}\n"
                error_text += f"📍 <b>Recipient:</b> <code>{recipient}</code>\n\n"
                error_text += f"❗ <b>Error:</b> {result.get('error', 'Unknown error')}\n\n"
                error_text += f"Please check the wallet balance and try again, or contact support if the issue persists."
                
                logger.error(f"❌ Transaction failed for admin {admin_id}: {result.get('error')}")
                
                await query.edit_message_text(
                    error_text,
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
                    ]])
                )
            
        except Exception as e:
            logger.error(f"Error executing transaction for admin {admin_id}: {e}")
            await query.edit_message_text(
                f"❌ <b>Transaction Error</b>\n\n"
                f"An unexpected error occurred while processing the transaction:\n\n"
                f"<code>{str(e)}</code>\n\n"
                f"Please try again or contact support if the issue persists.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
                ]])
            )
        
        # Clear context data
        context.user_data.pop("send_crypto_user_id", None)
        context.user_data.pop("send_crypto_wallet_id", None)
        context.user_data.pop("send_crypto_coin", None)
        context.user_data.pop("send_crypto_recipient", None)
        context.user_data.pop("send_crypto_amount", None)
        
    elif query.data == "admin_confirm_send_no":
        # Cancel the transaction
        logger.info(f"Admin {query.from_user.id} cancelled transaction")
        
        await query.edit_message_text(
            f"❌ <b>Transaction Cancelled</b>\n\n"
            f"The transaction has been cancelled by admin.\n"
            f"No funds were sent and no fees were charged.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
            ]])
        )
        
        # Clear context data
        context.user_data.pop("send_crypto_user_id", None)
        context.user_data.pop("send_crypto_wallet_id", None)
        context.user_data.pop("send_crypto_coin", None)
        context.user_data.pop("send_crypto_recipient", None)
        context.user_data.pop("send_crypto_amount", None)


async def admin_refresh_user_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: str):
    """Refresh a specific user's wallet balances"""
    query = update.callback_query
    await query.answer()
    
    try:
        wallet_info = await AdminWalletManager.get_user_wallet_info(user_id)
        
        if not wallet_info:
            await query.edit_message_text(
                f"❌ No wallet found for user ID: {user_id}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
                ]])
            )
            return
        
        await query.edit_message_text(
            f"🔄 <b>Refreshing Balances...</b>\n\n"
            f"Please wait while we update the wallet balances for user {user_id}.",
            parse_mode="HTML"
        )
        
        # Refresh balances
        wallet_manager = WalletManager()
        success = await wallet_manager.refresh_wallet_balances(wallet_info['wallet']['_id'])
        
        if success:
            # Get updated wallet info
            updated_wallet_info = await AdminWalletManager.get_user_wallet_info(user_id)
            
            refresh_text = f"✅ <b>Balances Refreshed!</b>\n\n"
            refresh_text += f"👤 <b>User ID:</b> {user_id}\n\n"
            refresh_text += f"💰 <b>Updated Balances:</b>\n"
            
            for coin in updated_wallet_info['coin_addresses']:
                status_icon = "🟢" if coin['balance'] > 0 else "⚪"
                coin_emoji = {
                    'BTC': EmojiEnums.BITCOIN.value,
                    'LTC': EmojiEnums.LITECOIN.value,
                    'DOGE': EmojiEnums.DOGECOIN.value,
                    'ETH': EmojiEnums.ETHEREUM.value,
                    'SOL': EmojiEnums.SOLANA.value,
                    'USDT': EmojiEnums.TETHER.value,
                    'BNB': EmojiEnums.YELLOW_CIRCLE.value,
                    'TRX': EmojiEnums.TRON.value
                }.get(coin['symbol'], '🪙')
                
                refresh_text += f"{status_icon} {coin_emoji} <b>{coin['symbol']}:</b> {coin['balance']}\n"
            
            await query.edit_message_text(
                refresh_text,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
                ]])
            )
        else:
            await query.edit_message_text(
                f"⚠️ <b>Refresh Partially Completed</b>\n\n"
                f"Some balances for user {user_id} may not have been updated due to network issues.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Try Again", callback_data=f"admin_refresh_{user_id}")],
                    [InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")]
                ])
            )
        
    except Exception as e:
        logger.error(f"Error refreshing user wallet: {e}")
        await query.edit_message_text(
            f"❌ Error refreshing wallet for user {user_id}: {str(e)}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_menu")
            ]])
        )


def register_handlers(application):
    """Register admin handlers"""
    # Command handlers
    application.add_handler(CommandHandler("admin", admin_menu_handler))
    
    # Callback query handlers - using default group
    application.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^admin_"))
    
    # Message handler for admin inputs (with low priority)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE,
        admin_message_handler
    ), group=10)  # Low priority to not interfere with other handlers 