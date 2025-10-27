import logging
from datetime import datetime
from typing import Dict, Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from community.content_generator import AIContentGenerator
from community.poster import CommunityPoster
from community.scheduler import get_community_scheduler
from config import db
from handlers.admin import AdminWalletManager

logger = logging.getLogger(__name__)


class CommunityAdminHandlers:
    """Admin handlers for community content management"""

    @staticmethod
    async def community_menu_handler(
        update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Main community management menu"""
        query = update.callback_query
        user_id = query.from_user.id

        if not await AdminWalletManager.is_admin(user_id):
            await query.answer("❌ Access denied.")
            return

        await query.answer()

        # Get current status
        scheduler = await get_community_scheduler()
        status = scheduler.get_status()
        poster = CommunityPoster()
        stats = await poster.get_posting_stats()

        status_text = f"""🏘️ <b>Community Content Management</b>

📊 <b>Current Status:</b>
• Scheduler: {'🟢 Running' if status['running'] else '🔴 Stopped'}
• Total Jobs: {status['total_jobs']}
• Posts Today: {stats['recent_posts_7_days']}
• Success Rate: {stats['success_rate']:.1f}%

📅 <b>Next Posts:</b>"""

        if status.get("next_posts"):
            for post in status["next_posts"][:3]:
                next_time = post.get("next_run", "Unknown")
                if next_time and next_time != "Unknown":
                    try:
                        from datetime import datetime

                        dt = datetime.fromisoformat(next_time.replace("Z", "+00:00"))
                        time_str = dt.strftime("%m/%d %H:%M")
                    except:
                        time_str = "Unknown"
                else:
                    time_str = "Unknown"

                status_text += f"\n• {post.get('content_type', 'Unknown')}: {time_str}"
        else:
            status_text += "\n• No scheduled posts"

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "📝 Post Now", callback_data="community_post_now"
                    ),
                    InlineKeyboardButton(
                        "⚙️ Settings", callback_data="community_settings"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "📊 Statistics", callback_data="community_stats"
                    ),
                    InlineKeyboardButton(
                        "🧪 Test System", callback_data="community_test"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "🔄 Restart Scheduler", callback_data="community_restart"
                    ),
                    InlineKeyboardButton(
                        "📋 View Posts", callback_data="community_view_posts"
                    ),
                ],
                [InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_menu")],
            ]
        )

        await query.edit_message_text(
            status_text, parse_mode="HTML", reply_markup=keyboard
        )

    @staticmethod
    async def post_now_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle immediate posting"""
        query = update.callback_query
        user_id = query.from_user.id

        if not await AdminWalletManager.is_admin(user_id):
            await query.answer("❌ Access denied.")
            return

        await query.answer()

        # Show content type selection
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "📈 Market Brief", callback_data="post_now_market_brief"
                    ),
                    InlineKeyboardButton(
                        "🎓 Educational", callback_data="post_now_educational"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "🔧 Platform Update", callback_data="post_now_platform_update"
                    ),
                    InlineKeyboardButton(
                        "🔐 Security Tip", callback_data="post_now_security_tip"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "📊 Weekly Analysis", callback_data="post_now_weekly_analysis"
                    )
                ],
                [InlineKeyboardButton("🔙 Back", callback_data="admin_community")],
            ]
        )

        await query.edit_message_text(
            "📝 <b>Post Content Now</b>\n\nSelect the type of content to generate and post:",
            parse_mode="HTML",
            reply_markup=keyboard,
        )

    @staticmethod
    async def execute_post_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Execute immediate posting"""
        query = update.callback_query
        user_id = query.from_user.id

        if not await AdminWalletManager.is_admin(user_id):
            await query.answer("❌ Access denied.")
            return

        # Extract content type from callback data
        content_type = query.data.replace("post_now_", "")

        await query.answer("⏳ Generating and posting content...")

        try:
            # Show loading message
            await query.edit_message_text(
                f"⏳ <b>Generating {content_type.replace('_', ' ').title()} Content</b>\n\n"
                "Please wait while I create and post the content...",
                parse_mode="HTML",
            )

            # Generate content
            generator = AIContentGenerator()
            content = await generator.generate_content(content_type)

            if not content:
                await query.edit_message_text(
                    f"❌ <b>Content Generation Failed</b>\n\n"
                    f"Could not generate {content_type} content. Please try again.",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "🔙 Back", callback_data="admin_community"
                                )
                            ]
                        ]
                    ),
                )
                return

            # Post to channel
            poster = CommunityPoster()
            success = await poster.post_to_channel(content, content_type)

            if success:
                # Log manual post
                db.community_posts.insert_one(
                    {
                        "timestamp": datetime.now(),
                        "content_type": content_type,
                        "content": content[:500],
                        "success": True,
                        "method": "manual",
                        "admin_id": str(user_id),
                    }
                )

                preview = content[:200] + "..." if len(content) > 200 else content

                await query.edit_message_text(
                    f"✅ <b>Content Posted Successfully!</b>\n\n"
                    f"<b>Type:</b> {content_type.replace('_', ' ').title()}\n"
                    f"<b>Preview:</b>\n{preview}",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "🔙 Back", callback_data="admin_community"
                                )
                            ]
                        ]
                    ),
                )
            else:
                await query.edit_message_text(
                    f"❌ <b>Posting Failed</b>\n\n"
                    f"Content was generated but could not be posted to the channel.\n"
                    f"Please check channel configuration and bot permissions.",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "🔙 Back", callback_data="admin_community"
                                )
                            ]
                        ]
                    ),
                )

        except Exception as e:
            logger.error(f"Error in manual post: {e}")
            await query.edit_message_text(
                f"❌ <b>Error</b>\n\n" f"An error occurred: {str(e)}",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔙 Back", callback_data="admin_community")]]
                ),
            )

    @staticmethod
    async def settings_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Community settings management"""
        query = update.callback_query
        user_id = query.from_user.id

        if not await AdminWalletManager.is_admin(user_id):
            await query.answer("❌ Access denied.")
            return

        await query.answer()

        # Get current settings
        try:
            posting_settings = (
                db.community_settings.find_one({"type": "posting_settings"}) or {}
            )
            schedule_settings = (
                db.community_settings.find_one({"type": "schedule_config"}) or {}
            )

            posting_enabled = posting_settings.get("enabled", True)
            posts_per_day = schedule_settings.get("schedule", {}).get(
                "posts_per_day", 2
            )

        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            posting_enabled = True
            posts_per_day = 2

        settings_text = f"""⚙️ <b>Community Settings</b>

📝 <b>Posting Status:</b> {'🟢 Enabled' if posting_enabled else '🔴 Disabled'}
📊 <b>Posts per Day:</b> {posts_per_day}

🔧 <b>Actions:</b>"""

        keyboard = [
            [
                InlineKeyboardButton(
                    "🔴 Disable Posting" if posting_enabled else "🟢 Enable Posting",
                    callback_data="community_toggle_posting",
                )
            ],
            [
                InlineKeyboardButton(
                    "📅 Edit Schedule", callback_data="community_edit_schedule"
                ),
                InlineKeyboardButton(
                    "🔄 Reset to Default", callback_data="community_reset_schedule"
                ),
            ],
            [InlineKeyboardButton("🔙 Back", callback_data="admin_community")],
        ]

        await query.edit_message_text(
            settings_text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    @staticmethod
    async def toggle_posting_handler(
        update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Toggle posting on/off"""
        query = update.callback_query
        user_id = query.from_user.id

        if not await AdminWalletManager.is_admin(user_id):
            await query.answer("❌ Access denied.")
            return

        try:
            # Get current status
            settings = (
                db.community_settings.find_one({"type": "posting_settings"}) or {}
            )
            current_enabled = settings.get("enabled", True)
            new_enabled = not current_enabled

            # Update database
            db.community_settings.update_one(
                {"type": "posting_settings"},
                {"$set": {"enabled": new_enabled, "updated_at": datetime.now()}},
                upsert=True,
            )

            # Update scheduler
            scheduler = await get_community_scheduler()
            await scheduler.enable_posting(new_enabled)

            await query.answer(f"✅ Posting {'enabled' if new_enabled else 'disabled'}")

            # Return to settings
            await CommunityAdminHandlers.settings_handler(update, context)

        except Exception as e:
            logger.error(f"Error toggling posting: {e}")
            await query.answer("❌ Error updating settings")

    @staticmethod
    async def test_system_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Test the community system"""
        query = update.callback_query
        user_id = query.from_user.id

        if not await AdminWalletManager.is_admin(user_id):
            await query.answer("❌ Access denied.")
            return

        await query.answer("🧪 Testing system...")

        await query.edit_message_text(
            "🧪 <b>Testing Community System</b>\n\n⏳ Running tests...", parse_mode="HTML"
        )

        try:
            test_results = []

            # Test 1: Content Generation
            try:
                generator = AIContentGenerator()
                test_content = await generator.generate_content("educational")
                if test_content:
                    test_results.append("✅ Content Generation: Working")
                else:
                    test_results.append("❌ Content Generation: Failed")
            except Exception as e:
                test_results.append(f"❌ Content Generation: Error - {str(e)[:50]}")

            # Test 2: Channel Connection
            poster = CommunityPoster()
            channel_test = await poster.test_channel_connection()
            if channel_test.get("success"):
                test_results.append("✅ Channel Connection: Working")
                test_results.append(
                    f"   📍 Channel: {channel_test.get('channel_title', 'Unknown')}"
                )
            else:
                test_results.append(
                    f"❌ Channel Connection: {channel_test.get('error', 'Unknown error')}"
                )

            # Test 3: Database Access
            try:
                db.community_posts.find_one()
                test_results.append("✅ Database Access: Working")
            except Exception as e:
                test_results.append(f"❌ Database Access: Error - {str(e)[:50]}")

            # Test 4: Scheduler Status
            try:
                scheduler = await get_community_scheduler()
                status = scheduler.get_status()
                if status.get("running"):
                    test_results.append("✅ Scheduler: Running")
                else:
                    test_results.append("❌ Scheduler: Not Running")
            except Exception as e:
                test_results.append(f"❌ Scheduler: Error - {str(e)[:50]}")

            results_text = "🧪 <b>System Test Results</b>\n\n" + "\n".join(test_results)

            keyboard = [
                [
                    InlineKeyboardButton(
                        "📤 Post Test Message", callback_data="community_post_test"
                    ),
                ],
                [InlineKeyboardButton("🔙 Back", callback_data="admin_community")],
            ]

            await query.edit_message_text(
                results_text,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        except Exception as e:
            logger.error(f"Error in system test: {e}")
            await query.edit_message_text(
                f"❌ <b>Test Failed</b>\n\nError: {str(e)}",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔙 Back", callback_data="admin_community")]]
                ),
            )

    @staticmethod
    async def post_test_message_handler(
        update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Post a test message to the channel"""
        query = update.callback_query
        user_id = query.from_user.id

        if not await AdminWalletManager.is_admin(user_id):
            await query.answer("❌ Access denied.")
            return

        await query.answer("📤 Posting test message...")

        try:
            poster = CommunityPoster()
            result = await poster.post_test_message()

            if result.get("success"):
                await query.edit_message_text(
                    "✅ <b>Test Message Posted Successfully!</b>\n\n"
                    "Check your community channel to see the test message.",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "🔙 Back", callback_data="admin_community"
                                )
                            ]
                        ]
                    ),
                )
            else:
                await query.edit_message_text(
                    f"❌ <b>Test Message Failed</b>\n\n"
                    f"Error: {result.get('error', 'Unknown error')}",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "🔙 Back", callback_data="admin_community"
                                )
                            ]
                        ]
                    ),
                )

        except Exception as e:
            logger.error(f"Error posting test message: {e}")
            await query.edit_message_text(
                f"❌ <b>Error</b>\n\nFailed to post test message: {str(e)}",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔙 Back", callback_data="admin_community")]]
                ),
            )

    @staticmethod
    async def view_posts_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """View recent posts"""
        query = update.callback_query
        user_id = query.from_user.id

        if not await AdminWalletManager.is_admin(user_id):
            await query.answer("❌ Access denied.")
            return

        await query.answer()

        try:
            poster = CommunityPoster()
            recent_posts = await poster.get_recent_posts(limit=5)

            if not recent_posts:
                posts_text = "📋 <b>Recent Posts</b>\n\nNo posts found in database."
            else:
                posts_text = "📋 <b>Recent Posts</b>\n\n"

                for i, post in enumerate(recent_posts, 1):
                    timestamp = post.get("timestamp", "Unknown")
                    content_type = post.get("content_type", "Unknown")
                    success = post.get("success", False)
                    content_preview = (
                        post.get("content", "")[:100] + "..."
                        if len(post.get("content", "")) > 100
                        else post.get("content", "")
                    )

                    status_emoji = "✅" if success else "❌"

                    posts_text += f"{i}. {status_emoji} <b>{content_type}</b>\n"
                    posts_text += f"   🕐 {timestamp}\n"
                    posts_text += f"   📝 {content_preview}\n\n"

            await query.edit_message_text(
                posts_text,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔙 Back", callback_data="admin_community")]]
                ),
            )

        except Exception as e:
            logger.error(f"Error viewing posts: {e}")
            await query.edit_message_text(
                f"❌ <b>Error</b>\n\nCould not load recent posts: {str(e)}",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔙 Back", callback_data="admin_community")]]
                ),
            )

    @staticmethod
    async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show detailed community statistics"""
        query = update.callback_query
        user_id = query.from_user.id

        if not await AdminWalletManager.is_admin(user_id):
            await query.answer("❌ Access denied.")
            return

        await query.answer()

        try:
            poster = CommunityPoster()
            stats = await poster.get_posting_stats()

            # Get additional stats from database
            from datetime import datetime, timedelta

            # Posts in last 30 days
            thirty_days_ago = datetime.now() - timedelta(days=30)
            recent_posts = list(
                db.community_posts.find({"timestamp": {"$gte": thirty_days_ago}}).sort(
                    "timestamp", -1
                )
            )

            # Calculate success rate by content type
            content_type_stats = {}
            for post in recent_posts:
                content_type = post.get("content_type", "unknown")
                if content_type not in content_type_stats:
                    content_type_stats[content_type] = {"total": 0, "success": 0}

                content_type_stats[content_type]["total"] += 1
                if post.get("success", False):
                    content_type_stats[content_type]["success"] += 1

            # Get scheduler status
            scheduler = await get_community_scheduler()
            scheduler_status = scheduler.get_status()

            stats_text = f"""📊 <b>Community Statistics</b>

📈 <b>Overall Performance:</b>
• Total Posts (30 days): {len(recent_posts)}
• Success Rate: {stats['success_rate']:.1f}%
• Posts Today: {len([p for p in recent_posts if p.get('timestamp', datetime.min).date() == datetime.now().date()])}
• Posts This Week: {stats['recent_posts_7_days']}

📝 <b>Content Type Breakdown:</b>"""

            for content_type, type_stats in content_type_stats.items():
                success_rate = (
                    (type_stats["success"] / type_stats["total"] * 100)
                    if type_stats["total"] > 0
                    else 0
                )
                stats_text += f"\n• {content_type.replace('_', ' ').title()}: {type_stats['total']} posts ({success_rate:.1f}% success)"

            stats_text += f"""

⚙️ <b>System Status:</b>
• Scheduler: {'🟢 Running' if scheduler_status.get('running') else '🔴 Stopped'}
• Active Jobs: {scheduler_status.get('total_jobs', 0)}
• Database Status: {'🟢 Connected' if db else '🔴 Disconnected'}

📅 <b>Recent Activity:</b>"""

            # Show last 3 posts
            for i, post in enumerate(recent_posts[:3], 1):
                timestamp = post.get("timestamp", datetime.now())
                content_type = post.get("content_type", "Unknown")
                success = post.get("success", False)
                status_emoji = "✅" if success else "❌"

                if isinstance(timestamp, datetime):
                    time_str = timestamp.strftime("%m/%d %H:%M")
                else:
                    time_str = str(timestamp)[:16]

                stats_text += f"\n{i}. {status_emoji} {content_type.replace('_', ' ').title()} - {time_str}"

            if not recent_posts:
                stats_text += "\nNo recent posts found."

            await query.edit_message_text(
                stats_text,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔙 Back", callback_data="admin_community")]]
                ),
            )

        except Exception as e:
            logger.error(f"Error loading statistics: {e}")
            await query.edit_message_text(
                f"❌ <b>Error Loading Statistics</b>\n\n"
                f"Could not load community statistics: {str(e)}",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔙 Back", callback_data="admin_community")]]
                ),
            )

    @staticmethod
    async def restart_scheduler_handler(
        update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Restart the community scheduler"""
        query = update.callback_query
        user_id = query.from_user.id

        if not await AdminWalletManager.is_admin(user_id):
            await query.answer("❌ Access denied.")
            return

        await query.answer("🔄 Restarting scheduler...")

        try:
            scheduler = await get_community_scheduler()

            # Stop and restart
            await scheduler.stop()
            await scheduler.start()

            await query.edit_message_text(
                "✅ <b>Scheduler Restarted Successfully!</b>\n\n"
                "The community content scheduler has been restarted with current configuration.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔙 Back", callback_data="admin_community")]]
                ),
            )

        except Exception as e:
            logger.error(f"Error restarting scheduler: {e}")
            await query.edit_message_text(
                f"❌ <b>Restart Failed</b>\n\n" f"Error: {str(e)}",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔙 Back", callback_data="admin_community")]]
                ),
            )
