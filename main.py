import asyncio
import logging
from quart import Quart, request, jsonify
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram.error import TelegramError
from config import *
from handlers import *
from utils import *
from functions import *

# Register all handlers
def register_handlers():
    """Register all handlers for the bot"""
    try:
        # Import and register handlers from each module
        from handlers.start import register_handlers as register_start
        from handlers.callbacks import register_handlers as register_callbacks
        from handlers.initiate_trade import register_handlers as register_initiate_trade
        from handlers.join import register_handlers as register_join
        from handlers.rules import register_handlers as register_rules
        from handlers.history import register_handlers as register_history
        from handlers.delete_trade import register_handlers as register_delete_trade
        from handlers.review import register_handlers as register_review
        from handlers.affiliate import register_handlers as register_affiliate
        from handlers.report import register_handlers as register_report
        from handlers.verdict import register_handlers as register_verdict
        
        # Register handlers from each module
        register_start(application)
        register_callbacks(application)
        register_initiate_trade(application)
        register_join(application)
        register_rules(application)
        register_history(application)
        register_delete_trade(application)
        register_review(application)
        register_affiliate(application)
        register_report(application)
        register_verdict(application)
        
        logger.info("All handlers registered successfully")
    except Exception as e:
        logger.error(f"Error registering handlers: {e}")
        raise


@app.before_serving
async def startup():
    """Initialize the application before serving"""
    try:
        await application.initialize()
        await application.start()
        register_handlers()
        logger.info("Bot started successfully")
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise


@app.after_serving
async def shutdown():
    """Clean up resources after serving"""
    try:
        await application.stop()
        await application.shutdown()
        logger.info("Bot stopped successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


@app.route('/health', methods=['GET'])
async def health_check():
    """Health check endpoint"""
    try:
        if not application.running:
            return jsonify({"status": "error", "message": "Application not running"}), 503
        
        # Check if bot can connect to Telegram
        await application.bot.get_me()
        return jsonify({"status": "healthy", "message": "Bot is running"}), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/webhook', methods=['POST'])
async def webhook():
    """Handle incoming webhook updates"""
    try:
        if not application.running:
            await application.initialize()
            await application.start()
            register_handlers()
        
        update_data = await request.get_json()
        if not update_data:
            return jsonify({"status": "error", "message": "No update data received"}), 400
        
        update = Update.de_json(update_data, application.bot)
        await application.process_update(update)
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/set_webhook', methods=['GET'])
async def set_webhook():
    """Set the webhook for the bot"""
    try:
        if not application.running:
            await application.initialize()
            await application.start()
            register_handlers()
        
        if not WEBHOOK_URL:
            return jsonify({"status": "error", "message": "WEBHOOK_URL not configured"}), 400
        
        # Set webhook with additional parameters for better security and functionality
        await application.bot.set_webhook(
            url=WEBHOOK_URL,
            allowed_updates=["message", "callback_query", "inline_query", "chosen_inline_result"],
            drop_pending_updates=True,
            max_connections=40
        )
        return jsonify({"status": "success", "message": f"Webhook set to {WEBHOOK_URL}"}), 200
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


def run_polling():
    """Run the bot in polling mode"""
    register_handlers()  # Register handlers before starting polling
    logger.info("Starting bot in polling mode...")
    application.run_polling(drop_pending_updates=True)


if __name__ == '__main__':
    if WEBHOOK_MODE == True:
        # Run in webhook mode (production/deployment)
        logger.info("Starting bot in webhook mode...")
        app.run(host='0.0.0.0', port=PORT)
    else:
        # Run in polling mode (local development)
        run_polling()