from config import *
from utils import *
from functions import *
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters


async def rules_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /rules command"""
    rules_text = (
        "📜 <b>Escrow Service Rules</b>\n\n"
        "1. <b>General Rules</b>\n"
        "• All trades must be conducted through our escrow service\n"
        "• Both parties must agree to the terms before starting a trade\n"
        "• Payments must be made within the specified time frame\n\n"
        
        "2. <b>Seller Responsibilities</b>\n"
        "• Provide accurate description of goods/services\n"
        "• Deliver goods/services as agreed\n"
        "• Respond to buyer inquiries promptly\n\n"
        
        "3. <b>Buyer Responsibilities</b>\n"
        "• Make payment within the agreed time frame\n"
        "• Verify goods/services upon receipt\n"
        "• Report any issues promptly\n\n"
        
        "4. <b>Dispute Resolution</b>\n"
        "• All disputes must be reported through the bot\n"
        "• Provide evidence to support your claim\n"
        "• Allow reasonable time for resolution\n\n"
        
        "5. <b>Fees and Payments</b>\n"
        "• Service fees are clearly displayed before trade\n"
        "• Payments are held in escrow until completion\n"
        "• Refunds are processed according to our policy\n\n"
        
        "6. <b>Prohibited Activities</b>\n"
        "• Fraudulent transactions\n"
        "• Misrepresentation of goods/services\n"
        "• Attempting to bypass the escrow service\n"
        "• Harassment or abusive behavior\n\n"
        
        "By using our service, you agree to these rules. "
        "Violations may result in account suspension or permanent ban."
    )
    
    await update.message.reply_text(
        rules_text,
        parse_mode="html",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
        ]])
    )


async def community_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /community command"""
    community_text = (
        "👥 <b>Join Our Community</b>\n\n"
        "Connect with other users and stay updated:\n\n"
        "📢 <b>Official Channel:</b>\n"
        "@trusted_escrow_bot_updates\n\n"
        "💬 <b>Discussion Group:</b>\n"
        "@trusted_escrow_bot_group\n\n"
        "📱 <b>Reviews Channel:</b>\n"
        "@trusted_escrow_bot_reviews\n\n"
        "Follow us for:\n"
        "• Latest updates and features\n"
        "• Community discussions\n"
        "• User reviews and testimonials\n"
        "• Support and assistance"
    )
    
    await update.message.reply_text(
        community_text,
        parse_mode="html",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Join Channel", url="https://t.me/trusted_escrow_bot_updates")],
            [InlineKeyboardButton("💬 Join Group", url="https://t.me/trusted_escrow_bot_group")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]
        ])
    )


def register_handlers(application):
    """Register handlers for the rules module"""
    application.add_handler(CommandHandler("rules", rules_handler))
    application.add_handler(CommandHandler("community", community_handler))
