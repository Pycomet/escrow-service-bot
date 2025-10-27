import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from config import ADMIN_ID
from functions.broker import BrokerClient
from functions.trade import TradeClient
from functions.user import UserClient
from utils.enums import EmojiEnums

logger = logging.getLogger(__name__)


async def broker_registration_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handle broker registration command"""
    user_id = str(update.effective_user.id)

    # Check if user is already a broker
    existing_broker = BrokerClient.get_broker(user_id)
    if existing_broker:
        if existing_broker.get("is_verified"):
            status = (
                "✅ Verified & Active"
                if existing_broker.get("is_active")
                else "⏸️ Verified but Inactive"
            )
        else:
            status = "⏳ Pending Verification"

        stats = BrokerClient.get_broker_stats(existing_broker["_id"])

        await update.message.reply_text(
            f"🤝 <b>Your Broker Profile</b>\n\n"
            f"📛 <b>Name:</b> {existing_broker['broker_name']}\n"
            f"📊 <b>Status:</b> {status}\n"
            f"💰 <b>Commission Rate:</b> {existing_broker.get('commission_rate', 0)}%\n"
            f"⭐ <b>Rating:</b> {existing_broker.get('rating', 0)}/5\n"
            f"📈 <b>Total Trades:</b> {existing_broker.get('total_trades', 0)}\n"
            f"✅ <b>Successful:</b> {existing_broker.get('successful_trades', 0)}\n"
            f"📊 <b>Success Rate:</b> {stats.get('success_rate', 0)}%\n"
            f"🎯 <b>Specialties:</b> {', '.join(existing_broker.get('specialties', []))}\n\n"
            f"📝 <b>Bio:</b> <i>{existing_broker.get('bio', 'No bio set')}</i>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "📊 View My Trades", callback_data="broker_my_trades"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "⚙️ Broker Settings", callback_data="broker_settings"
                        )
                    ],
                    [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")],
                ]
            ),
        )
        return

    # Start broker registration
    context.user_data["broker_registration"] = {"step": "name"}

    await update.message.reply_text(
        f"🤝 <b>Become a Broker</b>\n\n"
        f"Welcome to the broker program! As a verified broker, you can:\n\n"
        f"✅ Mediate trades between buyers and sellers\n"
        f"💰 Earn commission on successful trades\n"
        f"🛡️ Help resolve disputes and build trust\n"
        f"📈 Build your reputation in the community\n\n"
        f"<b>Requirements:</b>\n"
        f"• Clean trading history\n"
        f"• Understanding of crypto/fiat markets\n"
        f"• Commitment to fair mediation\n"
        f"• Admin verification required\n\n"
        f"<b>First, what would you like your broker name to be?</b>\n"
        f"<i>(This is how traders will see you)</i>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "❌ Cancel Registration",
                        callback_data="cancel_broker_registration",
                    )
                ]
            ]
        ),
    )


async def broker_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle broker registration text input"""
    registration_data = context.user_data.get("broker_registration")
    if not registration_data:
        return

    step = registration_data.get("step")
    user_id = str(update.effective_user.id)

    if step == "name":
        broker_name = update.message.text.strip()

        if len(broker_name) < 3 or len(broker_name) > 50:
            await update.message.reply_text(
                "❌ Broker name must be between 3 and 50 characters. Please try again:",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "❌ Cancel Registration",
                                callback_data="cancel_broker_registration",
                            )
                        ]
                    ]
                ),
            )
            return

        registration_data["broker_name"] = broker_name
        registration_data["step"] = "bio"

        await update.message.reply_text(
            f"✅ Great! Your broker name will be: <b>{broker_name}</b>\n\n"
            f"Now, please provide a brief bio describing your experience and approach to mediation.\n\n"
            f'<b>Example:</b> <i>"Experienced crypto trader with 3+ years in DeFi. I focus on clear communication and fair resolution of disputes. Available 12+ hours daily for trade support."</i>\n\n'
            f"What's your bio?",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "⏭️ Skip Bio", callback_data="skip_broker_bio"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "❌ Cancel Registration",
                            callback_data="cancel_broker_registration",
                        )
                    ],
                ]
            ),
        )

    elif step == "bio":
        bio = update.message.text.strip()

        if len(bio) > 500:
            await update.message.reply_text(
                "❌ Bio is too long (max 500 characters). Please shorten it:",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "⏭️ Skip Bio", callback_data="skip_broker_bio"
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                "❌ Cancel Registration",
                                callback_data="cancel_broker_registration",
                            )
                        ],
                    ]
                ),
            )
            return

        registration_data["bio"] = bio
        await complete_broker_registration(update, context, registration_data)


