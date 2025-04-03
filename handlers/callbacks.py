from config import *
# from handlers.initiate_trade import *
from handlers import *
from utils import *
from functions import *
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackQueryHandler, ContextTypes
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Callback Handlers
async def handle_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle menu-related callback queries"""
    try:
        query = update.callback_query
        await query.answer()
        
        data = query.data
        logger.info(f"Received callback data: {data}")
        
        if data == "menu":
            # Show main menu
            await query.edit_message_text(
                "🤖 <b>Welcome to the Escrow Service Bot!</b>\n\n"
                "What would you like to do?",
                parse_mode="html",
                reply_markup=await main_menu(update, context)
            )
        
        elif data == "create_trade":
            # Start trade creation process
            logger.info("Starting trade creation process")
            await initiate_trade_handler(update, context)
        
        elif data == "join_trade":
            # Start trade joining process
            logger.info("Starting trade joining process")
            await join_handler(update, context)
        
        elif data == "trade_history":
            # Show trade history
            logger.info("Showing trade history")
            await history_handler(update, context)
        
        elif data == "rules":
            # Show rules
            logger.info("Showing rules")
            await rules_handler(update, context)
        
        elif data == "community":
            # Show community links
            logger.info("Showing community links")
            await community_handler(update, context)
        
        elif data == "affiliate":
            # Show affiliate program
            logger.info("Showing affiliate program")
            await affiliate_handler(update, context)
        
        elif data == "support":
            # Show support options
            logger.info("Showing support options")
            await query.edit_message_text(
                "🆘 <b>Need Help?</b>\n\n"
                "We're here to help! Choose an option below:",
                parse_mode="html",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📝 Report an Issue", callback_data="report")],
                    [InlineKeyboardButton("❓ FAQ", callback_data="faq")],
                    [InlineKeyboardButton("📞 Contact Support", url=f"https://t.me/{SUPPORT_USERNAME}")],
                    [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]
                ])
            )
        
        elif data == "report":
            # Start report process
            logger.info("Starting report process")
            await report_handler(update, context)
        
        elif data == "faq":
            # Show FAQ
            logger.info("Showing FAQ")
            await query.edit_message_text(
                "❓ <b>Frequently Asked Questions</b>\n\n"
                "1. <b>How does the escrow service work?</b>\n"
                "The escrow service holds the buyer's payment until the goods/services are delivered and approved.\n\n"
                "2. <b>What happens if there's a dispute?</b>\n"
                "Both parties can submit evidence, and our team will review the case fairly.\n\n"
                "3. <b>How long does a trade take?</b>\n"
                "Most trades are completed within 24-48 hours, depending on delivery time.\n\n"
                "4. <b>What are the fees?</b>\n"
                "Fees are clearly displayed before creating a trade.\n\n"
                "5. <b>Is my payment secure?</b>\n"
                "Yes, all payments are held securely in escrow until the trade is completed.",
                parse_mode="html",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Support", callback_data="support")
                ]])
            )
        
    except Exception as e:
        logger.error(f"Error in menu callback: {e}")
        try:
            await query.edit_message_text(
                "❌ An error occurred. Please try again or contact support.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
                ]])
            )
        except Exception:
            pass

def register_handlers(application):
    """Register handlers for the callbacks module"""
    application.add_handler(CallbackQueryHandler(handle_menu_callback, pattern="^(menu|create_trade|join_trade|trade_history|rules|community|affiliate|support|report|faq)$"))
