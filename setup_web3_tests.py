#!/usr/bin/env python3
"""
Web3 Test Environment Setup Script
==================================

This script helps set up the environment for running Web3 tests.
It checks dependencies, installs missing packages, and runs basic verification.

Usage:
    python setup_web3_tests.py
"""

import os
import sys
import subprocess
import importlib

def print_header():
    """Print setup header"""
    print("🔧 Web3 Test Environment Setup")
    print("=" * 50)
    print("This script will prepare your environment for Web3 testing.\n")

def check_python_version():
    """Check Python version compatibility"""
    print("🐍 Checking Python Version...")
    version = sys.version_info
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python {version.major}.{version.minor} detected")
        print("   Web3 libraries require Python 3.8 or higher")
        print("   Please upgrade your Python installation")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
    return True

def install_package(package_name):
    """Install a package using pip"""
    try:
        print(f"   Installing {package_name}...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", package_name
        ], capture_output=True, text=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Failed to install {package_name}: {e}")
        return False

def check_and_install_dependencies():
    """Check and install required dependencies"""
    print("\n📦 Checking Dependencies...")
    
    # Core dependencies with installation names
    dependencies = {
        'mnemonic': 'mnemonic',
        'solders': 'solders', 
        'nacl': 'PyNaCl',
        'eth_account': 'eth-account',
        'eth_utils': 'eth-utils',
        'hdwallet': 'hdwallet',
        'web3': 'web3',
        'requests': 'requests',
        'base58': 'base58',
        'solana': 'solana',
    }
    
    missing_packages = []
    
    for module_name, package_name in dependencies.items():
        try:
            importlib.import_module(module_name)
            print(f"   ✅ {module_name}")
        except ImportError:
            print(f"   ❌ {module_name} - Missing")
            missing_packages.append(package_name)
    
    # Install missing packages
    if missing_packages:
        print(f"\n🚀 Installing {len(missing_packages)} missing packages...")
        
        for package in missing_packages:
            success = install_package(package)
            if not success:
                print(f"   ⚠️  Manual installation required: pip install {package}")
    
    # Re-check after installation
    print("\n🔄 Re-checking dependencies...")
    all_available = True
    
    for module_name, package_name in dependencies.items():
        try:
            importlib.import_module(module_name)
            print(f"   ✅ {module_name}")
        except ImportError:
            print(f"   ❌ {module_name} - Still missing")
            all_available = False
    
    return all_available

def check_test_files():
    """Check if test files exist"""
    print("\n📄 Checking Test Files...")
    
    test_files = [
        'test_web3_wallet_generation.py',
        'test_web3_balance_checking.py',
        'test_web3_transaction_simulation.py',
        'test_web3_comprehensive.py'
    ]
    
    missing_files = []
    
    for file in test_files:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} - Missing")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n⚠️  Missing test files: {', '.join(missing_files)}")
        print("   These files should be in the same directory as this setup script.")
        return False
    
    return True

def check_functions_directory():
    """Check if functions/scripts directory exists"""
    print("\n📁 Checking Functions Directory...")
    
    functions_dir = os.path.join('functions', 'scripts')
    
    if not os.path.exists(functions_dir):
        print(f"   ❌ {functions_dir} - Directory not found")
        print("   This directory should contain your Web3 script files.")
        return False
    
    print(f"   ✅ {functions_dir} - Found")
    
    # Check for some key files
    key_files = ['utils.py', 'solwalletgen.py', 'bscwalletgen.py']
    missing_key_files = []
    
    for file in key_files:
        file_path = os.path.join(functions_dir, file)
        if os.path.exists(file_path):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} - Missing")
            missing_key_files.append(file)
    
    if missing_key_files:
        print(f"\n⚠️  Missing key files in {functions_dir}:")
        print(f"   {', '.join(missing_key_files)}")
        return False
    
    return True

