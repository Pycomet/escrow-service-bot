from .fiat import *
from .crypto import *
from .product import *
from .market import *
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from utils.enums import TradeTypeEnums
import logging

logger = logging.getLogger(__name__)

class TradeFlowHandler:
    @staticmethod
    async def route_trade_flow(update: Update, context: ContextTypes.DEFAULT_TYPE, trade_type: str):
        """Route to specific trade flow based on trade type"""
        if trade_type == TradeTypeEnums.CRYPTO_FIAT.value:
            from .fiat import CryptoFiatFlow
            return await CryptoFiatFlow.handle_flow(update, context)
        
        elif trade_type == TradeTypeEnums.CRYPTO_CRYPTO.value:
            from .crypto import CryptoCryptoFlow
            return await CryptoCryptoFlow.handle_flow(update, context)
        
        elif trade_type == TradeTypeEnums.CRYPTO_PRODUCT.value:
            from .product import CryptoProductFlow
            return await CryptoProductFlow.handle_flow(update, context)
        
        elif trade_type == TradeTypeEnums.MARKET_SHOP.value:
            from .market import MarketShopFlow
            return await MarketShopFlow.handle_flow(update, context)
        
        else:
            await update.message.reply_text(
                "❌ Invalid trade type selected.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
                ]])
            )
            return False