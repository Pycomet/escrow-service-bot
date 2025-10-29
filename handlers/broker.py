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
        from config import db

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


# ========== BROKER-INITIATED TRADE HANDLERS ==========


async def broker_create_trade_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handle /broker_create_trade command"""
    user_id = str(update.effective_user.id)

    # Check if user is a verified broker
    broker = BrokerClient.get_broker(user_id)
    if not broker or not broker.get("is_verified") or not broker.get("is_active"):
        await update.message.reply_text(
            "❌ Only verified brokers can create broker-initiated trades.\n\n"
            "Use /broker to register as a broker.",
            parse_mode="HTML",
        )
        return

    # Show introduction and start trade creation
    from utils.keyboard import broker_trade_creation_menu
    from utils.messages import Messages

    await update.message.reply_text(
        Messages.broker_trade_creation_start(),
        parse_mode="HTML",
        reply_markup=broker_trade_creation_menu(),
    )


async def broker_trade_message_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handle text input during broker trade creation flow"""
    broker_trade_data = context.user_data.get("broker_trade_creation")
    if not broker_trade_data:
        return

    step = broker_trade_data.get("step")
    user_id = str(update.effective_user.id)
    text = update.message.text.strip()

    # Validate broker is still verified
    broker = BrokerClient.get_broker(user_id)
    if not broker or not broker.get("is_verified") or not broker.get("is_active"):
        context.user_data.pop("broker_trade_creation", None)
        await update.message.reply_text(
            "❌ Broker verification lost. Please contact admin.",
            parse_mode="HTML",
        )
        return

    from utils.keyboard import broker_trade_step_cancel_menu
    from utils.messages import Messages

    try:
        if step == "crypto_amount":
            # Parse crypto amount
            try:
                amount = float(text)
                if amount <= 0:
                    raise ValueError("Amount must be positive")
                broker_trade_data["crypto_amount"] = amount
                broker_trade_data["step"] = "seller_rate"
                await update.message.reply_text(
                    Messages.broker_trade_ask_seller_rate(),
                    parse_mode="HTML",
                    reply_markup=broker_trade_step_cancel_menu(),
                )
            except ValueError:
                await update.message.reply_text(
                    "❌ Invalid amount. Please enter a positive number:",
                    reply_markup=broker_trade_step_cancel_menu(),
                )

        elif step == "seller_rate":
            # Parse seller rate
            try:
                rate = float(text)
                if rate <= 0:
                    raise ValueError("Rate must be positive")
                broker_trade_data["seller_rate"] = rate
                broker_trade_data["step"] = "buyer_rate"
                await update.message.reply_text(
                    Messages.broker_trade_ask_buyer_rate(rate),
                    parse_mode="HTML",
                    reply_markup=broker_trade_step_cancel_menu(),
                )
            except ValueError:
                await update.message.reply_text(
                    "❌ Invalid rate. Please enter a positive number:",
                    reply_markup=broker_trade_step_cancel_menu(),
                )

        elif step == "buyer_rate":
            # Parse buyer rate
            try:
                rate = float(text)
                seller_rate = broker_trade_data.get("seller_rate")
                if rate <= seller_rate:
                    await update.message.reply_text(
                        f"❌ Buyer rate ({rate}) must be HIGHER than seller rate ({seller_rate}).\n"
                        "Please try again:",
                        reply_markup=broker_trade_step_cancel_menu(),
                    )
                    return
                broker_trade_data["buyer_rate"] = rate
                broker_trade_data["step"] = "market_rate"
                await update.message.reply_text(
                    Messages.broker_trade_ask_market_rate(),
                    parse_mode="HTML",
                    reply_markup=broker_trade_step_cancel_menu(),
                )
            except ValueError:
                await update.message.reply_text(
                    "❌ Invalid rate. Please enter a positive number:",
                    reply_markup=broker_trade_step_cancel_menu(),
                )

        elif step == "market_rate":
            # Parse market rate
            try:
                rate = float(text)
                if rate <= 0:
                    raise ValueError("Rate must be positive")
                broker_trade_data["market_rate"] = rate
                broker_trade_data["step"] = "seller_instructions"
                await update.message.reply_text(
                    Messages.broker_trade_ask_seller_instructions(),
                    parse_mode="HTML",
                    reply_markup=broker_trade_step_cancel_menu(),
                )
            except ValueError:
                await update.message.reply_text(
                    "❌ Invalid rate. Please enter a positive number:",
                    reply_markup=broker_trade_step_cancel_menu(),
                )

        elif step == "seller_instructions":
            # Handle /skip command
            if text.lower() == "/skip":
                broker_trade_data["seller_instructions"] = ""
            else:
                broker_trade_data["seller_instructions"] = text
            broker_trade_data["step"] = "buyer_instructions"
            await update.message.reply_text(
                Messages.broker_trade_ask_buyer_instructions(),
                parse_mode="HTML",
                reply_markup=broker_trade_step_cancel_menu(),
            )

        elif step == "buyer_instructions":
            # Handle /skip command
            if text.lower() == "/skip":
                broker_trade_data["buyer_instructions"] = ""
            else:
                broker_trade_data["buyer_instructions"] = text

            # Show preview
            await show_broker_trade_preview(update, context, broker_trade_data)

    except Exception as e:
        logger.error(f"Error in broker trade message handler: {e}")
        await update.message.reply_text(
            f"❌ An error occurred: {str(e)}\n\nPlease try again or /cancel",
            parse_mode="HTML",
        )


