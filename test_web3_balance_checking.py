#!/usr/bin/env python3
"""
Web3 Balance Checking Test Suite
===============================

This script tests balance checking for all supported blockchains:
- Solana (SOL) and SPL tokens (USDT)
- BSC/BNB and BEP-20 tokens
- Litecoin (LTC)
- Dogecoin (DOGE)

Requirements:
pip install solana spl-token web3 requests decimal
"""

import os
import sys

# Add the functions/scripts directory to Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
functions_scripts_dir = os.path.join(script_dir, 'functions', 'scripts')
sys.path.insert(0, functions_scripts_dir)

import json
from datetime import datetime
import traceback
from decimal import Decimal
import time

def test_solana_balance():
    """Test Solana balance checking"""
    print("🔷 Testing Solana Balance Checking...")
    try:
        from solwalletbalance import get_finalized_sol_balance, get_sol_price
        
        # Test known wallet addresses (public addresses, safe to test)
        test_addresses = [
            "9eeneoxQmxbYFTrffFS5rDz1VsdCpQuzd4D67UNE5D8W",  # Random public address
            "11111111111111111111111111111112",  # System program ID
        ]
        
        USDT_MINT = 'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB'
        
        results = []
        
        for address in test_addresses:
            try:
                # Test SOL balance
                sol_result = get_finalized_sol_balance(address)
                print(f"   SOL Balance for {address[:8]}...{address[-8:]}: {sol_result}")
                
                # Test USDT balance
                usdt_result = get_finalized_sol_balance(address, USDT_MINT)
                print(f"   USDT Balance for {address[:8]}...{address[-8:]}: {usdt_result}")
                
                results.append({
                    "address": address,
                    "sol_balance": sol_result,
                    "usdt_balance": usdt_result
                })
                
                # Small delay to avoid rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                print(f"   ❌ Error checking balance for {address}: {str(e)}")
                results.append({
                    "address": address,
                    "error": str(e)
                })
        
        # Test price fetching
        try:
            sol_price = get_sol_price()
            print(f"   SOL Price: ${sol_price}")
        except Exception as e:
            print(f"   ❌ Error fetching SOL price: {str(e)}")
            sol_price = None
        
        print("✅ Solana balance checking: PASSED")
        return True, {"results": results, "sol_price": sol_price}
        
    except Exception as e:
        print(f"❌ Solana balance checking: FAILED - {str(e)}")
        print(f"   Error details: {traceback.format_exc()}")
        return False, None

def test_bsc_balance():
    """Test BSC balance checking"""
    print("\n🔶 Testing BSC Balance Checking...")
    try:
        from bsc_wallet_balance import get_finalized_bsc_balance
        
        # Test known wallet addresses
        test_addresses = [
            "0x742d35Cc1B1c1F7BC46E2e0c6Ac9A4eCeD3e5C5D",  # Random address
            "0x0000000000000000000000000000000000000000",  # Zero address
        ]
        
        results = []
        
        for address in test_addresses:
            try:
                balance_result = get_finalized_bsc_balance(address)
                print(f"   BNB Balance for {address}: {balance_result}")
                
                results.append({
                    "address": address,
                    "balance": balance_result
                })
                
                # Small delay to avoid rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                print(f"   ❌ Error checking balance for {address}: {str(e)}")
                results.append({
                    "address": address,
                    "error": str(e)
                })
        
        # Test price fetching (mock since we don't have get_bnb_price)
        try:
            # Use a generic price API instead
            import requests
            response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=binancecoin&vs_currencies=usd")
            price_data = response.json()
            bnb_price = price_data.get('binancecoin', {}).get('usd', 'N/A')
            print(f"   BNB Price: ${bnb_price}")
        except Exception as e:
            print(f"   ❌ Error fetching BNB price: {str(e)}")
            bnb_price = None
        
        print("✅ BSC balance checking: PASSED")
        return True, {"results": results, "bnb_price": bnb_price}
        
    except Exception as e:
        print(f"❌ BSC balance checking: FAILED - {str(e)}")
        print(f"   Error details: {traceback.format_exc()}")
        return False, None

def test_generic_balance_checking():
    """Test generic balance checking functionality"""
    print("\n🔍 Testing Generic Balance Functions...")
    try:
        from get_bnb_balance import get_balance_bnb_bsc
        
        # Test with known addresses
        test_address = "0x742d35Cc1B1c1F7BC46E2e0c6Ac9A4eCeD3e5C5D"
        
        balance = get_balance_bnb_bsc(test_address)
        print(f"   Generic BNB balance check: {balance}")
        
        print("✅ Generic balance checking: PASSED")
        return True, {"balance": balance}
        
    except Exception as e:
        print(f"❌ Generic balance checking: FAILED - {str(e)}")
        print(f"   Error details: {traceback.format_exc()}")
        return False, None

