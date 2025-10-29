class UserType:
    _id = str
    name = str
    wallet = str
    chat = str
    verified = bool
    disabled = bool
    created_at = str


# New Broker Type
class BrokerType:
    _id: str  # Unique broker identifier (same as user_id)
    user_id: str  # Associated user ID
    broker_name: str  # Display name for broker
    commission_rate: float  # Commission percentage (e.g., 1.5 for 1.5%)
    is_active: bool  # Whether broker is active
    is_verified: bool  # Whether broker is verified by admin
    specialties: list  # List of trade types they specialize in
    total_trades: int  # Number of trades mediated
    successful_trades: int  # Number of successful trades
    rating: float  # Average rating (0.0 - 5.0)
    bio: str  # Broker description/bio
    created_at: str  # Creation timestamp
    updated_at: str  # Last update timestamp


class ChatType:
    _id = str
    name = str
    admin_id = str
    created_at = str


class TradeType:
    _id: str
    seller_id: str
    buyer_id: str
    terms: str
    price: int
    currency: str
    invoice_id: str
    is_active: bool
    is_paid: bool
    is_completed: bool
    chat_id: str
    created_at: str
    updated_at: str
    # New fields for wallet integration
    receiving_address: str  # Wallet address for receiving crypto (ETH/USDT)
    seller_wallet_id: str  # Seller's wallet ID (for ETH/USDT trades)
    is_wallet_trade: bool  # Whether this uses wallet integration

    # New Broker fields
    broker_id: str  # Broker user ID (empty if no broker)
    broker_enabled: bool  # Whether this trade uses a broker
    broker_commission: float  # Broker commission amount
    broker_approved_seller: bool  # Whether broker verified seller
    broker_approved_buyer: bool  # Whether broker verified buyer
    seller_broker_rating: int  # Seller's rating of broker (1-5)
    buyer_broker_rating: int  # Buyer's rating of broker (1-5)
    broker_notes: str  # Broker's notes on the trade

    # Broker-Initiated Trade fields
    is_broker_initiated: bool  # Whether this is a broker-initiated trade
    seller_rate: float  # Rate seller gets (e.g., 3.65 AED/USDT)
    buyer_rate: float  # Rate buyer pays (e.g., 3.69 AED/USDT)
    market_rate: float  # Market rate at creation for profit conversion
    fiat_currency: str  # Fiat currency used (e.g., "AED", "USD")
    payment_method: str  # Payment method: "BANK_TRANSFER" or "CASH_IN_PERSON"
    broker_profit_fiat: float  # Broker profit in fiat currency
    broker_profit_crypto: float  # Broker profit in crypto
    buyer_receive_amount: float  # Amount buyer will receive after broker profit deduction
    seller_instructions: str  # Instructions for the seller
    buyer_instructions: str  # Instructions for the buyer


class DisputeType:
    _id: str
    user_id: str
    trade_id: str
    complaint: str
    is_resolved: bool
    created_at: str


# New Wallet Types for Web3 Integration
class WalletType:
    _id: str  # Unique wallet identifier
    user_id: str  # Associated user ID (one-to-one mapping)
    wallet_name: str  # User-friendly wallet name
    mnemonic_encrypted: str  # Master encrypted mnemonic phrase (for all coins)
    is_active: bool  # Whether wallet is active
    created_at: str  # Creation timestamp
    updated_at: str  # Last update timestamp


class CoinAddressType:
    _id: str  # Unique address identifier
    wallet_id: str  # Associated wallet ID
    coin_symbol: str  # Coin symbol (BTC, ETH, LTC, DOGE, USDT, etc.)
    network: str  # Network (bitcoin, ethereum, litecoin, etc.)
    address: str  # Public address for this coin
    private_key_encrypted: str  # Encrypted private key for this coin
    derivation_path: str  # HD wallet derivation path
    is_default: bool  # Whether this is a default coin for all wallets
    balance: str  # Current balance (cached)
    balance_usd: str  # USD equivalent (cached)
    last_balance_update: str  # Last balance update timestamp
    created_at: str  # Creation timestamp


class WalletTransactionType:
    _id: str  # Unique transaction identifier
    wallet_id: str  # Associated wallet ID
    coin_address_id: str  # Associated coin address ID
    tx_hash: str  # Blockchain transaction hash
    from_address: str  # Sender address
    to_address: str  # Recipient address
    amount: str  # Transaction amount
    coin_symbol: str  # Coin symbol
    fee: str  # Transaction fee
    status: str  # Transaction status (pending, confirmed, failed)
    block_number: int  # Block number
    confirmations: int  # Number of confirmations
    transaction_type: str  # Type: 'send', 'receive', 'deposit', 'withdrawal'
    created_at: str  # Transaction timestamp
    confirmed_at: str  # Confirmation timestamp
