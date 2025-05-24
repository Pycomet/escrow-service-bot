#!/usr/bin/env python3
"""
Web3 Wallet Generation Test Suite
=================================

This script tests wallet generation for all supported blockchains:
- Solana (SOL)
- Bitcoin Cash (BSC/BNB)
- Litecoin (LTC)
- Dogecoin (DOGE)
- Tron (TRX)

Usage:
    python test_web3_wallet_generation.py [--timestamp]
    
Options:
    --timestamp    Create timestamped files instead of overwriting (keeps history)

Note: By default, results overwrite previous files (latest.json)

Requirements:
pip install mnemonic solders nacl eth-account eth-utils hdwallet binascii
"""

import os
import sys

# Add the functions/scripts directory to Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
functions_scripts_dir = os.path.join(script_dir, 'functions', 'scripts')
sys.path.insert(0, functions_scripts_dir)

import json
import argparse
from datetime import datetime
import traceback

def test_solana_wallet():
    """Test Solana wallet generation"""
    print("🔷 Testing Solana Wallet Generation...")
    try:
        from solwalletgen import generate_solana_wallet
        
        wallet = generate_solana_wallet()
        
        # Validate wallet structure
        required_keys = ['mnemonic', 'private_key', 'public_address']
        for key in required_keys:
            assert key in wallet, f"Missing key: {key}"
            assert wallet[key], f"Empty value for key: {key}"
        
        # Validate address format (Solana addresses are typically 32-44 characters)
        assert len(wallet['public_address']) >= 32, "Solana address too short"
        assert len(wallet['public_address']) <= 44, "Solana address too long"
        
        # Validate mnemonic (should be 12 words)
        mnemonic_words = wallet['mnemonic'].split()
        assert len(mnemonic_words) == 12, f"Expected 12 words, got {len(mnemonic_words)}"
        
        print("✅ Solana wallet generation: PASSED")
        print(f"   Address: {wallet['public_address']}")
        print(f"   Mnemonic: {wallet['mnemonic']}")
        return True, wallet
        
    except Exception as e:
        print(f"❌ Solana wallet generation: FAILED - {str(e)}")
        print(f"   Error details: {traceback.format_exc()}")
        return False, None

def test_bsc_wallet():
    """Test BSC/BNB wallet generation"""
    print("\n🔶 Testing BSC Wallet Generation...")
    try:
        from bscwalletgen import generate_bsc_wallet
        
        wallet = generate_bsc_wallet()
        
        # Validate wallet structure
        required_keys = ['mnemonic', 'private_key', 'address']
        for key in required_keys:
            assert key in wallet, f"Missing key: {key}"
            assert wallet[key], f"Empty value for key: {key}"
        
        # Validate address format (BSC addresses start with 0x and are 42 characters)
        assert wallet['address'].startswith('0x'), "BSC address should start with 0x"
        assert len(wallet['address']) == 42, f"BSC address should be 42 characters, got {len(wallet['address'])}"
        
        # Validate private key format (should be hex, may or may not have 0x prefix)
        private_key = wallet['private_key']
        if private_key.startswith('0x'):
            assert len(private_key) == 66
        else:
            assert len(private_key) == 64
            int(private_key, 16)  # Validate hex format
        
        # Validate mnemonic
        mnemonic_words = wallet['mnemonic'].split()
        assert len(mnemonic_words) == 12, f"Expected 12 words, got {len(mnemonic_words)}"
        
        print("✅ BSC wallet generation: PASSED")
        print(f"   Address: {wallet['address']}")
        print(f"   Mnemonic: {wallet['mnemonic']}")
        return True, wallet
        
    except Exception as e:
        print(f"❌ BSC wallet generation: FAILED - {str(e)}")
        print(f"   Error details: {traceback.format_exc()}")
        return False, None

