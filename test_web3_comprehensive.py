#!/usr/bin/env python3
"""
Comprehensive Web3 Test Suite Runner
=====================================

This script runs all Web3 functionality tests and provides a comprehensive report:
- Wallet Generation Tests
- Balance Checking Tests  
- Transaction Simulation Tests
- Utility Function Tests

This is the master test runner that executes all other test scripts.

Usage:
    python test_web3_comprehensive.py [--timestamp] [--cleanup]
    
Options:
    --timestamp    Create timestamped files instead of overwriting (keeps history)
    --cleanup      Remove old result files (keeps only latest 3)
    --help         Show this help message

Note: By default, results overwrite previous files (latest.html/latest.json)

Requirements:
pip install mnemonic solders nacl eth-account eth-utils hdwallet solana spl-token web3 requests decimal
"""

import os
import sys
import subprocess
import json
import argparse
import glob
from datetime import datetime
import time

def run_test_script(script_name):
    """Run a test script and return results"""
    print(f"\n{'='*60}")
    print(f"🚀 Running {script_name}")
    print(f"{'='*60}")
    
    try:
        # Run the test script
        result = subprocess.run([
            sys.executable, script_name
        ], capture_output=True, text=True, timeout=300)  # 5 minute timeout
        
        return {
            "script": script_name,
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
        
    except subprocess.TimeoutExpired:
        return {
            "script": script_name,
            "success": False,
            "error": "Test script timed out after 5 minutes",
            "returncode": -1
        }
    except Exception as e:
        return {
            "script": script_name,
            "success": False,
            "error": str(e),
            "returncode": -1
        }

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking Dependencies...")
    
    required_packages = [
        'mnemonic', 'solders', 'nacl', 'eth_account', 'eth_utils', 'hdwallet',
        'solana', 'web3', 'requests', 'base58'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + " ".join(missing_packages))
        return False
    
    print("✅ All dependencies available")
    return True

def check_script_files():
    """Check if all required script files exist"""
    print("\n📁 Checking Test Script Files...")
    
    required_scripts = [
        'test_web3_wallet_generation.py',
        'test_web3_balance_checking.py', 
        'test_web3_transaction_simulation.py'
    ]
    
    missing_scripts = []
    
    for script in required_scripts:
        if os.path.exists(script):
            print(f"   ✅ {script}")
        else:
            print(f"   ❌ {script} - MISSING")
            missing_scripts.append(script)
    
    if missing_scripts:
        print(f"\n⚠️  Missing test scripts: {', '.join(missing_scripts)}")
        return False
    
    print("✅ All test scripts available")
    return True

def check_web3_scripts():
    """Check if Web3 script files exist in functions/scripts"""
    print("\n🔧 Checking Web3 Script Files...")
    
    script_dir = os.path.join('functions', 'scripts')
    if not os.path.exists(script_dir):
        print(f"   ❌ {script_dir} directory not found")
        return False
    
    required_files = [
        'utils.py',
        'solwalletgen.py',
        'bscwalletgen.py', 
        'ltcwalletgen.py',
        'dogewalletgen.py',
        'tronwalletgen.py',
        'solwalletbalance.py',
        'bsc_wallet_balance.py',
        'get_bnb_balance.py'
    ]
    
    missing_files = []
    
    for file in required_files:
        file_path = os.path.join(script_dir, file)
        if os.path.exists(file_path):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} - MISSING")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n⚠️  Missing Web3 script files: {', '.join(missing_files)}")
        return False
    
    print("✅ All Web3 script files available")
    return True

