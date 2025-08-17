import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from config import *
from functions import *
from functions.trade import TradeClient
from functions.user import UserClient
from utils import *
from utils.enums import CallbackDataEnums, EmojiEnums
from utils.messages import Messages

logger = logging.getLogger(__name__)


async def send_message_or_edit(
    message, text, reply_markup, is_callback=False, parse_mode=None
):
    """Helper function to either send a new message or edit existing one"""
    try:
        if is_callback:
            return await message.edit_text(
                text, reply_markup=reply_markup, parse_mode=parse_mode
            )
        else:
            return await message.reply_text(
                text, reply_markup=reply_markup, parse_mode=parse_mode
            )
    except Exception as e:
        logger.error(f"Error in send_message_or_edit: {e}")
        raise


async def join_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /join command"""
    try:
        is_callback = bool(update.callback_query)
        message = update.callback_query.message if is_callback else update.message

        if is_callback:
            await update.callback_query.answer()

        await send_message_or_edit(
            message,
            f"{EmojiEnums.MAGNIFYING_GLASS.value} Please enter the Trade ID you want to join:",
            InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                            callback_data=CallbackDataEnums.MENU.value,
                        )
                    ]
                ]
            ),
            is_callback,
        )

        # Set state to wait for trade ID
        context.user_data["state"] = "waiting_for_trade_id"
        logger.info(
            f"Set state to waiting_for_trade_id for user {update.effective_user.id}"
        )
    except Exception as e:
        logger.error(f"Error in join handler: {e}")
        try:
            message = (
                update.callback_query.message
                if update.callback_query
                else update.message
            )
            if message:
                await send_message_or_edit(
                    message,
                    f"{EmojiEnums.CROSS_MARK.value} An error occurred. Please try again later.",
                    InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                                    callback_data=CallbackDataEnums.MENU.value,
                                )
                            ]
                        ]
                    ),
                    bool(update.callback_query),
                )
        except Exception as e2:
            logger.error(f"Error sending error message: {e2}")


async def handle_trade_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the trade ID input and buyer address input"""
    try:
        user_id = str(update.effective_user.id)
        
        # Check if this is buyer address input (after payment approval)
        try:
            awaiting_address_trade = db.trades.find_one({
                "buyer_id": user_id,
                "status": "awaiting_buyer_address", 
                "fiat_payment_approved": True
            })
            
            if awaiting_address_trade:
                logger.info(f"Processing buyer address input for user {user_id}")
                await handle_buyer_address_input(update, context)
                return
        except Exception as e:
            logger.warning(f"Could not check for awaiting address trade: {e}")
            # Continue with normal trade ID processing
        
        # Otherwise handle trade ID input
        if context.user_data.get("state") != "waiting_for_trade_id":
            logger.info(
                f"Ignoring message - state is not waiting_for_trade_id: {context.user_data.get('state')}"
            )
            return

        trade_id = update.message.text.strip()
        user_id = update.effective_user.id
        logger.info(f"Processing trade ID {trade_id} for user {user_id}")

        # Clear state
        context.user_data.pop("state", None)

        # Get trade details
        trade = TradeClient.get_trade(trade_id)
        if not trade:
            await update.message.reply_text(
                f"{EmojiEnums.CROSS_MARK.value} Trade not found. Please check the ID and try again.",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                                callback_data=CallbackDataEnums.MENU.value,
                            )
                        ]
                    ]
                ),
            )
            return

        # Check if trade is available for joining
        is_active = trade.get("is_active", False)
        status = str(trade.get("status", "")).lower()
        trade_type = trade.get("trade_type", "")

        # For CryptoToFiat trades, they become available after seller deposits (status="deposited")
        # For other trade types, check if they're in pending status
        if trade_type == "CryptoToFiat":
            if not is_active or status not in ["deposited", "pending"]:
                await update.message.reply_text(
                    f"{EmojiEnums.CROSS_MARK.value} This trade is no longer available for joining. The seller may not have deposited yet or the trade may be completed.",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                                    callback_data=CallbackDataEnums.MENU.value,
                                )
                            ]
                        ]
                    ),
                )
                return
        else:
            # For other trade types, use the original logic
            if status != "pending":
                await update.message.reply_text(
                    f"{EmojiEnums.CROSS_MARK.value} This trade is no longer available for joining (Status: {status}).",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                                    callback_data=CallbackDataEnums.MENU.value,
                                )
                            ]
                        ]
                    ),
                )
                return

        # Check if user is already involved in the trade
        seller_id = str(trade.get("seller_id", ""))
        buyer_id = str(trade.get("buyer_id", ""))

        # Check if trade already has a buyer
        if buyer_id and buyer_id != "":
            await update.message.reply_text(
                f"{EmojiEnums.CROSS_MARK.value} This trade already has a buyer and is no longer available.",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                                callback_data=CallbackDataEnums.MENU.value,
                            )
                        ]
                    ]
                ),
            )
            return

        if str(user_id) in [seller_id, buyer_id]:
            await update.message.reply_text(
                f"{EmojiEnums.CROSS_MARK.value} You are already involved in this trade.",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                                callback_data=CallbackDataEnums.MENU.value,
                            )
                        ]
                    ]
                ),
            )
            return

        # Store trade ID in context for later use
        context.user_data["join_trade_id"] = trade_id

        # Show detailed trade information for CryptoToFiat trades
        if trade_type == "CryptoToFiat":
            # Enhanced display with detailed payment information
            amount = str(trade.get("price", "0"))
            currency = str(trade.get("currency", "Unknown"))
            created_at = str(trade.get("created_at", "Unknown"))
            terms = str(trade.get("terms", ""))

            details = (
                f"💰 <b>Crypto → Fiat Trade Details</b>\n\n"
                f"🆔 <b>Trade ID:</b> <code>{trade_id}</code>\n"
                f"💎 <b>Crypto Amount:</b> {amount} {currency}\n"
                f"📅 <b>Created:</b> {created_at}\n"
                f"✅ <b>Status:</b> Seller has deposited crypto - Ready for buyer\n\n"
            )

            if terms:
                details += (
                    f"📋 <b>Payment Instructions from Seller:</b>\n<i>{terms}</i>\n\n"
                )

            details += (
                f"<b>🔄 How this trade works:</b>\n"
                f"1. You join as the buyer\n"
                f"2. You make the fiat payment to the seller as per their instructions\n"
                f"3. You submit proof of payment (screenshot/receipt)\n"
                f"4. Seller verifies your payment and releases the crypto\n"
                f"5. You receive {amount} {currency} in your wallet\n\n"
                f"<b>⚠️ Important:</b> The seller's crypto ({amount} {currency}) is already secured in escrow. "
                f"Only make the fiat payment after joining this trade.\n\n"
                f"Would you like to join this trade as a buyer?"
            )
        else:
            # Original simple display for other trade types
            amount = str(trade.get("price", "0"))
            currency = str(trade.get("currency", "Unknown"))
            created_at = str(trade.get("created_at", "Unknown"))
            terms = str(trade.get("terms", ""))

            details = (
                f"📋 <b>Trade Details</b>\n\n"
                f"ID: <code>{trade_id}</code>\n"
                f"Amount: {amount} {currency}\n"
                f"Created: {created_at}\n"
            )

            if terms:
                details += f"\nTerms: {terms}\n"

            details += "\nWould you like to join this trade as a buyer?"

        await update.message.reply_text(
            details,
            parse_mode="html",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            f"{EmojiEnums.CHECK_MARK.value} Yes, Join Trade",
                            callback_data=f"confirm_join_{trade_id}",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            f"{EmojiEnums.CROSS_MARK.value} No, Cancel",
                            callback_data=CallbackDataEnums.MENU.value,
                        )
                    ],
                ]
            ),
        )
    except Exception as e:
        logger.error(f"Error in handle_trade_id: {e}")
        await update.message.reply_text(
            f"{EmojiEnums.CROSS_MARK.value} An error occurred while processing the trade ID. Please try again later.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                            callback_data=CallbackDataEnums.MENU.value,
                        )
                    ]
                ]
            ),
        )


