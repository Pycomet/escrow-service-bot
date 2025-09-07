import asyncio
import logging

from quart import Quart, jsonify, request
from telegram import Bot, Update
from telegram.error import TelegramError
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from config import *
from functions import *
from handlers.webhook import process_merchant_webhook
from utils import *


# Register all handlers
def register_handlers():
    """Register all handlers for the bot"""
    try:
        # Check if application is available (might be None in testing)
        if application is None:
            logger.warning("Application is None, skipping handler registration")
            return

        # Import and register handlers from each module
        from handlers.admin import register_handlers as register_admin
        from handlers.affiliate import register_handlers as register_affiliate
        from handlers.broker import register_broker_handlers
        from handlers.callbacks import register_handlers as register_callbacks
        from handlers.delete_trade import register_handlers as register_delete_trade
        from handlers.history import register_handlers as register_history
        from handlers.initiate_trade import register_handlers as register_initiate_trade
        from handlers.join import register_handlers as register_join
        from handlers.report import register_handlers as register_report
        from handlers.review import register_handlers as register_review
        from handlers.rules import register_handlers as register_rules
        from handlers.start import register_handlers as register_start
        from handlers.verdict import register_handlers as register_verdict

        # Register handlers from each module
        register_start(application)
        register_initiate_trade(
            application
        )  # Register first to ensure cancel_creation has priority
        register_callbacks(application)
        register_join(application)
        register_rules(application)
        register_history(application)
        register_delete_trade(application)
        register_review(application)
        register_affiliate(application)
        register_report(application)
        register_verdict(application)
        register_admin(application)
        register_broker_handlers(application)

        logger.info("All handlers registered successfully")
    except Exception as e:
        logger.error(f"Error registering handlers: {e}")
        raise


@app.before_serving
async def startup():
    """Initialize the application before serving"""
    try:
        logger.info("Starting application initialization...")

        # Initialize application without waiting for full telegram bot setup
        loop = asyncio.get_event_loop()
        # Run initialization in background to prevent blocking startup
        loop.create_task(initialize_bot())

        logger.info("Application ready to serve requests")
    except Exception as e:
        logger.error(f"Error during startup, but continuing to serve: {e}")
        # Don't re-raise - allow the application to start even if there are issues
        # The health check endpoint will report the status


async def initialize_bot():
    """Initialize the bot in background to not block startup"""
    try:
        logger.info("Initializing Telegram bot...")

        # Check if application is available (might be None in testing)
        if application is None:
            logger.warning("Application is None, skipping bot initialization")
            return

        await application.initialize()
        await application.start()
        register_handlers()
        
        # Initialize community content scheduler
        try:
            from community.scheduler import start_community_scheduler
            await start_community_scheduler()
            logger.info("Community content scheduler initialized")
        except Exception as scheduler_error:
            logger.error(f"Failed to initialize community scheduler: {scheduler_error}")

        # Set webhook if in webhook mode
        if WEBHOOK_MODE and WEBHOOK_URL:
            logger.info("Checking for existing webhooks...")
            try:
                webhook_info = await application.bot.get_webhook_info()
                if webhook_info.url != WEBHOOK_URL:
                    if webhook_info.url:
                        logger.info(
                            f"Different webhook already set: {webhook_info.url}, removing it..."
                        )
                        await application.bot.delete_webhook()

                    logger.info(f"Setting webhook to {WEBHOOK_URL}")
                    await application.bot.set_webhook(
                        url=WEBHOOK_URL,
                        allowed_updates=[
                            "message",
                            "callback_query",
                            "inline_query",
                            "chosen_inline_result",
                        ],
                        drop_pending_updates=True,
                        max_connections=40,
                    )

                    # Verify webhook was set correctly
                    webhook_info = await application.bot.get_webhook_info()
                    if webhook_info.url == WEBHOOK_URL:
                        logger.info("Webhook set and verified successfully")
                    else:
                        logger.warning(
                            f"Webhook verification failed. Expected: {WEBHOOK_URL}, Got: {webhook_info.url}"
                        )
                else:
                    logger.info("Webhook is already correctly set. No changes needed.")
            except Exception as webhook_error:
                logger.error(f"Error setting webhook but continuing: {webhook_error}")
        else:
            logger.info("Webhook mode is disabled")

        logger.info("Bot initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize bot (will retry on requests): {e}")
        # We'll initialize the bot on-demand in the request handlers


@app.after_serving
async def shutdown():
    """Clean up resources after serving"""
    try:
        if application is not None:
            await application.stop()
            await application.shutdown()
            logger.info("Bot stopped successfully")
        else:
            logger.info("No application to shutdown")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