def generate_comprehensive_report(test_results, timestamp=False):
    """Generate a comprehensive HTML report"""
    if timestamp:
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_filename = f"web3_comprehensive_test_report_{timestamp_str}.html"
    else:
        html_filename = "web3_comprehensive_test_report_latest.html"
    
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Web3 Comprehensive Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .test-section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .success {{ background-color: #d4edda; border-color: #c3e6cb; }}
        .failure {{ background-color: #f8d7da; border-color: #f5c6cb; }}
        .stdout {{ background-color: #f8f9fa; padding: 10px; border-radius: 3px; white-space: pre-wrap; font-family: monospace; max-height: 300px; overflow-y: auto; }}
        .stderr {{ background-color: #f8d7da; padding: 10px; border-radius: 3px; white-space: pre-wrap; font-family: monospace; max-height: 200px; overflow-y: auto; }}
        .summary {{ background-color: #e2f3ff; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .stats {{ display: flex; justify-content: space-around; text-align: center; }}
        .stat {{ padding: 10px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Web3 Comprehensive Test Report</h1>
        <p><strong>Generated:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        <p><strong>Total Test Scripts:</strong> {len(test_results)}</p>
        <p><strong>Mode:</strong> {'Timestamped' if timestamp else 'Latest (Overwrite)'}</p>
    </div>
"""
    
    # Summary statistics
    successful_scripts = sum(1 for result in test_results if result['success'])
    total_scripts = len(test_results)
    success_rate = (successful_scripts / total_scripts * 100) if total_scripts > 0 else 0
    
    html_content += f"""
    <div class="summary">
        <h2>📊 Summary</h2>
        <div class="stats">
            <div class="stat">
                <h3>{successful_scripts}</h3>
                <p>Successful Scripts</p>
            </div>
            <div class="stat">
                <h3>{total_scripts - successful_scripts}</h3>
                <p>Failed Scripts</p>
            </div>
            <div class="stat">
                <h3>{success_rate:.1f}%</h3>
                <p>Success Rate</p>
            </div>
        </div>
    </div>
"""
    
    # Individual test results
    for result in test_results:
        status_class = "success" if result['success'] else "failure"
        status_emoji = "✅" if result['success'] else "❌"
        
        html_content += f"""
    <div class="test-section {status_class}">
        <h3>{status_emoji} {result['script']}</h3>
        <p><strong>Status:</strong> {'PASSED' if result['success'] else 'FAILED'}</p>
        <p><strong>Return Code:</strong> {result.get('returncode', 'N/A')}</p>
"""
        
        if 'stdout' in result and result['stdout']:
            html_content += f"""
        <h4>Output:</h4>
        <div class="stdout">{result['stdout']}</div>
"""
        
        if 'stderr' in result and result['stderr']:
            html_content += f"""
        <h4>Errors:</h4>
        <div class="stderr">{result['stderr']}</div>
"""
        
        if 'error' in result:
            html_content += f"""
        <h4>Error:</h4>
        <div class="stderr">{result['error']}</div>
"""
        
        html_content += "    </div>\n"
    
    html_content += """
    <div class="summary">
        <h2>📝 Notes</h2>
        <ul>
            <li>Wallet generation tests create new wallets with zero balance (expected)</li>
            <li>Balance checking tests may fail due to network issues or RPC limits</li>
            <li>Transaction simulation tests do not send real funds</li>
            <li>Some tests may require specific dependencies or network access</li>
        </ul>
    </div>
</body>
</html>
"""
    
    try:
        with open(html_filename, 'w') as f:
            f.write(html_content)
        print(f"\n📊 HTML report generated: {html_filename}")
    except Exception as e:
        print(f"\n❌ Failed to generate HTML report: {str(e)}")

def save_json_results(test_results, timestamp=False):
    """Save test results to JSON file"""
    if timestamp:
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_filename = f"web3_comprehensive_test_results_{timestamp_str}.json"
    else:
        json_filename = "web3_comprehensive_test_results_latest.json"
    
    try:
        with open(json_filename, 'w') as f:
            json.dump({
                'timestamp': datetime.now().strftime("%Y%m%d_%H%M%S"),
                'test_results': test_results,
                'summary': {
                    'total_scripts': len(test_results),
                    'successful_scripts': sum(1 for result in test_results if result['success']),
                    'failed_scripts': sum(1 for result in test_results if not result['success']),
                    'success_rate': (sum(1 for result in test_results if result['success']) / len(test_results) * 100) if test_results else 0
                }
            }, f, indent=2)
        print(f"💾 JSON results saved: {json_filename}")
    except Exception as e:
        print(f"❌ Failed to save JSON results: {str(e)}")

def cleanup_old_results(keep_count=3):
    """Clean up old result files, keeping only the most recent ones"""
    print(f"\n🧹 Cleaning up old result files (keeping {keep_count} most recent)...")
    
    # Get all result files
    patterns = [
        "web3_comprehensive_test_report_*.html",
        "web3_comprehensive_test_results_*.json", 
        "wallet_generation_test_results_*.json",
        "balance_checking_test_results_*.json",
        "transaction_simulation_test_results_*.json"
    ]
    
    cleaned_count = 0
    for pattern in patterns:
        files = glob.glob(pattern)
        if len(files) > keep_count:
            # Sort by modification time, newest first
            files.sort(key=os.path.getmtime, reverse=True)
            files_to_remove = files[keep_count:]
            
            for file_path in files_to_remove:
                try:
                    os.remove(file_path)
                    print(f"   🗑️  Removed: {file_path}")
                    cleaned_count += 1
                except OSError as e:
                    print(f"   ❌ Failed to remove {file_path}: {e}")
    
    if cleaned_count == 0:
        print("   ✅ No old files to clean up")
    else:
        print(f"   ✅ Cleaned up {cleaned_count} old result files")

def main(timestamp=False, cleanup=False):
    """Main test runner"""
    print("🌟 Web3 Comprehensive Test Suite")
    print("=" * 60)
    
    if timestamp:
        print("📝 Mode: Create timestamped files (keep history)")
    else:
        print("📝 Mode: Overwrite latest results")
        
    if cleanup:
        print("🧹 Cleanup: Will remove old files after testing")
    
    print("This will run all Web3 functionality tests")
    print("=" * 60)
    
    start_time = time.time()
    
    # Pre-flight checks
    print("🔧 Running Pre-flight Checks...")
    
    if not check_dependencies():
        print("\n❌ Dependency check failed. Please install missing packages.")
        return 1
    
    if not check_script_files():
        print("\n❌ Test script file check failed. Please ensure all test scripts exist.")
        return 1
    
    if not check_web3_scripts():
        print("\n❌ Web3 script file check failed. Please ensure functions/scripts directory exists with required files.")
        return 1
    
    print("\n✅ All pre-flight checks passed!")
    
    # Test scripts to run
    test_scripts = [
        'test_web3_wallet_generation.py',
        'test_web3_balance_checking.py',
        'test_web3_transaction_simulation.py'
    ]
    
    test_results = []
    
    # Run each test script
    for script in test_scripts:
        result = run_test_script(script)
        test_results.append(result)
        
        # Print immediate feedback
        status = "✅ PASSED" if result['success'] else "❌ FAILED"
        print(f"\n{script}: {status}")
        
        # Small delay between tests
        time.sleep(1)
    
    # Calculate final statistics
    end_time = time.time()
    total_time = end_time - start_time
    successful_scripts = sum(1 for result in test_results if result['success'])
    total_scripts = len(test_results)
    success_rate = (successful_scripts / total_scripts * 100) if total_scripts > 0 else 0
    
    # Final summary
    print("\n" + "=" * 60)
    print("🏁 FINAL SUMMARY")
    print("=" * 60)
    print(f"Total Execution Time: {total_time:.2f} seconds")
    print(f"Test Scripts Run: {total_scripts}")
    print(f"Successful Scripts: {successful_scripts}")
    print(f"Failed Scripts: {total_scripts - successful_scripts}")
    print(f"Overall Success Rate: {success_rate:.1f}%")
    
    # Detailed results
    print("\n📋 Detailed Results:")
    for result in test_results:
        status = "✅ PASSED" if result['success'] else "❌ FAILED"
        print(f"  {result['script']:35} : {status}")
    
    # Generate reports
    print("\n📊 Generating Reports...")
    save_json_results(test_results, timestamp)
    generate_comprehensive_report(test_results, timestamp)
    
    # Cleanup if requested
    if cleanup:
        cleanup_old_results()
    
    # Final recommendations
    print("\n" + "=" * 60)
    print("💡 RECOMMENDATIONS")
    print("=" * 60)
    
    if success_rate == 100:
        print("🎉 Excellent! All tests passed.")
        print("   Your Web3 functionality is working correctly.")
    elif success_rate >= 80:
        print("✅ Good! Most tests passed.")
        print("   Some minor issues may need attention.")
    elif success_rate >= 60:
        print("⚠️  Moderate success rate.")
        print("   Several issues need to be addressed.")
    else:
        print("❌ Low success rate.")
        print("   Major issues need immediate attention.")
    
    print("\n📝 Next Steps:")
    if not timestamp:
        print("   1. Check web3_comprehensive_test_report_latest.html for detailed results")
    else:
        print("   1. Review the detailed HTML report for specific errors")
    print("   2. Check network connectivity for balance/transaction tests")
    print("   3. Ensure all required dependencies are properly installed")
    print("   4. Verify that functions/scripts directory has all required files")
    
    # Return appropriate exit code
    if success_rate >= 80:
        return 0
    else:
        return 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Web3 comprehensive test suite")
    parser.add_argument("--timestamp", action="store_true", help="Create timestamped files instead of overwriting (keeps history)")
    parser.add_argument("--cleanup", action="store_true", help="Remove old result files (keeps only latest 3)")
    args = parser.parse_args()
    
    if args.cleanup:
        # Remove old result files
        old_results = glob.glob("web3_comprehensive_test_results_*.json")
        old_results.sort(key=lambda f: int(f.split('_')[-1].split('.')[0]))
        for old_file in old_results[:-3]:
            os.remove(old_file)
    
    sys.exit(main(args.timestamp, args.cleanup)) 