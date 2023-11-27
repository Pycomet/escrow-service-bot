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