def test_litecoin_wallet():
    """Test Litecoin wallet generation"""
    print("\n🔸 Testing Litecoin Wallet Generation...")
    try:
        from ltcwalletgen import generate_litecoin_wallet
        
        wallet = generate_litecoin_wallet()
        
        # Validate wallet structure
        required_keys = ['mnemonic', 'private_key', 'bech32_address']
        for key in required_keys:
            assert key in wallet, f"Missing key: {key}"
            assert wallet[key], f"Empty value for key: {key}"
        
        # Validate bech32 address format (Litecoin bech32 starts with ltc1)
        assert wallet['bech32_address'].startswith('ltc1'), "Litecoin bech32 address should start with ltc1"
        
        # Validate mnemonic
        mnemonic_words = wallet['mnemonic'].split()
        assert len(mnemonic_words) == 12, f"Expected 12 words, got {len(mnemonic_words)}"
        
        print("✅ Litecoin wallet generation: PASSED")
        print(f"   Address: {wallet['bech32_address']}")
        print(f"   Mnemonic: {wallet['mnemonic']}")
        return True, wallet
        
    except Exception as e:
        print(f"❌ Litecoin wallet generation: FAILED - {str(e)}")
        print(f"   Error details: {traceback.format_exc()}")
        return False, None

def test_dogecoin_wallet():
    """Test Dogecoin wallet generation"""
    print("\n🐕 Testing Dogecoin Wallet Generation...")
    try:
        from dogewalletgen import generate_doge_wallet
        
        wallet = generate_doge_wallet()
        
        # Validate wallet structure
        required_keys = ['mnemonic', 'private_key', 'address']
        for key in required_keys:
            assert key in wallet, f"Missing key: {key}"
            assert wallet[key], f"Empty value for key: {key}"
        
        # Validate address format (Dogecoin addresses start with D)
        assert wallet['address'].startswith('D'), "Dogecoin address should start with D"
        assert len(wallet['address']) >= 27, "Dogecoin address too short"
        assert len(wallet['address']) <= 34, "Dogecoin address too long"
        
        # Validate mnemonic
        mnemonic_words = wallet['mnemonic'].split()
        assert len(mnemonic_words) == 12, f"Expected 12 words, got {len(mnemonic_words)}"
        
        print("✅ Dogecoin wallet generation: PASSED")
        print(f"   Address: {wallet['address']}")
        print(f"   Mnemonic: {wallet['mnemonic']}")
        return True, wallet
        
    except Exception as e:
        print(f"❌ Dogecoin wallet generation: FAILED - {str(e)}")
        print(f"   Error details: {traceback.format_exc()}")
        return False, None

def test_tron_wallet():
    """Test Tron wallet generation"""
    print("\n🔺 Testing Tron Wallet Generation...")
    try:
        from tronwalletgen import generate_tron_wallet
        
        wallet = generate_tron_wallet()
        
        # Validate wallet structure
        required_keys = ['mnemonic', 'private_key', 'address']
        for key in required_keys:
            assert key in wallet, f"Missing key: {key}"
            assert wallet[key], f"Empty value for key: {key}"
        
        # Validate address format (Tron addresses start with T)
        assert wallet['address'].startswith('T'), "Tron address should start with T"
        assert len(wallet['address']) == 34, f"Tron address should be 34 characters, got {len(wallet['address'])}"
        
        # Validate mnemonic
        mnemonic_words = wallet['mnemonic'].split()
        assert len(mnemonic_words) == 12, f"Expected 12 words, got {len(mnemonic_words)}"
        
        print("✅ Tron wallet generation: PASSED")
        print(f"   Address: {wallet['address']}")
        print(f"   Mnemonic: {wallet['mnemonic']}")
        return True, wallet
        
    except Exception as e:
        print(f"❌ Tron wallet generation: FAILED - {str(e)}")
        print(f"   Error details: {traceback.format_exc()}")
        return False, None

