from .start import *
from .callbacks import *
from .initiate_trade import *
from .join import *
from .rules import *
from .history import *
from .delete_trade import *
from .review import *
from .affiliate import *
from .webhook import *
from .report import *
from .verdict import *

__all__ = [
    'start',
    'callbacks',
    'initiate_trade',
    'join',
    'rules',
    'history',
    'delete_trade',
    'review',
    'affiliate',
    'webhook',
    'report',
    'verdict'
]

# Register handlers
application.add_handler(CommandHandler("start", start))