async def handle_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle join-related callback queries"""
    try:
        query = update.callback_query
        await query.answer()

        data = query.data
        logger.info(f"Processing join callback with data: {data}")

        if data.startswith("confirm_join_"):
            trade_id = data.replace("confirm_join_", "")
            user_id = query.from_user.id

            # Join the trade
            success = TradeClient.join_trade(trade_id, user_id)
            if success:
                # Get updated trade info
                trade = TradeClient.get_trade(trade_id)

                # Update trade status to "buyer_joined"
                TradeClient.update_trade_status(trade_id, "buyer_joined")

                # Notify seller if trade exists
                if trade and trade.get("seller_id"):
                    try:
                        await context.bot.send_message(
                            chat_id=trade["seller_id"],
                            text=f"{EmojiEnums.CHECK_MARK.value} <b>Buyer Joined Your Trade!</b>\n\n"
                            f"Trade ID: <code>{trade_id}</code>\n"
                            f"A buyer has joined and will now make the fiat payment as per your instructions.\n\n"
                            f"You will be notified when they submit proof of payment for verification.",
                            parse_mode="html",
                        )
                    except Exception as e:
                        logger.error(f"Failed to notify seller: {e}")

                # Enhanced confirmation message for buyer with detailed next steps
                trade_type = trade.get("trade_type", "")
                if trade_type == "CryptoToFiat":
                    confirmation_msg = (
                        f"{EmojiEnums.CHECK_MARK.value} <b>Successfully Joined Trade #{trade_id}!</b>\n\n"
                        f"💰 <b>You're buying:</b> {trade['price']} {trade['currency']}\n\n"
                        f"<b>📋 Next Steps:</b>\n"
                        f"1. Make the fiat payment exactly as described in the seller's terms\n"
                        f"2. Take a screenshot or photo of your payment confirmation\n"
                        f"3. Click 'Submit Payment Proof' below to upload your proof\n"
                        f"4. Wait for seller verification (usually within a few hours)\n"
                        f"5. Receive your crypto once payment is verified!\n\n"
                        f"<b>⚠️ Payment Instructions:</b>\n"
                        f"<i>{trade.get('terms', 'No specific terms provided')}</i>\n\n"
                        f"<b>🔒 Security:</b> The seller's crypto is safely held in escrow. "
                        f"You will only receive it after they verify your payment."
                    )

                    reply_markup = InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "📤 Submit Payment Proof",
                                    callback_data=f"submit_proof_{trade_id}",
                                )
                            ],
                            [
                                InlineKeyboardButton(
                                    "❓ Need Help?",
                                    callback_data=f"help_trade_{trade_id}",
                                )
                            ],
                            [
                                InlineKeyboardButton(
                                    f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                                    callback_data=CallbackDataEnums.MENU.value,
                                )
                            ],
                        ]
                    )
                else:
                    # Original message for other trade types
                    confirmation_msg = (
                        f"{EmojiEnums.CHECK_MARK.value} You have successfully joined trade #{trade_id}.\n\n"
                        "Please proceed with the payment to complete the trade."
                    )

                    reply_markup = InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "💳 Make Payment", callback_data=f"pay_{trade_id}"
                                )
                            ],
                            [
                                InlineKeyboardButton(
                                    f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                                    callback_data=CallbackDataEnums.MENU.value,
                                )
                            ],
                        ]
                    )

                await query.message.edit_text(
                    confirmation_msg, parse_mode="html", reply_markup=reply_markup
                )
            else:
                await query.message.edit_text(
                    f"{EmojiEnums.CROSS_MARK.value} Failed to join trade. The trade may no longer be available.",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                                    callback_data=CallbackDataEnums.MENU.value,
                                )
                            ]
                        ]
                    ),
                )
        elif data.startswith("submit_proof_"):
            # Handle fiat payment proof submission
            trade_id = data.replace("submit_proof_", "")
            user_id = query.from_user.id

            # Verify user is the buyer
            trade = TradeClient.get_trade(trade_id)
            if not trade or str(trade.get("buyer_id")) != str(user_id):
                await query.message.edit_text(
                    f"{EmojiEnums.CROSS_MARK.value} You are not authorized to submit proof for this trade.",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                                    callback_data=CallbackDataEnums.MENU.value,
                                )
                            ]
                        ]
                    ),
                )
                return

            # Check if proof already submitted
            if trade.get("fiat_payment_proof"):
                await query.message.edit_text(
                    f"{EmojiEnums.INFO.value} <b>Payment Proof Already Submitted</b>\n\n"
                    f"You have already submitted payment proof for trade #{trade_id}.\n"
                    f"The seller is reviewing your submission.\n\n"
                    f"Status: {trade.get('status', 'Unknown')}",
                    parse_mode="html",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                                    callback_data=CallbackDataEnums.MENU.value,
                                )
                            ]
                        ]
                    ),
                )
                return

            # Set state for photo upload
            context.user_data["awaiting_payment_proof"] = trade_id

            await query.message.edit_text(
                f"📤 <b>Submit Payment Proof for Trade #{trade_id}</b>\n\n"
                f"Please send a <b>photo or screenshot</b> of your payment confirmation.\n\n"
                f"<b>What to include:</b>\n"
                f"• Payment amount and recipient details\n"
                f"• Transaction reference/confirmation number\n"
                f"• Date and time of payment\n"
                f"• Your name/account details (if visible)\n\n"
                f"<b>Accepted formats:</b> JPG, PNG, PDF\n\n"
                f"📸 <i>Send your payment proof now...</i>",
                parse_mode="html",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "❌ Cancel", callback_data=CallbackDataEnums.MENU.value
                            )
                        ]
                    ]
                ),
            )
        elif data.startswith("pay_"):
            # Original pay logic for non-CryptoToFiat trades
            trade_id = data.replace("pay_", "")
            user_id = query.from_user.id

            trade = TradeClient.get_trade(trade_id)
            if not trade:
                await query.message.edit_text(
                    f"{EmojiEnums.CROSS_MARK.value} Trade not found.",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                                    callback_data=CallbackDataEnums.MENU.value,
                                )
                            ]
                        ]
                    ),
                )
                return

            # Ensure user is buyer
            if str(trade.get("buyer_id")) != str(user_id):
                await query.message.edit_text(
                    f"{EmojiEnums.CROSS_MARK.value} You are not authorized to confirm payment for this trade.",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                                    callback_data=CallbackDataEnums.MENU.value,
                                )
                            ]
                        ]
                    ),
                )
                return

            # Mark fiat payment in DB
            TradeClient.confirm_fiat_payment(trade_id)
            TradeClient.update_trade_status(trade_id, "fiat_paid")

            # Notify seller
            try:
                await context.bot.send_message(
                    chat_id=trade["seller_id"],
                    text=f"{EmojiEnums.MONEY_BAG.value} Buyer has confirmed fiat payment for trade #{trade_id}. Please verify and release crypto when ready.",
                    parse_mode="html",
                )
            except Exception as e:
                logger.error(f"Failed to notify seller about fiat payment: {e}")

            # Acknowledge buyer
            await query.message.edit_text(
                f"{EmojiEnums.CHECK_MARK.value} Payment marked as completed. The seller has been notified.",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                                callback_data=CallbackDataEnums.MENU.value,
                            )
                        ]
                    ]
                ),
            )
            
        elif data.startswith("payment_status_"):
            # Handle payment status check
            trade_id = data.replace("payment_status_", "")
            await handle_payment_status_callback(query, context, trade_id)
            
        elif data.startswith("help_address_"):
            # Handle address help request
            trade_id = data.replace("help_address_", "")
            await handle_address_help_callback(query, context, trade_id)
            
    except Exception as e:
        logger.error(f"Error in handle_join_callback: {e}")
        try:
            if query and query.message:
                await query.message.edit_text(
                    f"{EmojiEnums.CROSS_MARK.value} An error occurred while joining the trade. Please try again later.",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                                    callback_data=CallbackDataEnums.MENU.value,
                                )
                            ]
                        ]
                    ),
                )
        except Exception as e2:
            logger.error(f"Error sending error message: {e2}")


async def handle_payment_proof_upload(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handle payment proof photo/document upload"""
    try:
        trade_id = context.user_data.get("awaiting_payment_proof")
        if not trade_id:
            logger.info("Ignoring upload - not awaiting payment proof")
            return

        user_id = update.effective_user.id

        # Verify trade and user authorization
        trade = TradeClient.get_trade(trade_id)
        if not trade or str(trade.get("buyer_id")) != str(user_id):
            await update.message.reply_text(
                f"{EmojiEnums.CROSS_MARK.value} You are not authorized to submit proof for this trade.",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                                callback_data=CallbackDataEnums.MENU.value,
                            )
                        ]
                    ]
                ),
            )
            return

        # Get file information
        file_obj = None
        file_type = None

        if update.message.photo:
            # Handle photo upload
            file_obj = update.message.photo[-1]  # Get highest resolution
            file_type = "photo"
        elif update.message.document:
            # Handle document upload
            file_obj = update.message.document
            file_type = "document"

            # Check file type
            mime_type = file_obj.mime_type or ""
            if not any(allowed in mime_type.lower() for allowed in ["image", "pdf"]):
                await update.message.reply_text(
                    f"{EmojiEnums.CROSS_MARK.value} Invalid file type. Please send a photo (JPG, PNG) or PDF document.",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                                    callback_data=CallbackDataEnums.MENU.value,
                                )
                            ]
                        ]
                    ),
                )
                return
        else:
            await update.message.reply_text(
                f"{EmojiEnums.CROSS_MARK.value} Please send a photo or document as payment proof.",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                                callback_data=CallbackDataEnums.MENU.value,
                            )
                        ]
                    ]
                ),
            )
            return

        if not file_obj:
            await update.message.reply_text(
                f"{EmojiEnums.CROSS_MARK.value} Failed to process the uploaded file. Please try again.",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                                callback_data=CallbackDataEnums.MENU.value,
                            )
                        ]
                    ]
                ),
            )
            return

        # Get file details
        file_id = file_obj.file_id
        file_size = getattr(file_obj, "file_size", 0)

        # Check file size (limit to 10MB)
        if file_size > 10 * 1024 * 1024:
            await update.message.reply_text(
                f"{EmojiEnums.CROSS_MARK.value} File too large. Please upload a file smaller than 10MB.",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                                callback_data=CallbackDataEnums.MENU.value,
                            )
                        ]
                    ]
                ),
            )
            return

        # Store payment proof in database
        success = TradeClient.add_fiat_payment_proof(
            trade_id, file_id, file_type, user_id
        )

        if success:
            # Update trade status
            TradeClient.update_trade_status(trade_id, "proof_submitted")

            # Clear the awaiting state
            context.user_data.pop("awaiting_payment_proof", None)

            # Notify seller about proof submission
            try:
                await context.bot.send_message(
                    chat_id=trade["seller_id"],
                    text=(
                        f"📤 <b>Payment Proof Submitted</b>\n\n"
                        f"Trade ID: <code>{trade_id}</code>\n"
                        f"The buyer has submitted proof of fiat payment.\n\n"
                        f"Please review and verify the payment proof."
                    ),
                    parse_mode="html",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "🔍 Review Payment Proof",
                                    callback_data=f"review_proof_{trade_id}",
                                )
                            ],
                            [
                                InlineKeyboardButton(
                                    "✅ Approve & Release Crypto",
                                    callback_data=f"approve_payment_{trade_id}",
                                )
                            ],
                            [
                                InlineKeyboardButton(
                                    "❌ Reject Payment",
                                    callback_data=f"reject_payment_{trade_id}",
                                )
                            ],
                        ]
                    ),
                )
            except Exception as e:
                logger.error(f"Failed to notify seller about proof submission: {e}")

            # Confirm to buyer
            await update.message.reply_text(
                f"{EmojiEnums.CHECK_MARK.value} <b>Payment Proof Submitted!</b>\n\n"
                f"Trade ID: <code>{trade_id}</code>\n\n"
                f"Your payment proof has been successfully submitted and the seller has been notified.\n\n"
                f"<b>What happens next:</b>\n"
                f"• The seller will review your payment proof\n"
                f"• If approved, they will release the crypto to you\n"
                f"• You'll be notified of the decision\n\n"
                f"<b>Estimated review time:</b> Usually within a few hours\n\n"
                f"Thank you for using our escrow service!",
                parse_mode="html",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "📊 Check Trade Status",
                                callback_data=f"status_{trade_id}",
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                                callback_data=CallbackDataEnums.MENU.value,
                            )
                        ],
                    ]
                ),
            )
        else:
            await update.message.reply_text(
                f"{EmojiEnums.CROSS_MARK.value} Failed to submit payment proof. Please try again or contact support.",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                                callback_data=CallbackDataEnums.MENU.value,
                            )
                        ]
                    ]
                ),
            )
    except Exception as e:
        logger.error(f"Error in handle_payment_proof_upload: {e}")
        await update.message.reply_text(
            f"{EmojiEnums.CROSS_MARK.value} An error occurred while processing your payment proof. Please try again.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                            callback_data=CallbackDataEnums.MENU.value,
                        )
                    ]
                ]
            ),
        )


