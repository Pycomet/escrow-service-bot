import logging
from datetime import datetime
from typing import List, Optional

from config import db
from database.types import BrokerType, UserType

from .user import UserClient
from .utils import generate_id

logger = logging.getLogger(__name__)


class BrokerClient:
    """Handle all broker-related database operations"""

    @staticmethod
    def register_broker(
        user_id: str, broker_name: str, bio: str = "", specialties: List[str] = None
    ) -> BrokerType:
        """Register a new broker"""
        if specialties is None:
            specialties = ["CryptoToFiat"]  # Default specialization

        # Check if broker already exists
        existing_broker = BrokerClient.get_broker(user_id)
        if existing_broker:
            logger.warning(f"Broker already exists for user {user_id}")
            return existing_broker

        broker: BrokerType = {
            "_id": generate_id(),
            "user_id": user_id,
            "broker_name": broker_name,
            "commission_rate": 1.0,  # Default 1% commission
            "is_active": True,
            "is_verified": False,  # Requires admin verification
            "specialties": specialties,
            "total_trades": 0,
            "successful_trades": 0,
            "rating": 0.0,
            "bio": bio,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        db.brokers.insert_one(broker)
        logger.info(f"New broker registered: {broker['_id']} for user {user_id}")
        return broker

    @staticmethod
    def get_broker(user_id: str) -> Optional[BrokerType]:
        """Get broker by user ID"""
        broker = db.brokers.find_one({"user_id": user_id})
        return broker

    @staticmethod
    def get_broker_by_id(broker_id: str) -> Optional[BrokerType]:
        """Get broker by broker ID"""
        broker = db.brokers.find_one({"_id": broker_id})
        return broker

    @staticmethod
    def get_verified_brokers(trade_type: str = None) -> List[BrokerType]:
        """Get all verified and active brokers, optionally filtered by trade type"""
        query = {"is_verified": True, "is_active": True}

        if trade_type:
            query["specialties"] = {"$in": [trade_type]}

        brokers = list(
            db.brokers.find(query).sort([("rating", -1), ("total_trades", -1)])
        )
        return brokers

    @staticmethod
    def verify_broker(broker_id: str, admin_id: str) -> bool:
        """Verify a broker (admin only)"""
        try:
            result = db.brokers.update_one(
                {"_id": broker_id},
                {"$set": {"is_verified": True, "updated_at": datetime.now()}},
            )

            if result.modified_count > 0:
                logger.info(f"Broker {broker_id} verified by admin {admin_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error verifying broker {broker_id}: {e}")
            return False

    @staticmethod
    def update_broker_commission(broker_id: str, commission_rate: float) -> bool:
        """Update broker commission rate"""
        try:
            if commission_rate < 0 or commission_rate > 10:  # Max 10% commission
                logger.error(f"Invalid commission rate: {commission_rate}")
                return False

            result = db.brokers.update_one(
                {"_id": broker_id},
                {
                    "$set": {
                        "commission_rate": commission_rate,
                        "updated_at": datetime.now(),
                    }
                },
            )

            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating broker commission: {e}")
            return False

    @staticmethod
    def add_broker_specialization(broker_id: str, trade_type: str) -> bool:
        """Add a trade type to broker's specializations"""
        try:
            result = db.brokers.update_one(
                {"_id": broker_id},
                {
                    "$addToSet": {"specialties": trade_type},  # Prevents duplicates
                    "$set": {"updated_at": datetime.now()},
                },
            )

            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error adding broker specialization: {e}")
            return False

    @staticmethod
    def validate_broker_for_trade(
        broker_id: str, trade_type: str, seller_id: str, buyer_id: str = None
    ) -> dict:
        """Validate if broker can handle this trade"""
        broker = BrokerClient.get_broker_by_id(broker_id)

        if not broker:
            return {"valid": False, "reason": "Broker not found"}

        if not broker.get("is_verified"):
            return {"valid": False, "reason": "Broker not verified"}

        if not broker.get("is_active"):
            return {"valid": False, "reason": "Broker not active"}

        if trade_type not in broker.get("specialties", []):
            return {
                "valid": False,
                "reason": f"Broker doesn't handle {trade_type} trades",
            }

        # Check if broker is trying to broker their own trade
        if broker.get("user_id") in [seller_id, buyer_id]:
            return {"valid": False, "reason": "Broker cannot mediate their own trade"}

        return {"valid": True, "broker": broker}

    @staticmethod
    def increment_broker_trades(broker_id: str, successful: bool = True) -> bool:
        """Increment broker trade counters"""
        try:
            update_fields = {
                "$inc": {"total_trades": 1},
                "$set": {"updated_at": datetime.now()},
            }

            if successful:
                update_fields["$inc"]["successful_trades"] = 1

            result = db.brokers.update_one({"_id": broker_id}, update_fields)

            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error incrementing broker trades: {e}")
            return False

    @staticmethod
    def rate_broker(broker_id: str, rating: int, trade_id: str) -> bool:
        """Add a rating to broker and recalculate average"""
        try:
            if rating < 1 or rating > 5:
                logger.error(f"Invalid rating: {rating}")
                return False

            # Get current broker data
            broker = BrokerClient.get_broker_by_id(broker_id)
            if not broker:
                return False

            # Add the rating to broker_ratings collection for tracking
            db.broker_ratings.insert_one(
                {
                    "broker_id": broker_id,
                    "trade_id": trade_id,
                    "rating": rating,
                    "created_at": datetime.now(),
                }
            )

            # Recalculate average rating
            pipeline = [
                {"$match": {"broker_id": broker_id}},
                {
                    "$group": {
                        "_id": "$broker_id",
                        "average_rating": {"$avg": "$rating"},
                        "total_ratings": {"$sum": 1},
                    }
                },
            ]

            result = list(db.broker_ratings.aggregate(pipeline))
            if result:
                new_rating = round(result[0]["average_rating"], 1)

                db.brokers.update_one(
                    {"_id": broker_id},
                    {"$set": {"rating": new_rating, "updated_at": datetime.now()}},
                )

                logger.info(f"Broker {broker_id} rating updated to {new_rating}")
                return True

            return False
        except Exception as e:
            logger.error(f"Error rating broker: {e}")
            return False

    @staticmethod
    def get_broker_stats(broker_id: str) -> dict:
        """Get comprehensive broker statistics"""
        broker = BrokerClient.get_broker_by_id(broker_id)
        if not broker:
            return {}

        # Get recent ratings
        recent_ratings = list(
            db.broker_ratings.find({"broker_id": broker_id})
            .sort([("created_at", -1)])
            .limit(10)
        )

        # Calculate success rate
        total_trades = broker.get("total_trades", 0)
        successful_trades = broker.get("successful_trades", 0)
        success_rate = (
            (successful_trades / total_trades * 100) if total_trades > 0 else 0
        )

        return {
            "broker": broker,
            "success_rate": round(success_rate, 1),
            "recent_ratings": recent_ratings,
            "total_earnings": broker.get("commission_rate", 0)
            * successful_trades,  # Estimated
        }

    @staticmethod
    def search_brokers(
        query: str = "", trade_type: str = None, min_rating: float = 0.0
    ) -> List[BrokerType]:
        """Search brokers with filters"""
        search_query = {
            "is_verified": True,
            "is_active": True,
            "rating": {"$gte": min_rating},
        }

        if query:
            search_query["$or"] = [
                {"broker_name": {"$regex": query, "$options": "i"}},
                {"bio": {"$regex": query, "$options": "i"}},
            ]

        if trade_type:
            search_query["specialties"] = {"$in": [trade_type]}

        brokers = list(
            db.brokers.find(search_query).sort([("rating", -1), ("total_trades", -1)])
        )

        return brokers

    @staticmethod
    def deactivate_broker(broker_id: str) -> bool:
        """Deactivate a broker"""
        try:
            result = db.brokers.update_one(
                {"_id": broker_id},
                {"$set": {"is_active": False, "updated_at": datetime.now()}},
            )

            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error deactivating broker: {e}")
            return False
