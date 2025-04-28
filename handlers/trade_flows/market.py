from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from functions.trade import TradeClient
from functions.user import UserClient
import logging

logger = logging.getLogger(__name__)

class MarketShopFlow:
    @staticmethod
    async def handle_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the Market Shop trade flow"""
        current_step = context.user_data.get("trade_creation", {}).get("step")
        
        if current_step == "description":
            return await MarketShopFlow.handle_description(update, context)
        elif current_step == "browse":
            return await MarketShopFlow.handle_browse(update, context)
        else:
            logger.warning(f"Unexpected step in MarketShopFlow: {current_step}")
            return False

    @staticmethod
    async def handle_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the shop description and create market listing"""
        description = update.message.text
        trade_data = context.user_data["trade_creation"]
        
        # Get user from database
        user = UserClient.get_user(update.message)
        
        # Create the market shop trade
        trade = TradeClient.open_new_trade(
            update.message,
            currency=trade_data["currency"],
            trade_type="MarketShop"
        )
        
        if not trade:
            await update.message.reply_text(
                "❌ Failed to create market shop. Please try again.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
                ]])
            )
            return False
        
        # Update trade with description and amount using database user object
        TradeClient.add_terms(user, description)
        TradeClient.add_price(user, trade_data["amount"])
        
        # Create forward text for sharing
        forward_text = (
            f"🏪 New Market Shop\n"
            f"ID: {trade['_id']}\n"
            f"Products starting from: {trade_data['amount']} {trade_data['currency']}\n"
            f"Description: {description}"
        )
        
        # Send success message
        await update.message.reply_text(
            f"✅ Market shop created successfully!\n\n"
            f"Shop ID: <code>{trade['_id']}</code>\n"
            f"Products starting from: {trade_data['amount']} {trade_data['currency']}\n"
            f"Description: {description}\n\n"
            f"Share your shop with potential buyers:",
            parse_mode="html",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📤 Share Shop", switch_inline_query=forward_text)],
                [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]
            ])
        )
        
        # Clear trade creation data
        context.user_data.pop("trade_creation", None)
        return True

    @staticmethod
    async def handle_browse(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle browsing available market shops"""
        # Get list of active market shops
        active_shops = TradeClient.get_active_market_shops()
        
        if not active_shops:
            await update.message.reply_text(
                "❌ No market shops available at the moment.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
                ]])
            )
            return False
        
        # Create keyboard with shop listings
        keyboard = []
        for shop in active_shops:
            keyboard.append([
                InlineKeyboardButton(
                    f"🏪 {shop.get('description', 'Shop')} - From {shop['price']} {shop['currency']}",
                    callback_data=f"view_shop_{shop['_id']}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")])
        
        await update.message.reply_text(
            "🏪 Available Market Shops:\n\n"
            "Select a shop to view details and available products:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return True

    @staticmethod
    async def handle_shop_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle viewing a specific shop"""
        query = update.callback_query
        shop_id = query.data.replace("view_shop_", "")
        
        shop = TradeClient.get_trade(shop_id)
        if not shop:
            await query.edit_message_text(
                "❌ Shop not found. Please try again.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Shops", callback_data="browse_shops")
                ]])
            )
            return False
        
        # Show shop details and products
        await query.edit_message_text(
            f"🏪 <b>{shop.get('description', 'Shop')}</b>\n\n"
            f"ID: <code>{shop['_id']}</code>\n"
            f"Products from: {shop['price']} {shop['currency']}\n\n"
            f"To make a purchase, click the button below:",
            parse_mode="html",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🛍️ Make Purchase", callback_data=f"purchase_{shop['_id']}")],
                [InlineKeyboardButton("🔙 Back to Shops", callback_data="browse_shops")]
            ])
        )
        return True
