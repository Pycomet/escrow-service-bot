#!/usr/bin/env python3
"""
Quick Community Setup Script - Simplified version
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    print("🏘️ Community Content System - Quick Setup")
    print("=" * 50)
    print()
    
    # Check if we're in the right directory
    if not os.path.exists("community"):
        print("❌ Error: community/ directory not found.")
        print("Please run this script from the project root directory.")
        return False
    
    print("✅ Community module found")
    
    # Check required environment variables
    print("\n🔍 Checking environment variables...")
    
    required_vars = {
        "TOKEN": "Telegram Bot Token",
        "GEMINI_API_KEY": "Google Gemini API Key",
        "COMMUNITY_CHANNEL_ID": "Community Channel ID"
    }
    
    missing = []
    for var, desc in required_vars.items():
        if os.getenv(var):
            print(f"   ✅ {var}: Set")
        else:
            print(f"   ❌ {var}: Missing")
            missing.append((var, desc))
    
    if missing:
        print(f"\n⚠️  Missing {len(missing)} required variables:")
        for var, desc in missing:
            print(f"   • {var}: {desc}")
        
        print("\n📝 Add these to your .env file:")
        for var, desc in missing:
            if var == "COMMUNITY_CHANNEL_ID":
                print(f"   {var}=@your_channel_username")
            else:
                print(f"   {var}=your_{var.lower()}_here")
        
        return False
    
    print("\n✅ All required variables are set!")
    
    # Test basic imports
    print("\n🧪 Testing system components...")
    
    try:
        from community.content_generator import AIContentGenerator
        print("   ✅ Content generator: OK")
    except Exception as e:
        print(f"   ❌ Content generator: {e}")
        return False
    
    try:
        from community.poster import CommunityPoster
        print("   ✅ Poster: OK")
    except Exception as e:
        print(f"   ❌ Poster: {e}")
        return False
    
    try:
        from community.scheduler import get_community_scheduler
        print("   ✅ Scheduler: OK")
    except Exception as e:
        print(f"   ❌ Scheduler: {e}")
        return False
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Start your bot: python main.py")
    print("2. Use /admin command")
    print("3. Click '🏘️ Community Content'")
    print("4. Test the system with 'Test System' button")
    print("5. Try posting content with 'Post Now' button")
    
    print("\n🔧 For testing:")
    print("   python community/test_system.py --quick")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n✨ Ready to go!")
        else:
            print("\n❌ Setup incomplete. Please fix the issues above.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n👋 Setup cancelled.")
    except Exception as e:
        print(f"\n❌ Setup error: {e}")
        sys.exit(1)
