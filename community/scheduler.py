import asyncio
import logging
import os
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from config import db, application
from community.content_generator import AIContentGenerator
from community.poster import CommunityPoster

logger = logging.getLogger(__name__)


class CommunityScheduler:
    """Manages scheduled posting of community content"""
    
    def __init__(self):
        self.scheduler = None
        self.content_generator = AIContentGenerator()
        self.poster = CommunityPoster()
        self.timezone = pytz.UTC
        self.is_running = False
        
        # Content schedule configuration
        self.schedule_config = self._load_schedule_config()
    
    def _load_schedule_config(self) -> Dict:
        """Load posting schedule from database or use defaults"""
        try:
            # Try to load from database
            config = db.community_settings.find_one({"type": "schedule_config"})
            if config and config.get("schedule"):
                return config["schedule"]
        except Exception as e:
            logger.warning(f"Could not load schedule from database: {e}")
        
        # Default schedule
        return {
            "enabled": True,
            "posts_per_day": 2,
            "weekly_schedule": {
                "monday": [
                    {"time": "09:00", "type": "market_brief"},
                    {"time": "18:00", "type": "educational"}
                ],
                "tuesday": [
                    {"time": "10:00", "type": "educational"},
                    {"time": "17:00", "type": "platform_update"}
                ],
                "wednesday": [
                    {"time": "09:00", "type": "market_brief"},
                    {"time": "19:00", "type": "security_tip"}
                ],
                "thursday": [
                    {"time": "10:00", "type": "platform_update"},
                    {"time": "18:00", "type": "educational"}
                ],
                "friday": [
                    {"time": "09:00", "type": "market_brief"},
                    {"time": "17:00", "type": "educational"}
                ],
                "saturday": [
                    {"time": "11:00", "type": "educational"}
                ],
                "sunday": [
                    {"time": "16:00", "type": "weekly_analysis"}
                ]
            }
        }
    
    async def initialize(self):
        """Initialize the scheduler"""
        try:
            if self.scheduler is not None:
                logger.warning("Scheduler already initialized")
                return
            
            # Create scheduler with timezone handling
            self.scheduler = AsyncIOScheduler(timezone=self.timezone)
            
            # Add jobs based on schedule configuration
            if self.schedule_config.get("enabled", True):
                await self._setup_scheduled_jobs()
            
            logger.info("Community scheduler initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize community scheduler: {e}")
            raise
    
    async def _setup_scheduled_jobs(self):
        """Set up all scheduled jobs based on configuration"""
        try:
            weekly_schedule = self.schedule_config.get("weekly_schedule", {})
            
            for day_name, posts in weekly_schedule.items():
                for post_config in posts:
                    post_time = post_config.get("time")
                    content_type = post_config.get("type")
                    
                    if not post_time or not content_type:
                        logger.warning(f"Invalid post config for {day_name}: {post_config}")
                        continue
                    
                    # Parse time (format: "HH:MM")
                    try:
                        hour, minute = map(int, post_time.split(':'))
                    except ValueError:
                        logger.error(f"Invalid time format: {post_time}")
                        continue
                    
                    # Map day names to cron day_of_week values
                    day_mapping = {
                        'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                        'friday': 4, 'saturday': 5, 'sunday': 6
                    }
                    
                    day_of_week = day_mapping.get(day_name.lower())
                    if day_of_week is None:
                        logger.error(f"Invalid day name: {day_name}")
                        continue
                    
                    # Create cron trigger
                    trigger = CronTrigger(
                        day_of_week=day_of_week,
                        hour=hour,
                        minute=minute,
                        timezone=self.timezone
                    )
                    
                    # Add job to scheduler
                    job_id = f"community_post_{day_name}_{post_time}_{content_type}"
                    
                    self.scheduler.add_job(
                        func=self._generate_and_post_content,
                        trigger=trigger,
                        args=[content_type],
                        id=job_id,
                        name=f"Community Post: {content_type} on {day_name} at {post_time}",
                        replace_existing=True,
                        max_instances=1
                    )
                    
                    logger.info(f"Scheduled job: {job_id}")
            
            logger.info(f"Set up {len(self.scheduler.get_jobs())} scheduled community posts")
            
        except Exception as e:
            logger.error(f"Error setting up scheduled jobs: {e}")
            raise
    
    async def start(self):
        """Start the scheduler"""
        try:
            if not self.scheduler:
                await self.initialize()
            
            if self.is_running:
                logger.warning("Scheduler is already running")
                return
            
            self.scheduler.start()
            self.is_running = True
            logger.info("Community content scheduler started")
            
            # Log next scheduled posts
            jobs = self.scheduler.get_jobs()
            if jobs:
                logger.info("Next scheduled posts:")
                for job in jobs[:5]:  # Show next 5 jobs
                    logger.info(f"  - {job.name}: {job.next_run_time}")
            
        except Exception as e:
            logger.error(f"Failed to start community scheduler: {e}")
            raise
    
    async def stop(self):
        """Stop the scheduler"""
        try:
            if self.scheduler and self.is_running:
                self.scheduler.shutdown(wait=False)
                self.is_running = False
                logger.info("Community content scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
    
    async def _generate_and_post_content(self, content_type: str):
        """Generate and post content - called by scheduled jobs"""
        try:
            logger.info(f"Generating {content_type} content for community post")
            
            # Check if posting is enabled in database
            if not await self._is_posting_enabled():
                logger.info("Community posting is disabled, skipping")
                return
            
            # Generate content
            content = await self.content_generator.generate_content(content_type)
            
            if not content:
                logger.error(f"Failed to generate {content_type} content")
                return
            
            # Post to channel
            success = await self.poster.post_to_channel(content, content_type)
            
            if success:
                # Log successful post
                await self._log_post(content_type, content, success=True)
                logger.info(f"Successfully posted {content_type} content to community")
            else:
                logger.error(f"Failed to post {content_type} content to community")
                await self._log_post(content_type, content, success=False)
                
        except Exception as e:
            logger.error(f"Error in scheduled content generation for {content_type}: {e}")
            await self._log_post(content_type, f"Error: {str(e)}", success=False)
    
    async def _is_posting_enabled(self) -> bool:
        """Check if community posting is enabled"""
        try:
            settings = db.community_settings.find_one({"type": "posting_settings"})
            return settings.get("enabled", True) if settings else True
        except Exception as e:
            logger.error(f"Error checking posting settings: {e}")
            return True  # Default to enabled
    
    async def _log_post(self, content_type: str, content: str, success: bool):
        """Log post attempt to database"""
        try:
            log_entry = {
                "timestamp": datetime.now(),
                "content_type": content_type,
                "content": content[:500],  # Store first 500 chars
                "success": success,
                "scheduled": True
            }
            
            db.community_posts.insert_one(log_entry)
            
        except Exception as e:
            logger.error(f"Error logging post: {e}")
    
    # Admin control methods
    async def update_schedule(self, new_schedule: Dict) -> bool:
        """Update the posting schedule"""
        try:
            # Validate schedule format
            if not self._validate_schedule(new_schedule):
                logger.error("Invalid schedule format")
                return False
            
            # Update database
            db.community_settings.update_one(
                {"type": "schedule_config"},
                {"$set": {"schedule": new_schedule, "updated_at": datetime.now()}},
                upsert=True
            )
            
            # Update in-memory config
            self.schedule_config = new_schedule
            
            # Restart scheduler with new config
            if self.is_running:
                await self.stop()
                await self.initialize()
                await self.start()
            
            logger.info("Community posting schedule updated")
            return True
            
        except Exception as e:
            logger.error(f"Error updating schedule: {e}")
            return False
    
    async def enable_posting(self, enabled: bool) -> bool:
        """Enable or disable community posting"""
        try:
            db.community_settings.update_one(
                {"type": "posting_settings"},
                {"$set": {"enabled": enabled, "updated_at": datetime.now()}},
                upsert=True
            )
            
            logger.info(f"Community posting {'enabled' if enabled else 'disabled'}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating posting settings: {e}")
            return False
    
    async def post_now(self, content_type: str) -> bool:
        """Manually trigger a post now"""
        try:
            logger.info(f"Manual post requested: {content_type}")
            await self._generate_and_post_content(content_type)
            return True
        except Exception as e:
            logger.error(f"Error in manual post: {e}")
            return False
    
    def _validate_schedule(self, schedule: Dict) -> bool:
        """Validate schedule configuration format"""
        try:
            required_keys = ["enabled", "weekly_schedule"]
            if not all(key in schedule for key in required_keys):
                return False
            
            weekly_schedule = schedule["weekly_schedule"]
            valid_days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            valid_content_types = ["market_brief", "educational", "platform_update", "security_tip", "weekly_analysis"]
            
            for day, posts in weekly_schedule.items():
                if day not in valid_days:
                    return False
                
                for post in posts:
                    if not isinstance(post, dict) or "time" not in post or "type" not in post:
                        return False
                    
                    # Validate time format (HH:MM)
                    try:
                        time_parts = post["time"].split(":")
                        if len(time_parts) != 2:
                            return False
                        hour, minute = map(int, time_parts)
                        if not (0 <= hour <= 23 and 0 <= minute <= 59):
                            return False
                    except (ValueError, AttributeError):
                        return False
                    
                    # Validate content type
                    if post["type"] not in valid_content_types:
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating schedule: {e}")
            return False
    
    def get_status(self) -> Dict:
        """Get current scheduler status"""
        try:
            jobs = self.scheduler.get_jobs() if self.scheduler else []
            next_posts = []
            
            for job in jobs[:5]:  # Next 5 jobs
                next_posts.append({
                    "name": job.name,
                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                    "content_type": job.args[0] if job.args else "unknown"
                })
            
            return {
                "running": self.is_running,
                "total_jobs": len(jobs),
                "next_posts": next_posts,
                "schedule_enabled": self.schedule_config.get("enabled", False)
            }
            
        except Exception as e:
            logger.error(f"Error getting scheduler status: {e}")
            return {
                "running": False,
                "total_jobs": 0,
                "next_posts": [],
                "error": str(e)
            }


# Global scheduler instance
community_scheduler = None


async def get_community_scheduler() -> CommunityScheduler:
    """Get or create the global community scheduler instance"""
    global community_scheduler
    
    if community_scheduler is None:
        community_scheduler = CommunityScheduler()
        await community_scheduler.initialize()
    
    return community_scheduler


async def start_community_scheduler():
    """Start the community content scheduler"""
    try:
        scheduler = await get_community_scheduler()
        await scheduler.start()
        logger.info("Community content scheduler started successfully")
    except Exception as e:
        logger.error(f"Failed to start community scheduler: {e}")


async def stop_community_scheduler():
    """Stop the community content scheduler"""
    try:
        global community_scheduler
        if community_scheduler:
            await community_scheduler.stop()
            community_scheduler = None
        logger.info("Community content scheduler stopped")
    except Exception as e:
        logger.error(f"Error stopping community scheduler: {e}")