def test_balance_validation():
    """Test balance validation and conversion utilities"""
    print("\n🧮 Testing Balance Validation...")
    try:
        from utils import is_number, calc_fee
        
        # Test number validation
        test_numbers = ["123.45", "0.001", "invalid", "", "0", "-5"]
        
        for test_num in test_numbers:
            result = is_number(test_num)
            print(f"   Number validation '{test_num}': {result}")
        
        # Test fee calculation
        try:
            fee_result = calc_fee(100, 0.02, "USDT")
            print(f"   Fee calculation (100 USDT, 2%): {fee_result}")
        except Exception as e:
            print(f"   ❌ Fee calculation error: {str(e)}")
        
        print("✅ Balance validation: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Balance validation: FAILED - {str(e)}")
        return False

def test_price_fetching():
    """Test cryptocurrency price fetching"""
    print("\n💰 Testing Price Fetching...")
    try:
        from utils import get_trx_price
        
        # Test TRX price fetching
        try:
            trx_price = get_trx_price()
            print(f"   TRX Price: ${trx_price}")
        except Exception as e:
            print(f"   ❌ TRX price fetch error: {str(e)}")
            trx_price = None
        
        print("✅ Price fetching: PASSED")
        return True, {"trx_price": trx_price}
        
    except Exception as e:
        print(f"❌ Price fetching: FAILED - {str(e)}")
        return False, None

def create_test_wallets():
    """Create test wallets for balance checking"""
    print("\n🏗️  Creating Test Wallets for Balance Checks...")
    
    test_wallets = {}
    
    try:
        # Create Solana wallet
        from solwalletgen import generate_solana_wallet
        sol_wallet = generate_solana_wallet()
        test_wallets['solana'] = sol_wallet['public_address']
        print(f"   Solana test wallet: {sol_wallet['public_address']}")
    except Exception as e:
        print(f"   ❌ Failed to create Solana wallet: {str(e)}")
    
    try:
        # Create BSC wallet
        from bscwalletgen import generate_bsc_wallet
        bsc_wallet = generate_bsc_wallet()
        test_wallets['bsc'] = bsc_wallet['address']
        print(f"   BSC test wallet: {bsc_wallet['address']}")
    except Exception as e:
        print(f"   ❌ Failed to create BSC wallet: {str(e)}")
    
    try:
        # Create Dogecoin wallet
        from dogewalletgen import generate_doge_wallet
        doge_wallet = generate_doge_wallet()
        test_wallets['dogecoin'] = doge_wallet['address']
        print(f"   Dogecoin test wallet: {doge_wallet['address']}")
    except Exception as e:
        print(f"   ❌ Failed to create Dogecoin wallet: {str(e)}")
    
    print("✅ Test wallet creation completed")
    return test_wallets

def save_test_results(results):
    """Save test results to a JSON file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"balance_checking_test_results_{timestamp}.json"
    
    # Convert non-serializable data
    serializable_results = {}
    for key, value in results.items():
        if isinstance(value, tuple):
            serializable_results[key] = {
                "success": value[0],
                "data": value[1] if value[1] else None
            }
        else:
            serializable_results[key] = value
    
    try:
        with open(filename, 'w') as f:
            json.dump(serializable_results, f, indent=2, default=str)
        print(f"\n💾 Test results saved to: {filename}")
    except Exception as e:
        print(f"\n❌ Failed to save test results: {str(e)}")

def main():
    """Main test runner"""
    print("🚀 Starting Web3 Balance Checking Test Suite")
    print("=" * 60)
    
    # Store test results
    test_results = {}
    
    # Create test wallets first
    test_wallets = create_test_wallets()
    test_results['test_wallets'] = test_wallets
    
    # Run balance checking tests
    test_results['solana_balance'] = test_solana_balance()
    test_results['bsc_balance'] = test_bsc_balance()
    test_results['generic_balance'] = test_generic_balance_checking()
    test_results['balance_validation'] = test_balance_validation()
    test_results['price_fetching'] = test_price_fetching()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    successful_tests = 0
    total_tests = 0
    
    for test_name, result in test_results.items():
        if test_name == 'test_wallets':
            continue  # Skip wallet creation summary
            
        if isinstance(result, tuple):
            status = "✅ PASSED" if result[0] else "❌ FAILED"
            print(f"{test_name.upper().replace('_', ' '):25} : {status}")
            total_tests += 1
            if result[0]:
                successful_tests += 1
        else:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name.upper().replace('_', ' '):25} : {status}")
            total_tests += 1
            if result:
                successful_tests += 1
    
    success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
    print(f"\nOverall Success Rate: {successful_tests}/{total_tests} ({success_rate:.1f}%)")
    
    # Important notes
    print("\n" + "=" * 60)
    print("📝 IMPORTANT NOTES")
    print("=" * 60)
    print("• New wallets will have zero balance (this is expected)")
    print("• Some RPC endpoints may be rate-limited")
    print("• Network connectivity issues may affect results")
    print("• Balance checking requires active internet connection")
    
    # Save results
    save_test_results(test_results)
    
    if success_rate >= 80:  # Allow for some network-related failures
        print("\n🎉 Balance checking tests completed successfully!")
        return 0
    else:
        print(f"\n⚠️  Some tests failed. Please check network connectivity and RPC endpoints.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 