async def complete_broker_registration(update, context, registration_data):
    """Complete the broker registration process"""
    user_id = str(update.effective_user.id)
    broker_name = registration_data["broker_name"]
    bio = registration_data.get("bio", "")

    # Register the broker
    broker = BrokerClient.register_broker(
        user_id=user_id,
        broker_name=broker_name,
        bio=bio,
        specialties=["CryptoToFiat"],  # Default specialization
    )

    if broker:
        # Clear registration data
        context.user_data.pop("broker_registration", None)

        # Notify admin about new broker registration
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    f"🤝 <b>New Broker Registration</b>\n\n"
                    f"📛 <b>Name:</b> {broker_name}\n"
                    f"👤 <b>User ID:</b> {user_id}\n"
                    f"📝 <b>Bio:</b> {bio}\n\n"
                    f"Please review and verify this broker if they meet the requirements."
                ),
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "✅ Verify Broker",
                                callback_data=f"verify_broker_{broker['_id']}",
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                "❌ Reject Application",
                                callback_data=f"reject_broker_{broker['_id']}",
                            )
                        ],
                    ]
                ),
            )
        except Exception as e:
            logger.error(f"Failed to notify admin about broker registration: {e}")

        await update.message.reply_text(
            f"🎉 <b>Broker Application Submitted!</b>\n\n"
            f"📛 <b>Name:</b> {broker_name}\n"
            f"📝 <b>Bio:</b> {bio}\n\n"
            f"Your application has been submitted to the admin for review.\n\n"
            f"✅ You'll be notified once your application is approved\n"
            f"💰 Default commission rate: 1.0% (adjustable after verification)\n"
            f"🎯 Default specialization: Crypto-to-Fiat trades\n\n"
            f"Thank you for your interest in becoming a broker!",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]]
            ),
        )
    else:
        await update.message.reply_text(
            f"❌ <b>Registration Failed</b>\n\n"
            f"There was an error processing your broker application. Please try again later or contact support.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🔄 Try Again", callback_data="/broker_register"
                        )
                    ],
                    [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")],
                ]
            ),
        )