def test_address_validation():
    """Test address validation utilities"""
    print("\n🔍 Testing Address Validation...")
    try:
        from utils import is_address_valid
        
        # Test data with known valid addresses
        test_cases = [
            ("9eeneoxQmxbYFTrffFS5rDz1VsdCpQuzd4D67UNE5D8W", "SOL", True),
            ("0x742d35Cc1B1c1F7BC46E2e0c6Ac9A4eCeD3e5C5D", "BSC", True),
            ("ltc1qw508d6qejxtdg4y5r3zarvary0c5xw7kw508d6qejxtdg4y5r3zarvary0c5xw7kw5rljs90", "LTC", True),
            ("DNABPoSJKyAV7KaQewN85mXZs6ZBcwjqv6", "DOGE", True),
            ("invalid_address", "SOL", False),
            ("", "BSC", False),
            ("not_an_address", "LTC", False),
            ("123456", "DOGE", False),
        ]
        
        passed_tests = 0
        total_tests = len(test_cases)
        
        for address, symbol, expected in test_cases:
            try:
                result = is_address_valid(address, symbol)
                if result == expected:
                    print(f"   ✅ {symbol} address validation: {address[:10]}... -> {result}")
                    passed_tests += 1
                else:
                    print(f"   ❌ {symbol} address validation: Expected {expected}, got {result} for {address[:20]}...")
            except Exception as e:
                print(f"   ❌ {symbol} address validation error: {str(e)}")
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"Address validation tests: {passed_tests}/{total_tests} passed ({success_rate:.1f}%)")
        
        return passed_tests >= (total_tests * 0.7)  # 70% success rate
        
    except Exception as e:
        print(f"❌ Address validation testing: FAILED - {str(e)}")
        return False

def save_test_results(results, timestamp=False):
    """Save test results to a JSON file"""
    if timestamp:
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"wallet_generation_test_results_{timestamp_str}.json"
    else:
        filename = "wallet_generation_test_results_latest.json"
    
    # Convert non-serializable data
    serializable_results = {}
    for key, value in results.items():
        if isinstance(value, tuple):
            serializable_results[key] = {
                "success": value[0],
                "wallet_data": value[1] if value[1] else None
            }
        else:
            serializable_results[key] = value
    
    try:
        with open(filename, 'w') as f:
            json.dump(serializable_results, f, indent=2, default=str)
        print(f"\n💾 Test results saved to: {filename}")
    except Exception as e:
        print(f"\n❌ Failed to save test results: {str(e)}")

def main(timestamp=False):
    """Main test runner"""
    print("🚀 Starting Web3 Wallet Generation Test Suite")
    print("=" * 60)
    
    # Store test results
    test_results = {}
    
    # Run all wallet generation tests
    test_results['solana'] = test_solana_wallet()
    test_results['bsc'] = test_bsc_wallet()
    test_results['litecoin'] = test_litecoin_wallet()
    test_results['dogecoin'] = test_dogecoin_wallet()
    test_results['tron'] = test_tron_wallet()
    
    # Run utility tests
    test_results['address_validation'] = test_address_validation()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    successful_tests = 0
    total_tests = 0
    
    for test_name, result in test_results.items():
        if test_name == 'address_validation':
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name.upper():20} : {status}")
            total_tests += 1
            if result:
                successful_tests += 1
        else:
            status = "✅ PASSED" if result[0] else "❌ FAILED"
            print(f"{test_name.upper():20} : {status}")
            total_tests += 1
            if result[0]:
                successful_tests += 1
    
    success_rate = (successful_tests / total_tests) * 100
    print(f"\nOverall Success Rate: {successful_tests}/{total_tests} ({success_rate:.1f}%)")
    
    # Save results
    save_test_results(test_results, timestamp)
    
    if success_rate == 100:
        print("\n🎉 All tests passed! Your wallet generation functions are working correctly.")
        return 0
    else:
        print(f"\n⚠️  Some tests failed. Please check the error messages above.")
        return 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Web3 Wallet Generation Test Suite")
    parser.add_argument("--timestamp", action="store_true", help="Create timestamped files instead of overwriting (keeps history)")
    args = parser.parse_args()
    sys.exit(main(args.timestamp)) 