async def handle_buyer_address_input(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handle buyer address input for crypto release"""
    try:
        user_id = str(update.effective_user.id)
        address = update.message.text.strip()

        # Find trade awaiting buyer address for this user
        trade = db.trades.find_one(
            {
                "buyer_id": user_id,
                "status": "awaiting_buyer_address",
                "fiat_payment_approved": True,
            }
        )

        if not trade:
            logger.info(f"No trade awaiting address for user {user_id}")
            return

        trade_id = trade["_id"]
        currency = trade.get("currency", "")

        # Basic address validation
        if not address or len(address) < 20:
            await update.message.reply_text(
                f"{EmojiEnums.CROSS_MARK.value} Invalid address format. Please provide a valid {currency} address.",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "❓ Need Help?",
                                callback_data=f"help_address_{trade_id}",
                            ),
                            InlineKeyboardButton(
                                f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                                callback_data="menu",
                            ),
                        ]
                    ]
                ),
            )
            return

        # Additional validation based on currency
        if not _validate_crypto_address(address, currency):
            await update.message.reply_text(
                f"{EmojiEnums.CROSS_MARK.value} Invalid {currency} address format. Please check and try again.",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "❓ Need Help?",
                                callback_data=f"help_address_{trade_id}",
                            ),
                            InlineKeyboardButton(
                                f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                                callback_data="menu",
                            ),
                        ]
                    ]
                ),
            )
            return

        # Save buyer address
        success = TradeClient.set_buyer_address(trade_id, address)
        if not success:
            await update.message.reply_text(
                f"{EmojiEnums.CROSS_MARK.value} Failed to save your address. Please try again or contact support.",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                                callback_data="menu",
                            )
                        ]
                    ]
                ),
            )
            return

        # Calculate amounts
        original_amount = float(trade.get("price", 0))
        fee_amount, total_deposit_required = TradeClient.calculate_trade_fee(
            original_amount
        )

        # Show confirmation to buyer
        await update.message.reply_text(
            f"✅ <b>Address Confirmed!</b>\n\n"
            f"Trade ID: <code>{trade_id}</code>\n\n"
            f"📍 <b>Your {currency} address:</b>\n<code>{address}</code>\n\n"
            f"💰 <b>You will receive:</b> {original_amount} {currency}\n\n"
            f"🔄 <b>Initiating crypto release...</b>\n"
            f"Please wait while we transfer the crypto to your address.",
            parse_mode="html",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "📊 Check Payment Status",
                            callback_data=f"payment_status_{trade_id}",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                            callback_data="menu",
                        )
                    ]
                ]
            ),
        )

        # Initiate crypto release
        release_success = TradeClient.initiate_crypto_release(trade_id)

        if release_success:
            # Complete the trade
            TradeClient.complete_trade(trade_id)

            # Notify buyer of successful release
            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    f"🎉 <b>Crypto Released Successfully!</b>\n\n"
                    f"Trade ID: <code>{trade_id}</code>\n\n"
                    f"💰 <b>Transferred:</b> {original_amount} {currency}\n"
                    f"📍 <b>To address:</b> <code>{address}</code>\n\n"
                    f"The crypto has been successfully transferred to your address.\n"
                    f"You can check your wallet or blockchain explorer to confirm the transaction.\n\n"
                    f"Thank you for using our escrow service! 🚀"
                ),
                parse_mode="html",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "📊 Check Payment Status", 
                                callback_data=f"payment_status_{trade_id}"
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                "📈 Trade History", callback_data="trade_history"
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                                callback_data="menu",
                            )
                        ],
                    ]
                ),
            )

            # Notify seller of completion
            try:
                await context.bot.send_message(
                    chat_id=trade["seller_id"],
                    text=(
                        f"🎉 <b>Trade Completed Successfully!</b>\n\n"
                        f"Trade ID: <code>{trade_id}</code>\n\n"
                        f"💰 <b>Released to buyer:</b> {original_amount} {currency}\n"
                        f"📍 <b>Sent to:</b> <code>{address}</code>\n\n"
                        f"The crypto has been successfully transferred to the buyer.\n"
                        f"Trade completed! 🎉"
                    ),
                    parse_mode="html",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "📊 Trade History", callback_data="trade_history"
                                )
                            ],
                            [
                                InlineKeyboardButton(
                                    f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                                    callback_data="menu",
                                )
                            ],
                        ]
                    ),
                )
            except Exception as e:
                logger.error(f"Failed to notify seller of completion: {e}")
        else:
            # Crypto release failed
            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    f"❌ <b>Crypto Release Failed</b>\n\n"
                    f"Trade ID: <code>{trade_id}</code>\n\n"
                    f"There was an error releasing the crypto to your address.\n"
                    f"Our team has been notified and will resolve this issue.\n\n"
                    f"Please contact support with your trade ID for assistance."
                ),
                parse_mode="html",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "📞 Contact Support",
                                url=f"https://t.me/{SUPPORT_USERNAME}",
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                                callback_data="menu",
                            )
                        ],
                    ]
                ),
            )

            # Notify seller of issue
            try:
                await context.bot.send_message(
                    chat_id=trade["seller_id"],
                    text=(
                        f"⚠️ <b>Crypto Release Issue</b>\n\n"
                        f"Trade ID: <code>{trade_id}</code>\n\n"
                        f"There was an issue releasing the crypto to the buyer.\n"
                        f"Our team has been notified and will resolve this issue.\n\n"
                        f"You may be contacted for additional information."
                    ),
                    parse_mode="html",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                                    callback_data="menu",
                                )
                            ]
                        ]
                    ),
                )
            except Exception as e:
                logger.error(f"Failed to notify seller of release issue: {e}")

    except Exception as e:
        logger.error(f"Error in handle_buyer_address_input: {e}")
        await update.message.reply_text(
            f"{EmojiEnums.CROSS_MARK.value} An error occurred while processing your address. Please try again.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            f"{EmojiEnums.BACK_ARROW.value} Back to Menu",
                            callback_data="menu",
                        )
                    ]
                ]
            ),
        )


def _validate_crypto_address(address: str, currency: str) -> bool:
    """Basic crypto address validation"""
    try:
        currency = currency.upper()

        if currency == "BTC":
            # Bitcoin address validation (basic)
            return (
                len(address) >= 26
                and len(address) <= 35
                and (
                    address.startswith("1")
                    or address.startswith("3")
                    or address.startswith("bc1")
                )
            )
        elif currency == "ETH" or currency == "USDT":
            # Ethereum address validation (basic)
            return len(address) == 42 and address.startswith("0x")
        elif currency == "LTC":
            # Litecoin address validation (basic)
            return (
                len(address) >= 26
                and len(address) <= 35
                and (
                    address.startswith("L")
                    or address.startswith("M")
                    or address.startswith("ltc1")
                )
            )
        elif currency == "SOL":
            # Solana address validation (basic)
            return len(address) >= 32 and len(address) <= 44
        else:
            # Generic validation
            return len(address) >= 20

    except Exception as e:
        logger.error(f"Error validating address: {e}")
        return False


async def handle_payment_status_callback(query, context, trade_id):
    """Handle payment status check callback"""
    try:
        trade = TradeClient.get_trade(trade_id)
        if not trade:
            await query.message.edit_text(
                "❌ Trade not found.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]
                ])
            )
            return
            
        # Get transaction status
        currency = trade.get("currency", "")
        buyer_address = trade.get("buyer_address", "")
        amount = trade.get("price", 0)
        
        if buyer_address:
            # Payment has been sent
            status_message = (
                f"📊 <b>Payment Status</b>\n\n"
                f"Trade ID: <code>{trade_id}</code>\n"
                f"Currency: {currency}\n"
                f"Amount: {amount} {currency}\n"
                f"Your Address: <code>{buyer_address}</code>\n\n"
                f"✅ <b>Status:</b> Payment sent to your address\n"
                f"🔍 You can check the transaction on the blockchain explorer\n\n"
                f"💡 <b>Tip:</b> It may take a few minutes for the transaction to be confirmed on the network."
            )
        else:
            # Still waiting for address
            status_message = (
                f"📊 <b>Payment Status</b>\n\n"
                f"Trade ID: <code>{trade_id}</code>\n"
                f"Currency: {currency}\n"
                f"Amount: {amount} {currency}\n\n"
                f"⏳ <b>Status:</b> Waiting for your {currency} address\n"
                f"💬 Please send your {currency} address to receive the payment."
            )
            
        await query.message.edit_text(
            status_message,
            parse_mode="html",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Refresh Status", callback_data=f"payment_status_{trade_id}")],
                [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]
            ])
        )
        
    except Exception as e:
        logger.error(f"Error in payment status callback: {e}")
        await query.message.edit_text(
            "❌ Error checking payment status. Please try again.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]
            ])
        )


async def handle_address_help_callback(query, context, trade_id):
    """Handle address help callback"""
    try:
        trade = TradeClient.get_trade(trade_id)
        if not trade:
            await query.message.edit_text(
                "❌ Trade not found.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]
                ])
            )
            return
            
        currency = trade.get("currency", "")
        
        help_messages = {
            "USDT": (
                f"🔰 <b>USDT Address Help</b>\n\n"
                f"USDT can run on different networks:\n"
                f"• <b>ERC-20 (Ethereum):</b> Starts with 0x...\n"
                f"• <b>TRC-20 (Tron):</b> Starts with T...\n"
                f"• <b>BSC (BEP-20):</b> Starts with 0x...\n\n"
                f"⚠️ <b>Important:</b> Make sure you provide an address that matches the network the seller is using!\n\n"
                f"📱 <b>Where to find your address:</b>\n"
                f"• Open your wallet app (MetaMask, Trust Wallet, etc.)\n"
                f"• Select USDT\n"
                f"• Tap 'Receive' or 'Copy Address'\n\n"
                f"💡 <b>Example addresses:</b>\n"
                f"• Ethereum: 0x742d35cc6e3f4dc5bf5b123456789abcdef123456\n"
                f"• Tron: TQn9Y2khEsLJW1ChVWFMSMeRDow5KcbLSE"
            ),
            "ETH": (
                f"🔰 <b>ETH Address Help</b>\n\n"
                f"Ethereum addresses:\n"
                f"• Start with 0x...\n"
                f"• Are 42 characters long\n"
                f"• Contain numbers (0-9) and letters (a-f)\n\n"
                f"📱 <b>Where to find your address:</b>\n"
                f"• Open your wallet app (MetaMask, Coinbase Wallet, etc.)\n"
                f"• Tap 'Receive' or your account name\n"
                f"• Copy the address\n\n"
                f"💡 <b>Example:</b>\n"
                f"0x742d35cc6e3f4dc5bf5b123456789abcdef123456"
            ),
            "BTC": (
                f"🔰 <b>BTC Address Help</b>\n\n"
                f"Bitcoin addresses can start with:\n"
                f"• <b>1...</b> (Legacy format)\n"
                f"• <b>3...</b> (Script format) \n"
                f"• <b>bc1...</b> (Bech32 format)\n\n"
                f"📱 <b>Where to find your address:</b>\n"
                f"• Open your Bitcoin wallet\n"
                f"• Tap 'Receive'\n"
                f"• Copy the address\n\n"
                f"💡 <b>Examples:</b>\n"
                f"• 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa\n"
                f"• bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4"
            )
        }
        
        help_message = help_messages.get(currency, 
            f"🔰 <b>{currency} Address Help</b>\n\n"
            f"Please provide a valid {currency} address where you want to receive your crypto.\n\n"
            f"📱 <b>Where to find your address:</b>\n"
            f"• Open your {currency} wallet\n"
            f"• Look for 'Receive' or 'Deposit'\n"
            f"• Copy the address\n\n"
            f"⚠️ <b>Important:</b> Double-check the address before sending!"
        )
        
        await query.message.edit_text(
            help_message,
            parse_mode="html",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💬 Send Address Now", callback_data="menu")],
                [InlineKeyboardButton("🔙 Back", callback_data=f"payment_status_{trade_id}")]
            ])
        )
        
    except Exception as e:
        logger.error(f"Error in address help callback: {e}")
        await query.message.edit_text(
            "❌ Error loading help information. Please try again.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]
            ])
        )


def register_handlers(application):
    """Register handlers for the join module"""
    application.add_handler(CommandHandler("join", join_handler))
    # Handle text messages for trade ID input, buyer address input, and rejection reasons
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, handle_trade_id
        ),
        group=1  # Higher priority than trade flow dispatch
    )
    # Handle photo uploads for payment proof
    application.add_handler(
        MessageHandler(
            filters.PHOTO & filters.ChatType.PRIVATE, handle_payment_proof_upload
        )
    )
    # Handle document uploads for payment proof
    application.add_handler(
        MessageHandler(
            filters.Document.ALL & filters.ChatType.PRIVATE, handle_payment_proof_upload
        )
    )
    # Handle join-related callbacks
    application.add_handler(
        CallbackQueryHandler(
            handle_join_callback,
            pattern="^(confirm_join_|pay_|submit_proof_|help_trade_|payment_status_|help_address_)",
        )
    )
    # Note: buyer address input is now handled within handle_trade_id based on state