async def broker_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle broker-related callback queries"""
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = str(query.from_user.id)

    if data == "cancel_broker_registration":
        context.user_data.pop("broker_registration", None)
        await query.edit_message_text(
            "❌ Broker registration cancelled.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]]
            ),
        )

    elif data == "skip_broker_bio":
        registration_data = context.user_data.get("broker_registration", {})
        registration_data["bio"] = ""
        await complete_broker_registration(query, context, registration_data)

    elif data == "broker_my_trades":
        # Show trades where user is the broker
        brokered_trades = list(db.trades.find({"broker_id": user_id}))

        if not brokered_trades:
            await query.edit_message_text(
                "📊 <b>Your Brokered Trades</b>\n\n"
                "You haven't mediated any trades yet.\n"
                "Trades will appear here once you're assigned as a broker.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔙 Back", callback_data="/broker_register")]]
                ),
            )
            return

        trades_text = "📊 <b>Your Brokered Trades</b>\n\n"
        for trade in brokered_trades[-5:]:  # Show last 5 trades
            status = trade.get("status", "Unknown")
            amount = trade.get("price", 0)
            currency = trade.get("currency", "")

            trades_text += (
                f"🔸 Trade {trade['_id'][:8]}... - {amount} {currency} ({status})\n"
            )

        await query.edit_message_text(
            trades_text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Back", callback_data="/broker_register")]]
            ),
        )

    elif data == "broker_settings":
        broker = BrokerClient.get_broker(user_id)
        if not broker:
            await query.edit_message_text("❌ Broker profile not found.")
            return

        await query.edit_message_text(
            f"⚙️ <b>Broker Settings</b>\n\n"
            f"📛 <b>Name:</b> {broker['broker_name']}\n"
            f"💰 <b>Commission:</b> {broker.get('commission_rate', 0)}%\n"
            f"🎯 <b>Specialties:</b> {', '.join(broker.get('specialties', []))}\n\n"
            f"Contact admin to modify your settings.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Back", callback_data="/broker_register")]]
            ),
        )

    # Admin broker verification callbacks
    elif data.startswith("verify_broker_") and user_id == str(ADMIN_ID):
        broker_id = data.replace("verify_broker_", "")
        success = BrokerClient.verify_broker(broker_id, user_id)

        if success:
            broker = BrokerClient.get_broker_by_id(broker_id)

            # Notify the broker
            try:
                await context.bot.send_message(
                    chat_id=broker["user_id"],
                    text=(
                        f"🎉 <b>Broker Application Approved!</b>\n\n"
                        f"Congratulations! You are now a verified broker.\n\n"
                        f"📛 <b>Name:</b> {broker['broker_name']}\n"
                        f"💰 <b>Commission Rate:</b> {broker.get('commission_rate', 1.0)}%\n"
                        f"🎯 <b>Specialties:</b> {', '.join(broker.get('specialties', []))}\n\n"
                        f"You can now mediate trades and earn commissions!\n"
                        f"Use /broker to manage your broker profile."
                    ),
                    parse_mode="HTML",
                )
            except Exception as e:
                logger.error(f"Failed to notify broker of verification: {e}")

            await query.edit_message_text(
                f"✅ Broker {broker['broker_name']} has been verified and activated.",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "🔙 Back to Admin", callback_data="admin_menu"
                            )
                        ]
                    ]
                ),
            )
        else:
            await query.edit_message_text("❌ Failed to verify broker.")

    elif data.startswith("reject_broker_") and user_id == str(ADMIN_ID):
        broker_id = data.replace("reject_broker_", "")
        broker = BrokerClient.get_broker_by_id(broker_id)

        if broker:
            # Notify the broker
            try:
                await context.bot.send_message(
                    chat_id=broker["user_id"],
                    text=(
                        f"❌ <b>Broker Application Rejected</b>\n\n"
                        f"Unfortunately, your broker application has not been approved at this time.\n\n"
                        f"This could be due to:\n"
                        f"• Insufficient trading experience\n"
                        f"• Application incomplete\n"
                        f"• Current broker capacity\n\n"
                        f"You may reapply in the future. Contact support for feedback."
                    ),
                    parse_mode="HTML",
                )
            except Exception as e:
                logger.error(f"Failed to notify broker of rejection: {e}")

            # Deactivate the broker
            BrokerClient.deactivate_broker(broker_id)

            await query.edit_message_text(
                f"❌ Broker application for {broker['broker_name']} has been rejected.",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "🔙 Back to Admin", callback_data="admin_menu"
                            )
                        ]
                    ]
                ),
            )


def register_broker_handlers(application):
    """Register broker-related handlers"""
    from telegram.ext import (
        CallbackQueryHandler,
        CommandHandler,
        MessageHandler,
        filters,
    )

    # Command handlers
    application.add_handler(CommandHandler("broker", broker_registration_handler))

    # Message handler for broker registration
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE,
            broker_message_handler,
        ),
        group=2,  # Higher priority than trade flow dispatch
    )

    # Callback handlers for broker operations
    application.add_handler(
        CallbackQueryHandler(
            broker_callback_handler,
            pattern="^(cancel_broker_registration|skip_broker_bio|broker_my_trades|broker_settings|verify_broker_|reject_broker_)",
        )
    )
