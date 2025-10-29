from enum import Enum


class TradeTypeEnums(Enum):
    CRYPTO_FIAT = "CryptoToFiat"
    CRYPTO_CRYPTO = "CryptoToCrypto"
    CRYPTO_PRODUCT = "CryptoToProduct"
    MARKET_SHOP = "MarketShop"
    BROKER_INITIATED = "BrokerInitiated"

    @staticmethod
    def get_display_name(trade_type: str) -> str:
        """Get full display name with emoji for trade type

        Args:
            trade_type: Raw trade type value (e.g., "CryptoToFiat")

        Returns:
            Display name with emoji (e.g., "💰 Crypto → Fiat Trade")
        """
        display_names = {
            "CryptoToFiat": "💰 Crypto → Fiat Trade",
            "CryptoToCrypto": "🔄 Crypto Swap",
            "CryptoToProduct": "🛍️ Buy Goods with Crypto",
            "MarketShop": "🏪 Marketplace Listing",
            "BrokerInitiated": "🤝 Broker-Initiated Trade",
        }
        return display_names.get(trade_type, trade_type)

    @staticmethod
    def get_short_display_name(trade_type: str) -> str:
        """Get short display name without emoji for trade type

        Args:
            trade_type: Raw trade type value (e.g., "CryptoToFiat")

        Returns:
            Short display name (e.g., "Crypto → Fiat")
        """
        short_names = {
            "CryptoToFiat": "Crypto → Fiat",
            "CryptoToCrypto": "Crypto Swap",
            "CryptoToProduct": "Buy Goods",
            "MarketShop": "Marketplace",
            "BrokerInitiated": "Broker Trade",
        }
        return short_names.get(trade_type, trade_type)


class TradeStatusEnums(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PARTIAL = "partial"
    PAID = "paid"
    COMPLETED = "completed"
    APPROVED = "approved"
    ERROR = "error"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class CryptoCurrencyEnums(Enum):
    USDT = "USDT"
    BTC = "BTC"
    ETH = "ETH"
    SOL = "SOL"
    BNB = "BNB"
    LTC = "LTC"
    DOGE = "DOGE"
    TRX = "TRX"


class FiatCurrencyEnums(Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    AED = "AED"
    SAR = "SAR"
    EGP = "EGP"
    NGN = "NGN"


class PaymentMethodEnums(Enum):
    BANK_TRANSFER = "BANK_TRANSFER"
    CASH_IN_PERSON = "CASH_IN_PERSON"

    @staticmethod
    def get_display_name(method: str) -> str:
        """Get display name for payment method

        Args:
            method: Raw payment method value

        Returns:
            Display name with emoji
        """
        display_names = {
            "BANK_TRANSFER": "🏦 Bank Transfer",
            "CASH_IN_PERSON": "💵 Cash in Person",
        }
        return display_names.get(method, method)


class CallbackDataEnums(Enum):
    # Main Menu
    MENU = "menu"
    CREATE_TRADE = "create_trade"
    JOIN_TRADE = "join_trade"
    TRADE_HISTORY = "trade_history"
    MY_WALLETS = "my_wallets"
    RULES = "rules"
    COMMUNITY = "community"
    AFFILIATE = "affiliate"
    SUPPORT = "support"
    REPORT = "report"
    FAQ = "faq"

    # Wallet
    WALLET_BALANCES = "wallet_balances"
    WALLET_CREATE = "wallet_create"
    WALLET_TRANSACTIONS = "wallet_transactions"
    WALLET_REFRESH = "wallet_refresh"

    # Trade Types
    TRADE_TYPE_PREFIX = "trade_type_"
    CURRENCY_PREFIX = "currency_"

    # Actions
    CANCEL = "cancel"
    BACK = "back"
    CONFIRM = "confirm"
    DELETE = "delete"


class EmojiEnums(Enum):
    # Trade related
    MONEY_BAG = "💰"
    HANDSHAKE = "🤝"
    SCROLL = "📜"
    LOCK = "🔐"
    RULES = "📋"
    CLIPBOARD = "📋"  # Same as rules but named for clarity
    COMMUNITY = "👥"
    TARGET = "🎯"
    QUESTION = "❓"
    MAGNIFYING_GLASS = "🔍"

    # Crypto
    BITCOIN = "₿"
    ETHEREUM = "Ξ"
    SOLANA = "◎"
    YELLOW_CIRCLE = "🟡"  # BNB
    LITECOIN = "Ł"
    DOGECOIN = "Ð"
    TETHER = "₮"
    TRON = "ⓣ"

    # Actions
    CHECK_MARK = "✅"
    CROSS_MARK = "❌"
    WARNING = "⚠️"
    HOURGLASS = "⏳"
    REFRESH = "🔄"
    GEAR = "⚙️"
    BACK_ARROW = "🔙"
    SEND = "💸"
    RECEIVE = "📥"

    # Status
    FIRE = "🔥"
    STAR = "⭐"
    BELL = "🔔"
    ROBOT = "🤖"
    INFO = "ℹ️"


class MessageTypeEnums(Enum):
    WELCOME = "welcome"
    TRADE_CREATED = "trade_created"
    TRADE_JOINED = "trade_joined"
    DEPOSIT_INSTRUCTIONS = "deposit_instructions"
    DEPOSIT_CONFIRMED = "deposit_confirmed"
    DEPOSIT_PENDING = "deposit_pending"
    ERROR = "error"
    SUCCESS = "success"
    WARNING = "warning"
    INFO = "info"