@app.route("/health", methods=["GET"])
async def health_check():
    """Health check endpoint - simplified to ensure Cloud Run startup succeeds"""
    try:
        status = {
            "status": "ok",
            "message": "Service is running",
            "details": {
                "application_running": application.running if application else False
            },
        }

        # Only check Telegram API status if application is running
        if application and application.running:
            try:
                # Set a short timeout for the request
                bot_info = await asyncio.wait_for(application.bot.get_me(), timeout=2.0)
                status["details"]["bot_name"] = bot_info.username
                status["details"]["bot_connected"] = True
            except asyncio.TimeoutError:
                status["details"]["bot_connected"] = False
                status["details"]["bot_error"] = "Telegram API timeout"
            except Exception as bot_err:
                status["details"]["bot_connected"] = False
                status["details"]["bot_error"] = str(bot_err)
        else:
            status["details"]["bot_connected"] = False
            status["details"]["bot_error"] = "Application not initialized"

        return jsonify(status), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return (
            jsonify(
                {"status": "error", "message": "Health check error", "error": str(e)}
            ),
            500,
        )


@app.route("/webhook", methods=["POST"])
async def webhook():
    """Handle incoming webhook updates"""
    try:
        # Check if application is available
        if application is None:
            logger.error("Application is None, cannot process webhook")
            return (
                jsonify({"status": "error", "message": "Bot not initialized"}),
                503,
            )

        # Initialize the bot if it's not running
        if not application.running:
            logger.info("Bot not running, initializing on demand...")
            try:
                await application.initialize()
                await application.start()
                register_handlers()
                logger.info("Bot initialized successfully on-demand")
            except Exception as init_err:
                logger.error(f"Failed to initialize bot on-demand: {init_err}")
                return (
                    jsonify(
                        {"status": "error", "message": "Bot initialization failed"}
                    ),
                    500,
                )

        update_data = await request.get_json()
        if not update_data:
            return (
                jsonify({"status": "error", "message": "No update data received"}),
                400,
            )

        update = Update.de_json(update_data, application.bot)
        await application.process_update(update)
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/set_webhook", methods=["GET"])
async def set_webhook():
    """Set the webhook for the bot"""
    try:
        # Check if application is available
        if application is None:
            logger.error("Application is None, cannot set webhook")
            return (
                jsonify({"status": "error", "message": "Bot not initialized"}),
                503,
            )

        if not application.running:
            await application.initialize()
            await application.start()
            register_handlers()

        if not WEBHOOK_URL:
            return (
                jsonify({"status": "error", "message": "WEBHOOK_URL not configured"}),
                400,
            )

        # Delete any existing webhook
        logger.info("Removing any existing webhook...")
        await application.bot.delete_webhook()

        # Set webhook with additional parameters for better security and functionality
        logger.info(f"Setting webhook to {WEBHOOK_URL}")
        await application.bot.set_webhook(
            url=WEBHOOK_URL,
            allowed_updates=[
                "message",
                "callback_query",
                "inline_query",
                "chosen_inline_result",
            ],
            drop_pending_updates=True,
            max_connections=40,
        )

        # Verify webhook was set correctly
        webhook_info = await application.bot.get_webhook_info()
        webhook_status = "success" if webhook_info.url == WEBHOOK_URL else "warning"
        webhook_message = f"Webhook set to {WEBHOOK_URL}"

        if webhook_status == "warning":
            webhook_message += f" but verification shows {webhook_info.url}"

        return jsonify({"status": webhook_status, "message": webhook_message}), 200
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/pay", methods=["POST"])
async def handle_payment_webhook():
    """Handle payment webhook from merchant"""
    try:
        # Check if application is available
        if application is None:
            logger.error("Application is None, cannot process payment webhook")
            return (
                jsonify({"status": "error", "message": "Bot not initialized"}),
                503,
            )

        if not application.running:
            await application.initialize()
            await application.start()
            register_handlers()

        result = await process_merchant_webhook(application.bot)
        return result
    except Exception as e:
        logger.error(f"Error processing payment webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/", methods=["GET"])
async def root():
    """Simple root endpoint for Cloud Run's default health checks"""
    return (
        jsonify({"status": "ok", "message": "Service is ready to handle requests"}),
        200,
    )


def run_polling():
    """Run the bot in polling mode"""
    if application is None:
        logger.error("Application is None, cannot run in polling mode")
        return

    register_handlers()  # Register handlers before starting polling
    logger.info("Starting bot in polling mode...")
    application.run_polling(drop_pending_updates=True)


# Don't run app.run() here since entrypoint.sh handles starting the server with hypercorn
if __name__ == "__main__":
    if WEBHOOK_MODE == True:
        # Run in webhook mode (production/deployment)
        logger.info("Starting bot in webhook mode...")
        app.run(host="0.0.0.0", port=PORT)
    else:
        # Run in polling mode (local development)
        run_polling()
