import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from utils.enums import TradeTypeEnums

from .crypto import *
from .fiat import *
from .market import *
from .product import *

logger = logging.getLogger(__name__)


class TradeFlowHandler:
    @staticmethod
    async def initiate_flow_setup(
        update: Update, context: ContextTypes.DEFAULT_TYPE, trade_type: str
    ) -> bool:
        """Route to specific trade flow's initial setup method."""
        flow_class = None
        if trade_type == TradeTypeEnums.CRYPTO_FIAT.value:
            flow_class = CryptoFiatFlow
        elif trade_type == TradeTypeEnums.CRYPTO_CRYPTO.value:
            # Ensure CryptoCryptoFlow exists and has a 'start_initial_setup' method
            flow_class = CryptoCryptoFlow
        elif trade_type == TradeTypeEnums.CRYPTO_PRODUCT.value:
            # Ensure CryptoProductFlow exists and has a 'start_initial_setup' method
            flow_class = CryptoProductFlow
        elif trade_type == TradeTypeEnums.MARKET_SHOP.value:
            # Ensure MarketShopFlow exists and has a 'start_initial_setup' method
            flow_class = MarketShopFlow
        else:
            logger.error(
                f"Invalid trade_type '{trade_type}' received in initiate_flow_setup."
            )
            # No need to send a message here, the caller (handle_trade_type_selection) handles it.
            return False

        if flow_class and hasattr(flow_class, "start_initial_setup"):
            try:
                # The query object is needed to edit the message
                query = update.callback_query
                return await getattr(flow_class, "start_initial_setup")(query, context)
            except Exception as e:
                logger.error(f"Error calling start_initial_setup for {trade_type}: {e}")
                return False
        else:
            logger.warning(
                f"Flow class {flow_class} or method start_initial_setup not found for {trade_type}."
            )
            # If a flow is defined in enums but not implemented or method is missing
            if update.callback_query:
                await update.callback_query.message.edit_text(
                    f"🛠️ The setup for {trade_type} trades is currently under construction. Please check back later.",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "🔙 Back to Menu", callback_data="menu"
                                )
                            ]
                        ]
                    ),
                )
            return False

    @staticmethod
    async def route_to_flow_method(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        trade_type: str,
        method_name: str,
    ) -> bool:
        """Route to a specific method within a trade flow class."""
        flow_class = None
        if trade_type == TradeTypeEnums.CRYPTO_FIAT.value:
            flow_class = CryptoFiatFlow
        elif trade_type == TradeTypeEnums.CRYPTO_CRYPTO.value:
            flow_class = CryptoCryptoFlow
        elif trade_type == TradeTypeEnums.CRYPTO_PRODUCT.value:
            flow_class = CryptoProductFlow
        elif trade_type == TradeTypeEnums.MARKET_SHOP.value:
            flow_class = MarketShopFlow
        else:
            logger.error(
                f"Invalid trade_type '{trade_type}' received in route_to_flow_method for method '{method_name}'."
            )
            return False

        if flow_class and hasattr(flow_class, method_name):
            try:
                return await getattr(flow_class, method_name)(update, context)
            except Exception as e:
                logger.error(f"Error calling {method_name} for {trade_type}: {e}")
                return False
        else:
            logger.warning(
                f"Flow class {flow_class} or method {method_name} not found for {trade_type}."
            )
            return False

    # The existing route_trade_flow might be deprecated or adapted if all flow logic starts via initiate_flow_setup
    # For now, keeping it as it might be used by other parts of the system (e.g. resuming a trade)
    @staticmethod
    async def route_trade_flow(
        update: Update, context: ContextTypes.DEFAULT_TYPE, trade_type: str
    ):
        """Route to specific trade flow based on trade type (original method)."""
        if trade_type == TradeTypeEnums.CRYPTO_FIAT.value:
            # from .fiat import CryptoFiatFlow # Already imported at top
            return await CryptoFiatFlow.handle_flow(update, context)

        elif trade_type == TradeTypeEnums.CRYPTO_CRYPTO.value:
            # from .crypto import CryptoCryptoFlow
            return await CryptoCryptoFlow.handle_flow(update, context)

        elif trade_type == TradeTypeEnums.CRYPTO_PRODUCT.value:
            # from .product import CryptoProductFlow
            return await CryptoProductFlow.handle_flow(update, context)

        elif trade_type == TradeTypeEnums.MARKET_SHOP.value:
            # from .market import MarketShopFlow
            return await MarketShopFlow.handle_flow(update, context)

        else:
            # This part is unlikely to be hit if called from handle_trade_description, which is being removed.
            # However, if other parts call it, this error handling is useful.
            # Check if update.message exists before trying to use it.
            target_message = (
                update.callback_query.message
                if update.callback_query
                else update.message
            )
            if target_message:
                await target_message.reply_text(
                    "❌ Invalid trade type encountered during routing.",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "🔙 Back to Menu", callback_data="menu"
                                )
                            ]
                        ]
                    ),
                )
            else:
                logger.error(
                    "route_trade_flow: No message object found in update to send error."
                )
            return False