async def show_broker_trade_preview(update, context, broker_trade_data):
    """Show preview of broker trade before creation"""
    from config import BOT_FEE_PERCENTAGE
    from functions.trade import TradeClient
    from utils.keyboard import broker_trade_preview_menu
    from utils.messages import Messages

    # Calculate profit breakdown
    profit_data = TradeClient._calculate_broker_profit(
        crypto_amount=broker_trade_data["crypto_amount"],
        seller_rate=broker_trade_data["seller_rate"],
        buyer_rate=broker_trade_data["buyer_rate"],
        market_rate=broker_trade_data["market_rate"],
        bot_fee_percentage=BOT_FEE_PERCENTAGE,
    )

    # Build summary for preview
    summary = {
        "crypto_amount": broker_trade_data["crypto_amount"],
        "crypto_currency": broker_trade_data["crypto_currency"],
        "seller_rate": broker_trade_data["seller_rate"],
        "buyer_rate": broker_trade_data["buyer_rate"],
        "market_rate": broker_trade_data["market_rate"],
        "fiat_currency": broker_trade_data["fiat_currency"],
        "payment_method": broker_trade_data["payment_method"],
        "seller_receives_fiat": profit_data["seller_receives_fiat"],
        "buyer_pays_fiat": profit_data["buyer_pays_fiat"],
        "broker_profit_fiat": profit_data["broker_profit_fiat"],
        "broker_profit_crypto": profit_data["broker_profit_crypto"],
        "bot_fee_crypto": profit_data["bot_fee_crypto"],
        "buyer_receive_amount": profit_data["buyer_receive_amount"],
        "seller_instructions": broker_trade_data.get("seller_instructions", ""),
        "buyer_instructions": broker_trade_data.get("buyer_instructions", ""),
    }

    # Store summary for finalization
    broker_trade_data["preview_summary"] = summary

    await update.message.reply_text(
        Messages.broker_trade_preview(summary),
        parse_mode="HTML",
        reply_markup=broker_trade_preview_menu(),
    )


