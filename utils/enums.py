from enum import Enum


class TradeTypeEnums(Enum):
    CRYPTO_FIAT = "CryptoToFiat"
    CRYPTO_CRYPTO = "CryptoToCrypto"
    CRYPTO_PRODUCT = "CryptoToProduct"
    MARKET_SHOP = "MarketShop"


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
