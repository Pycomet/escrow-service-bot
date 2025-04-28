#!/usr/bin/env python3

from functions.trade import TradeClient
import json
from bson import json_util
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def print_active_trades():
    """Print all active trades in the database"""
    logger.info("Fetching active trades...")
    try:
        active_trades = TradeClient.get_all_active_trades()
        
        print(f"\n===== Active Trades ({len(active_trades)}) =====")
        
        if not active_trades:
            print("No active trades found in the database.")
            return
        
        for i, trade in enumerate(active_trades, 1):
            # Convert ObjectId to string for better readability
            trade_str = json.loads(json_util.dumps(trade))
            print(f"\n--- Trade {i} ---")
            print(f"ID: {trade_str.get('_id')}")
            print(f"Seller ID: {trade_str.get('seller_id')}")
            print(f"Buyer ID: {trade_str.get('buyer_id')}")
            print(f"Price: {trade_str.get('price')} {trade_str.get('currency')}")
            print(f"Is Active: {trade_str.get('is_active')}")
            print(f"Is Paid: {trade_str.get('is_paid')}")
            print(f"Created At: {trade_str.get('created_at')}")
            print(f"Updated At: {trade_str.get('updated_at')}")
    except Exception as e:
        logger.error(f"Error fetching active trades: {e}")
        raise

if __name__ == "__main__":
    print_active_trades() 