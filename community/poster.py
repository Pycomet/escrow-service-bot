import logging
import os
from datetime import datetime
from typing import Optional

from telegram import Bot
from telegram.error import TelegramError

from config import db, get_application

logger = logging.getLogger(__name__)


class CommunityPoster:
    """Handles posting content to the community Telegram channel"""

    def __init__(self):
        self.bot = None
        self.channel_id = os.getenv("COMMUNITY_CHANNEL_ID")

        if not self.channel_id:
            logger.warning("COMMUNITY_CHANNEL_ID not set. Community posting disabled.")

    async def _get_bot(self) -> Optional[Bot]:
        """Get Telegram bot instance"""
        if self.bot is None:
            try:
                app = get_application()
                if app and hasattr(app, "bot"):
                    self.bot = app.bot
                else:
                    logger.error("Could not get bot from application")
                    return None
            except Exception as e:
                logger.error(f"Error getting bot instance: {e}")
                return None

        return self.bot

    async def post_to_channel(
        self, content: str, content_type: str = "general"
    ) -> bool:
        """Post content to the community channel"""
        try:
            if not self.channel_id:
                logger.error("Community channel ID not configured")
                return False

            bot = await self._get_bot()
            if not bot:
                logger.error("Bot not available for posting")
                return False

            # Clean and validate content
            cleaned_content = self._clean_content(content)
            if not cleaned_content:
                logger.error("Content is empty after cleaning")
                return False

            # Post to channel
            message = await bot.send_message(
                chat_id=self.channel_id,
                text=cleaned_content,
                parse_mode="HTML",
                disable_web_page_preview=True,
            )

            if message:
                logger.info(f"Successfully posted {content_type} content to channel")

                # Log successful post to database
                await self._log_successful_post(
                    content_type, cleaned_content, message.message_id
                )

                return True
            else:
                logger.error("Failed to post message - no message returned")
                return False

        except TelegramError as e:
            logger.error(f"Telegram error posting to channel: {e}")

            # Handle specific Telegram errors
            if "chat not found" in str(e).lower():
                logger.error(
                    "Channel not found. Check COMMUNITY_CHANNEL_ID configuration."
                )
            elif "bot was blocked" in str(e).lower():
                logger.error("Bot was blocked from the channel")
            elif "not enough rights" in str(e).lower():
                logger.error("Bot doesn't have permission to post in the channel")

            return False

        except Exception as e:
            logger.error(f"Unexpected error posting to channel: {e}")
            return False

    def _clean_content(self, content: str) -> str:
        """Clean and validate content before posting"""
        try:
            if not content:
                return ""

            # Preserve line breaks while removing excessive whitespace on each line
            lines = content.split("\n")
            cleaned_lines = []

            for line in lines:
                # Remove excessive whitespace within each line
                cleaned_line = " ".join(line.split())
                cleaned_lines.append(cleaned_line)

            # Join lines back together with newlines
            cleaned = "\n".join(cleaned_lines)

            # Remove excessive consecutive blank lines (more than 2 newlines becomes 2)
            import re

            cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

            # Ensure content isn't too long (Telegram limit is 4096 characters)
            if len(cleaned) > 4000:  # Leave some buffer
                cleaned = cleaned[:3997] + "..."
                logger.warning("Content was truncated due to length")

            # Basic HTML validation - ensure tags are properly closed
            cleaned = self._fix_html_tags(cleaned)

            return cleaned

        except Exception as e:
            logger.error(f"Error cleaning content: {e}")
            return content  # Return original if cleaning fails

    def _fix_html_tags(self, content: str) -> str:
        """Basic HTML tag validation and fixing"""
        try:
            # Simple validation for common HTML tags used in Telegram
            import re

            # Find unclosed bold tags
            bold_open = len(re.findall(r"<b>", content))
            bold_close = len(re.findall(r"</b>", content))
            if bold_open > bold_close:
                content += "</b>" * (bold_open - bold_close)

            # Find unclosed italic tags
            italic_open = len(re.findall(r"<i>", content))
            italic_close = len(re.findall(r"</i>", content))
            if italic_open > italic_close:
                content += "</i>" * (italic_open - italic_close)

            # Find unclosed code tags
            code_open = len(re.findall(r"<code>", content))
            code_close = len(re.findall(r"</code>", content))
            if code_open > code_close:
                content += "</code>" * (code_open - code_close)

            return content

        except Exception as e:
            logger.error(f"Error fixing HTML tags: {e}")
            return content

    async def _log_successful_post(
        self, content_type: str, content: str, message_id: int
    ):
        """Log successful post to database"""
        try:
            log_entry = {
                "timestamp": datetime.now(),
                "content_type": content_type,
                "content": content,
                "message_id": message_id,
                "channel_id": self.channel_id,
                "success": True,
                "method": "automated",
            }

            db.community_posts.insert_one(log_entry)

        except Exception as e:
            logger.error(f"Error logging successful post: {e}")

    async def test_channel_connection(self) -> dict:
        """Test connection to the community channel"""
        try:
            if not self.channel_id:
                return {
                    "success": False,
                    "error": "COMMUNITY_CHANNEL_ID not configured",
                }

            bot = await self._get_bot()
            if not bot:
                return {"success": False, "error": "Bot not available"}

            # Try to get chat info
            chat = await bot.get_chat(self.channel_id)

            return {
                "success": True,
                "channel_title": chat.title,
                "channel_type": chat.type,
                "channel_id": self.channel_id,
                "member_count": getattr(chat, "member_count", "Unknown"),
            }

        except TelegramError as e:
            return {"success": False, "error": f"Telegram error: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {str(e)}"}

    async def post_test_message(self) -> dict:
        """Post a test message to verify posting works"""
        try:
            test_content = f"""🧪 **Test Message**

This is a test message from the escrow bot community system.

✅ Content generation: Working
✅ Channel connection: Working  
✅ Posting system: Working

Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

#TestMessage #SystemCheck"""

            success = await self.post_to_channel(test_content, "test")

            if success:
                return {"success": True, "message": "Test message posted successfully"}
            else:
                return {"success": False, "error": "Failed to post test message"}

        except Exception as e:
            return {"success": False, "error": f"Error posting test message: {str(e)}"}

    async def get_recent_posts(self, limit: int = 10) -> list:
        """Get recent posts from the database"""
        try:
            posts = list(db.community_posts.find().sort("timestamp", -1).limit(limit))

            # Convert ObjectId to string for JSON serialization
            for post in posts:
                if "_id" in post:
                    post["_id"] = str(post["_id"])
                if "timestamp" in post:
                    post["timestamp"] = post["timestamp"].isoformat()

            return posts

        except Exception as e:
            logger.error(f"Error getting recent posts: {e}")
            return []

    async def get_posting_stats(self) -> dict:
        """Get posting statistics"""
        try:
            # Total posts
            total_posts = db.community_posts.count_documents({})

            # Successful posts
            successful_posts = db.community_posts.count_documents({"success": True})

            # Posts by type
            pipeline = [{"$group": {"_id": "$content_type", "count": {"$sum": 1}}}]
            posts_by_type = list(db.community_posts.aggregate(pipeline))

            # Recent activity (last 7 days)
            from datetime import timedelta

            week_ago = datetime.now() - timedelta(days=7)
            recent_posts = db.community_posts.count_documents(
                {"timestamp": {"$gte": week_ago}}
            )

            return {
                "total_posts": total_posts,
                "successful_posts": successful_posts,
                "success_rate": (successful_posts / total_posts * 100)
                if total_posts > 0
                else 0,
                "posts_by_type": {item["_id"]: item["count"] for item in posts_by_type},
                "recent_posts_7_days": recent_posts,
            }

        except Exception as e:
            logger.error(f"Error getting posting stats: {e}")
            return {
                "total_posts": 0,
                "successful_posts": 0,
                "success_rate": 0,
                "posts_by_type": {},
                "recent_posts_7_days": 0,
                "error": str(e),
            }
