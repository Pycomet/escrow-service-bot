"""
Handler Registration System

This module provides a centralized way to register handlers without
triggering application creation at import time.
"""
import logging

logger = logging.getLogger(__name__)

# Store handlers to be registered later
_pending_handlers = []

def register_handler_later(handler):
    """Store a handler to be registered when the application is ready"""
    _pending_handlers.append(handler)

def register_all_pending_handlers(application):
    """Register all pending handlers with the application"""
    if application is None:
        logger.warning("Cannot register handlers: application is None")
        return
    
    registered_count = 0
    failed_count = 0
    
    for handler in _pending_handlers:
        try:
            application.add_handler(handler)
            registered_count += 1
        except Exception as e:
            logger.error(f"Failed to register handler {handler}: {e}")
            failed_count += 1
    
    logger.info(f"Handler registration complete: {registered_count} registered, {failed_count} failed")
    
    # Clear the pending handlers list
    _pending_handlers.clear()

def get_pending_handler_count():
    """Get the number of pending handlers"""
    return len(_pending_handlers)