async def finalize_broker_trade_creation(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Finalize and create the broker-initiated trade"""
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)
    broker_trade_data = context.user_data.get("broker_trade_creation")

    if not broker_trade_data:
        await query.edit_message_text("❌ Trade creation data not found.")
        return

    try:
        # Create the trade
        trade = TradeClient.create_broker_initiated_trade(
            broker_id=user_id,
            crypto_amount=broker_trade_data["crypto_amount"],
            crypto_currency=broker_trade_data["crypto_currency"],
            seller_rate=broker_trade_data["seller_rate"],
            buyer_rate=broker_trade_data["buyer_rate"],
            market_rate=broker_trade_data["market_rate"],
            fiat_currency=broker_trade_data["fiat_currency"],
            payment_method=broker_trade_data["payment_method"],
            seller_instructions=broker_trade_data.get("seller_instructions", ""),
            buyer_instructions=broker_trade_data.get("buyer_instructions", ""),
        )

        # Clear user data
        context.user_data.pop("broker_trade_creation", None)

        # Send success notification
        from utils.messages import Messages

        summary = broker_trade_data["preview_summary"]
        await query.edit_message_text(
            Messages.broker_trade_created_notification(trade["_id"], summary),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]]
            ),
        )

        logger.info(f"Broker {user_id} created broker-initiated trade {trade['_id']}")

    except ValueError as e:
        await query.edit_message_text(
            f"❌ <b>Trade Creation Failed</b>\n\n{str(e)}\n\n"
            "Please try again or contact support.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🔄 Try Again", callback_data="broker_create_trade_start"
                        )
                    ],
                    [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")],
                ]
            ),
        )
    except Exception as e:
        logger.error(f"Error creating broker-initiated trade: {e}")
        await query.edit_message_text(
            f"❌ <b>Error Creating Trade</b>\n\n"
            "An unexpected error occurred. Please try again later.",
            parse_mode="HTML",
        )


async def broker_trade_callback_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handle callback queries for broker trade creation"""
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = str(query.from_user.id)

    from utils.keyboard import (
        broker_trade_currency_selection,
        broker_trade_fiat_currency_selection,
        broker_trade_payment_method_menu,
        broker_trade_step_cancel_menu,
    )
    from utils.messages import Messages

    if data == "broker_create_trade_start":
        # Validate broker
        broker = BrokerClient.get_broker(user_id)
        if not broker or not broker.get("is_verified") or not broker.get("is_active"):
            await query.edit_message_text(
                "❌ Only verified brokers can create trades.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔙 Back", callback_data="menu")]]
                ),
            )
            return

        # Initialize broker trade creation flow
        context.user_data["broker_trade_creation"] = {"step": "crypto_currency"}

        await query.edit_message_text(
            "💰 <b>Select Cryptocurrency</b>\n\n"
            "Which cryptocurrency will be used in this trade?",
            parse_mode="HTML",
            reply_markup=broker_trade_currency_selection(),
        )

    elif data.startswith("broker_trade_currency_"):
        crypto_currency = data.replace("broker_trade_currency_", "")
        broker_trade_data = context.user_data.get("broker_trade_creation", {})
        broker_trade_data["crypto_currency"] = crypto_currency
        broker_trade_data["step"] = "fiat_currency"
        context.user_data["broker_trade_creation"] = broker_trade_data

        await query.edit_message_text(
            "💵 <b>Select Fiat Currency</b>\n\n"
            "Which fiat currency will be used for payment?",
            parse_mode="HTML",
            reply_markup=broker_trade_fiat_currency_selection(),
        )

    elif data.startswith("broker_trade_fiat_"):
        fiat_currency = data.replace("broker_trade_fiat_", "")
        broker_trade_data = context.user_data.get("broker_trade_creation", {})
        broker_trade_data["fiat_currency"] = fiat_currency
        broker_trade_data["step"] = "payment_method"
        context.user_data["broker_trade_creation"] = broker_trade_data

        await query.edit_message_text(
            "💳 <b>Select Payment Method</b>\n\n" "How will the fiat payment be made?",
            parse_mode="HTML",
            reply_markup=broker_trade_payment_method_menu(),
        )

    elif data.startswith("broker_trade_payment_"):
        payment_method = data.replace("broker_trade_payment_", "")
        broker_trade_data = context.user_data.get("broker_trade_creation", {})
        broker_trade_data["payment_method"] = payment_method
        broker_trade_data["step"] = "crypto_amount"
        context.user_data["broker_trade_creation"] = broker_trade_data

        await query.edit_message_text(
            Messages.broker_trade_ask_crypto_amount(),
            parse_mode="HTML",
            reply_markup=broker_trade_step_cancel_menu(),
        )

    elif data == "broker_trade_confirm_create":
        await finalize_broker_trade_creation(update, context)

    elif data == "broker_create_trade_cancel":
        context.user_data.pop("broker_trade_creation", None)
        await query.edit_message_text(
            "❌ Broker trade creation cancelled.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]]
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
    application.add_handler(
        CommandHandler("broker_create_trade", broker_create_trade_handler)
    )

    # Message handler for broker registration and trade creation
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE,
            broker_message_handler,
        ),
        group=2,  # Higher priority than trade flow dispatch
    )

    # Additional message handler for broker trade creation (same group)
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE,
            broker_trade_message_handler,
        ),
        group=2,
    )

    # Callback handlers for broker operations
    application.add_handler(
        CallbackQueryHandler(
            broker_callback_handler,
            pattern="^(cancel_broker_registration|skip_broker_bio|broker_my_trades|broker_settings|verify_broker_|reject_broker_)",
        )
    )

    # Callback handlers for broker trade creation
    application.add_handler(
        CallbackQueryHandler(
            broker_trade_callback_handler,
            pattern="^(broker_create_trade_|broker_trade_)",
        )
    )
