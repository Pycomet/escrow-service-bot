#!/usr/bin/env python3
"""
Community Content System Setup Script
Run this to help configure the community content management system.
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

def print_header():
    """Print setup header"""
    print("🏘️" + "=" * 50)
    print("   COMMUNITY CONTENT SYSTEM SETUP")
    print("=" * 52)
    print()

def check_environment():
    """Check required environment variables"""
    print("🔍 Checking environment configuration...")
    
    required_vars = {
        "TOKEN": "Telegram Bot Token",
        "GEMINI_API_KEY": "Google Gemini API Key", 
        "DATABASE_URL": "MongoDB Connection URL",
        "COMMUNITY_CHANNEL_ID": "Community Channel ID"
    }
    
    optional_vars = {
        "WEBHOOK_URL": "Webhook URL for production",
        "ADMIN_ID": "Admin User ID",
        "TRADING_CHANNEL": "Trading Channel Username",
        "CONTACT_SUPPORT": "Support Username"
    }
    
    missing_required = []
    missing_optional = []
    
    print("\n📋 Required Variables:")
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Hide sensitive values
            display_value = value[:10] + "..." if len(value) > 10 else value
            if var in ["TOKEN", "GEMINI_API_KEY"]:
                display_value = "***" + value[-4:] if len(value) > 4 else "***"
            print(f"   ✅ {var}: {display_value}")
        else:
            print(f"   ❌ {var}: Not set")
            missing_required.append((var, description))
    
    print("\n📋 Optional Variables:")
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            display_value = value[:20] + "..." if len(value) > 20 else value
            print(f"   ✅ {var}: {display_value}")
        else:
            print(f"   ⚠️  {var}: Not set (using defaults)")
            missing_optional.append((var, description))
    
    if missing_required:
        print("\n❌ Missing Required Variables:")
        for var, desc in missing_required:
            print(f"   • {var}: {desc}")
        print("\nPlease add these to your .env file before continuing.")
        return False
    
    if missing_optional:
        print("\n💡 Optional Variables You May Want to Set:")
        for var, desc in missing_optional:
            print(f"   • {var}: {desc}")
    
    print("\n✅ Environment check completed!")
    return True

def create_env_template():
    """Create .env template file"""
    template = """# Telegram Bot Configuration
TOKEN=your_telegram_bot_token_here
ADMIN_ID=your_telegram_user_id_here

# Google Gemini AI
GEMINI_API_KEY=your_gemini_api_key_here

# Database
DATABASE_URL=mongodb://localhost:27017/
DATABASE_NAME=escrow_bot_db

# Community Channel (REQUIRED for community content)
COMMUNITY_CHANNEL_ID=@your_channel_username
# OR for private channels: COMMUNITY_CHANNEL_ID=-1001234567890

# Channels (Optional)
TRADING_CHANNEL=your_trading_channel
CONTACT_SUPPORT=your_support_username
REVIEW_CHANNEL=your_review_channel

# Webhook (Production)
WEBHOOK_MODE=false
WEBHOOK_URL=https://your-domain.com/webhook

# BTCPay Server (Optional)
BTCPAY_URL=https://your-btcpay-server.com
BTCPAY_API_KEY=your_btcpay_api_key
BTCPAY_STORE_ID=your_store_id

# Bot Configuration
BOT_FEE_PERCENTAGE=2.5
DEBUG=false
"""
    
    env_file = ".env"
    if os.path.exists(env_file):
        print(f"📄 .env file already exists at {os.path.abspath(env_file)}")
        response = input("Do you want to create a backup and overwrite it? (y/N): ")
        if response.lower() != 'y':
            print("Skipping .env file creation.")
            return
        
        # Create backup
        backup_file = f".env.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.rename(env_file, backup_file)
        print(f"📄 Backup created: {backup_file}")
    
    with open(env_file, 'w') as f:
        f.write(template)
    
    print(f"✅ Created .env template at {os.path.abspath(env_file)}")
    print("📝 Please edit this file with your actual values.")

def show_next_steps():
    """Show next steps for setup"""
    print("\n🚀 Next Steps:")
    print("1. Configure your environment variables in .env file")
    print("2. Set up your Telegram channel:")
    print("   • Create a Telegram channel")
    print("   • Add your bot as an administrator")
    print("   • Give it permission to post messages")
    print("   • Get the channel ID (username or numeric ID)")
    print("3. Test the system:")
    print("   python community/test_system.py --quick")
    print("4. Run a full test:")
    print("   python community/test_system.py")
    print("5. Start your bot and use /admin -> Community Content")
    print()
    print("📖 For detailed instructions, see community/README.md")

def show_channel_setup_help():
    """Show help for setting up Telegram channel"""
    print("\n📺 Telegram Channel Setup Help:")
    print()
    print("1. Create a Channel:")
    print("   • Open Telegram")
    print("   • Create New Channel")
    print("   • Choose Public or Private")
    print()
    print("2. Add Your Bot:")
    print("   • Go to channel settings")
    print("   • Add Administrator")
    print("   • Search for your bot username")
    print("   • Give 'Post Messages' permission")
    print()
    print("3. Get Channel ID:")
    print("   Public channels: @your_channel_username")
    print("   Private channels: Get numeric ID (e.g., -1001234567890)")
    print("   You can use @userinfobot to get the ID")
    print()
    print("4. Test Connection:")
    print("   Use the admin panel 'Test System' feature")

def show_menu():
    """Display the main menu"""
    print("\n🎯 What would you like to do?")
    print("1. Check environment configuration")
    print("2. Create .env template file")
    print("3. Show channel setup help")
    print("4. Show next steps")
    print("5. Exit")
    print()

def get_user_choice():
    """Get and validate user choice"""
    while True:
        try:
            choice = input("Enter your choice (1-5): ").strip()
            if choice in ['1', '2', '3', '4', '5']:
                return choice
            elif choice.lower() in ['exit', 'quit', 'q']:
                return '5'
            elif choice == '':
                print("Please enter a choice (1-5)")
                continue
            else:
                print(f"Invalid choice '{choice}'. Please enter 1-5.")
                continue
        except (EOFError, KeyboardInterrupt):
            return '5'
        except Exception as e:
            print(f"Error reading input: {e}")
            continue

def main():
    """Main setup function"""
    print_header()
    
    print("This script will help you set up the Community Content Management System.")
    print("The system automatically generates and posts content to your Telegram channel.")
    print()
    
    # Check if we're in the right directory
    if not os.path.exists("community"):
        print("❌ Error: community/ directory not found.")
        print("Please run this script from the project root directory.")
        return
    
    print("✅ Community module found!")
    
    # Main menu loop
    while True:
        show_menu()
        choice = get_user_choice()
        
        print()  # Add spacing
        
        if choice == "1":
            print("🔍 Checking Environment Configuration...")
            print("-" * 40)
            check_environment()
            
        elif choice == "2":
            print("📄 Creating .env Template File...")
            print("-" * 40)
            create_env_template()
            
        elif choice == "3":
            print("📺 Telegram Channel Setup Help...")
            print("-" * 40)
            show_channel_setup_help()
            
        elif choice == "4":
            print("🚀 Next Steps Guide...")
            print("-" * 40)
            show_next_steps()
            
        elif choice == "5":
            print("👋 Setup complete! Good luck with your community content system.")
            break
        
        # Wait for user to continue (except for exit)
        if choice != "5":
            print()
            input("Press Enter to return to menu...")
            print("\n" + "="*50)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Setup cancelled by user.")
    except Exception as e:
        print(f"\n❌ Setup error: {e}")
        sys.exit(1)
