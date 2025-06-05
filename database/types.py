class UserType:
    _id = str
    name = str
    wallet = str
    chat = str
    verified = bool
    disabled = bool
    created_at = str


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


class DisputeType:
    _id: str
    user_id: str
    trade_id: str
    complaint: str
    is_resolved: bool
    created_at: str


# New Wallet Types for Web3 Integration
class WalletType:
    _id: str                    # Unique wallet identifier
    user_id: str               # Associated user ID (one-to-one mapping)
    wallet_name: str           # User-friendly wallet name
    mnemonic_encrypted: str    # Master encrypted mnemonic phrase (for all coins)
    is_active: bool           # Whether wallet is active
    created_at: str           # Creation timestamp
    updated_at: str           # Last update timestamp


class CoinAddressType:
    _id: str                    # Unique address identifier
    wallet_id: str             # Associated wallet ID
    coin_symbol: str           # Coin symbol (BTC, ETH, LTC, DOGE, USDT, etc.)
    network: str               # Network (bitcoin, ethereum, litecoin, etc.)
    address: str               # Public address for this coin
    private_key_encrypted: str # Encrypted private key for this coin
    derivation_path: str       # HD wallet derivation path
    is_default: bool          # Whether this is a default coin for all wallets
    balance: str              # Current balance (cached)
    balance_usd: str          # USD equivalent (cached)
    last_balance_update: str  # Last balance update timestamp
    created_at: str           # Creation timestamp


class WalletTransactionType:
    _id: str                 # Unique transaction identifier
    wallet_id: str          # Associated wallet ID
    coin_address_id: str    # Associated coin address ID
    tx_hash: str            # Blockchain transaction hash
    from_address: str       # Sender address
    to_address: str         # Recipient address
    amount: str             # Transaction amount
    coin_symbol: str        # Coin symbol
    fee: str               # Transaction fee
    status: str            # Transaction status (pending, confirmed, failed)
    block_number: int      # Block number
    confirmations: int     # Number of confirmations
    transaction_type: str  # Type: 'send', 'receive', 'deposit', 'withdrawal'
    created_at: str        # Transaction timestamp
    confirmed_at: str      # Confirmation timestamp
