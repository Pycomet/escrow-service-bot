def get_trade_status(trade):
    """
    Determine trade status based on trade_type, is_active, and is_paid flags
    Returns tuple of (status, emoji)
    """
    trade_type = trade.get('trade_type', '')
    is_active = trade.get('is_active', False)
    is_paid = trade.get('is_paid', False)
    is_completed = trade.get('is_completed', False)

    # Status emoji mapping
    STATUS_EMOJI = {
        'awaiting_payment': '💳',
        'awaiting_deposit': '⏳',
        'awaiting_confirmation': '⌛',
        'completed': '✅',
        'cancelled': '❌',
        'disputed': '⚠️',
        'pending': '🕒'
    }

    # Determine status based on trade type and flags
    if not is_active and not is_paid and not is_completed:
        status = 'cancelled'
    elif is_completed:
        status = 'completed'
    elif trade_type == 'CryptoToFiat':
        if not is_paid:
            status = 'awaiting_deposit'
        elif is_paid and not is_completed:
            status = 'awaiting_confirmation'
    elif trade_type == 'FiatToCrypto':
        if not is_paid:
            status = 'awaiting_payment'
        elif is_paid and not is_completed:
            status = 'awaiting_confirmation'
    else:
        status = 'pending'

    emoji = STATUS_EMOJI.get(status, '❓')
    return status, emoji

def format_trade_status(status):
    """
    Format status string for display
    """
    return status.replace('_', ' ').title() 