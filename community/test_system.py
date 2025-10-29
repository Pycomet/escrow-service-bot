#!/usr/bin/env python3
"""
Test script for the community content management system.
Run this to verify all components are working correctly.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from content_generator import AIContentGenerator, MarketDataFetcher
from poster import CommunityPoster
from scheduler import get_community_scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_market_data():
    """Test market data fetching"""
    logger.info("🔍 Testing market data fetching...")

    try:
        fetcher = MarketDataFetcher()
        market_data = await fetcher.get_market_data()

        logger.info(f"✅ Market data fetched successfully")
        logger.info(
            f"   📊 BTC: ${market_data['prices']['BTC']:,.0f} ({market_data['changes']['BTC']:+.1f}%)"
        )
        logger.info(
            f"   📊 ETH: ${market_data['prices']['ETH']:,.0f} ({market_data['changes']['ETH']:+.1f}%)"
        )
        logger.info(f"   📊 Sentiment: {market_data['market_sentiment']}")
        return True

    except Exception as e:
        logger.error(f"❌ Market data test failed: {e}")
        return False


async def test_content_generation():
    """Test AI content generation"""
    logger.info("🤖 Testing AI content generation...")

    try:
        generator = AIContentGenerator()

        # Test different content types
        content_types = [
            "educational",
            "market_brief",
            "platform_update",
            "security_tip",
        ]

        for content_type in content_types:
            logger.info(f"   Generating {content_type} content...")
            content = await generator.generate_content(content_type)

            if content:
                preview = content[:100] + "..." if len(content) > 100 else content
                logger.info(f"   ✅ {content_type}: {preview}")
            else:
                logger.error(f"   ❌ {content_type}: Failed to generate")
                return False

        logger.info("✅ All content types generated successfully")
        return True

    except Exception as e:
        logger.error(f"❌ Content generation test failed: {e}")
        return False


async def test_channel_connection():
    """Test Telegram channel connection"""
    logger.info("📡 Testing channel connection...")

    try:
        poster = CommunityPoster()
        result = await poster.test_channel_connection()

        if result.get("success"):
            logger.info("✅ Channel connection successful")
            logger.info(f"   📍 Channel: {result.get('channel_title', 'Unknown')}")
            logger.info(f"   👥 Members: {result.get('member_count', 'Unknown')}")
            return True
        else:
            logger.error(f"❌ Channel connection failed: {result.get('error')}")
            return False

    except Exception as e:
        logger.error(f"❌ Channel connection test failed: {e}")
        return False


async def test_posting(dry_run=True):
    """Test posting to channel"""
    logger.info(f"📤 Testing posting to channel (dry_run={dry_run})...")

    try:
        if not dry_run:
            poster = CommunityPoster()
            result = await poster.post_test_message()

            if result.get("success"):
                logger.info("✅ Test message posted successfully")
                return True
            else:
                logger.error(f"❌ Posting failed: {result.get('error')}")
                return False
        else:
            logger.info("✅ Posting test skipped (dry run mode)")
            return True

    except Exception as e:
        logger.error(f"❌ Posting test failed: {e}")
        return False


async def test_scheduler():
    """Test scheduler functionality"""
    logger.info("⏰ Testing scheduler...")

    try:
        scheduler = await get_community_scheduler()
        status = scheduler.get_status()

        logger.info(f"   📊 Running: {status.get('running', False)}")
        logger.info(f"   📊 Jobs: {status.get('total_jobs', 0)}")

        if status.get("next_posts"):
            logger.info("   📅 Next posts:")
            for post in status["next_posts"][:3]:
                logger.info(
                    f"      • {post.get('content_type')}: {post.get('next_run', 'Unknown')}"
                )

        logger.info("✅ Scheduler test completed")
        return True

    except Exception as e:
        logger.error(f"❌ Scheduler test failed: {e}")
        return False


async def test_database_connection():
    """Test database connectivity"""
    logger.info("🗄️ Testing database connection...")

    try:
        from config import db

        # Test basic database operations
        test_doc = {"test": True, "timestamp": datetime.now(), "type": "system_test"}

        # Insert test document
        result = db.community_posts.insert_one(test_doc)

        # Find and delete test document
        found_doc = db.community_posts.find_one({"_id": result.inserted_id})
        db.community_posts.delete_one({"_id": result.inserted_id})

        if found_doc:
            logger.info("✅ Database connection successful")
            return True
        else:
            logger.error("❌ Database test failed - document not found")
            return False

    except Exception as e:
        logger.error(f"❌ Database test failed: {e}")
        return False


async def run_full_test(post_to_channel=False):
    """Run all tests"""
    logger.info("🧪 Starting Community Content System Tests")
    logger.info("=" * 50)

    test_results = {}

    # Run tests
    test_results["database"] = await test_database_connection()
    test_results["market_data"] = await test_market_data()
    test_results["content_generation"] = await test_content_generation()
    test_results["channel_connection"] = await test_channel_connection()
    test_results["posting"] = await test_posting(dry_run=not post_to_channel)
    test_results["scheduler"] = await test_scheduler()

    # Summary
    logger.info("=" * 50)
    logger.info("🏁 Test Results Summary:")

    passed = 0
    total = len(test_results)

    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"   {test_name.replace('_', ' ').title()}: {status}")
        if result:
            passed += 1

    logger.info(f"\n📊 Overall: {passed}/{total} tests passed")

    if passed == total:
        logger.info("🎉 All tests passed! Community system is ready.")
        return True
    else:
        logger.error("⚠️ Some tests failed. Please check the logs above.")
        return False


async def generate_sample_content():
    """Generate sample content for review"""
    logger.info("📝 Generating sample content...")

    try:
        generator = AIContentGenerator()
        content_types = [
            "educational",
            "market_brief",
            "platform_update",
            "security_tip",
        ]

        for content_type in content_types:
            logger.info(f"\n--- {content_type.upper()} SAMPLE ---")
            content = await generator.generate_content(content_type)

            if content:
                print(content)
                print("\n" + "-" * 50)
            else:
                logger.error(f"Failed to generate {content_type} content")

        return True

    except Exception as e:
        logger.error(f"Error generating sample content: {e}")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test community content system")
    parser.add_argument(
        "--post", action="store_true", help="Actually post test message to channel"
    )
    parser.add_argument(
        "--samples", action="store_true", help="Generate sample content"
    )
    parser.add_argument("--quick", action="store_true", help="Run quick tests only")

    args = parser.parse_args()

    if args.samples:
        asyncio.run(generate_sample_content())
    elif args.quick:

        async def quick_test():
            logger.info("🚀 Running quick tests...")
            await test_database_connection()
            await test_market_data()
            await test_content_generation()

        asyncio.run(quick_test())
    else:
        asyncio.run(run_full_test(post_to_channel=args.post))