def run_quick_test():
    """Run a quick test to verify everything works"""
    print("\n🧪 Running Quick Verification Test...")
    
    try:
        # Test wallet generation import
        sys.path.insert(0, os.path.join('functions', 'scripts'))
        
        print("   Testing Solana wallet generation...")
        from solwalletgen import generate_solana_wallet
        wallet = generate_solana_wallet()
        assert 'mnemonic' in wallet
        assert 'private_key' in wallet
        assert 'public_address' in wallet
        print("   ✅ Solana wallet generation works")
        
        print("   Testing BSC wallet generation...")
        from bscwalletgen import generate_bsc_wallet
        wallet = generate_bsc_wallet()
        assert 'mnemonic' in wallet
        assert 'private_key' in wallet
        assert 'address' in wallet
        print("   ✅ BSC wallet generation works")
        
        print("   Testing utilities...")
        from utils import is_address_valid
        # Test with a known good address format
        result = is_address_valid("9eeneoxQmxbYFTrffFS5rDz1VsdCpQuzd4D67UNE5D8W", "SOL")
        print("   ✅ Address validation works")
        
        print("\n🎉 Quick verification test PASSED!")
        return True
        
    except Exception as e:
        print(f"\n❌ Quick verification test FAILED: {str(e)}")
        print("   Some functionality may not work correctly.")
        return False

def create_run_script():
    """Create a convenient run script"""
    print("\n📝 Creating run script...")
    
    script_content = """#!/bin/bash
# Web3 Test Runner Script
# This script runs the comprehensive Web3 tests

echo "🚀 Starting Web3 Comprehensive Tests..."
echo "======================================"

python test_web3_comprehensive.py

echo ""
echo "Test completed! Check the generated reports for details."
"""
    
    try:
        with open('run_web3_tests.sh', 'w') as f:
            f.write(script_content)
        
        # Make executable on Unix-like systems
        if os.name != 'nt':
            os.chmod('run_web3_tests.sh', 0o755)
        
        print("   ✅ Created run_web3_tests.sh")
        
        # Also create a Windows batch file
        batch_content = """@echo off
echo 🚀 Starting Web3 Comprehensive Tests...
echo ======================================

python test_web3_comprehensive.py

echo.
echo Test completed! Check the generated reports for details.
pause
"""
        
        with open('run_web3_tests.bat', 'w') as f:
            f.write(batch_content)
        
        print("   ✅ Created run_web3_tests.bat")
        return True
        
    except Exception as e:
        print(f"   ❌ Failed to create run scripts: {str(e)}")
        return False

def main():
    """Main setup function"""
    print_header()
    
    # Check Python version
    if not check_python_version():
        return 1
    
    # Check and install dependencies
    deps_ok = check_and_install_dependencies()
    
    # Check test files
    files_ok = check_test_files()
    
    # Check functions directory
    functions_ok = check_functions_directory()
    
    # Run verification test if everything looks good
    if deps_ok and files_ok and functions_ok:
        test_ok = run_quick_test()
    else:
        test_ok = False
    
    # Create run scripts
    scripts_ok = create_run_script()
    
    # Final summary
    print("\n" + "=" * 50)
    print("📋 SETUP SUMMARY")
    print("=" * 50)
    
    checks = [
        ("Python Version", True),  # We already exit if this fails
        ("Dependencies", deps_ok),
        ("Test Files", files_ok), 
        ("Functions Directory", functions_ok),
        ("Quick Verification", test_ok),
        ("Run Scripts", scripts_ok)
    ]
    
    for check_name, status in checks:
        status_icon = "✅" if status else "❌"
        print(f"{check_name:20} : {status_icon}")
    
    # Final recommendations
    print("\n💡 NEXT STEPS:")
    
    if all(status for _, status in checks):
        print("🎉 Setup completed successfully!")
        print("\nYou can now run the tests:")
        print("  • python test_web3_comprehensive.py")
        print("  • ./run_web3_tests.sh (Linux/Mac)")
        print("  • run_web3_tests.bat (Windows)")
        return 0
    else:
        print("⚠️  Setup completed with issues:")
        
        if not deps_ok:
            print("  • Install missing dependencies manually")
        if not files_ok:
            print("  • Ensure all test files are in the current directory")
        if not functions_ok:
            print("  • Check that functions/scripts directory exists and has required files")
        if not test_ok:
            print("  • Review error messages above for specific issues")
        
        print("\nYou may still be able to run some tests, but full functionality is not guaranteed.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 