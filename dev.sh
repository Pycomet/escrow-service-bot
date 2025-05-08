#!/bin/bash

# Function to check if a process is running
check_process() {
    if pgrep -f "$1" > /dev/null; then
        echo "✅ $1 is running"
        return 0
    else
        echo "❌ $1 is not running"
        return 1
    fi
}

# Function to show status
show_status() {
    echo "=== Current Status ==="
    check_process "ngrok"
    check_process "python main.py"
    echo "====================="
}

# Function to display URLs
show_urls() {
    echo "============================================="
    echo "🌐 Ngrok URL: $NGROK_URL"
    echo "🔗 Webhook URL: $WEBHOOK_URL"
    echo "============================================="
    echo "📋 Copy the Webhook URL above to test your bot"
    echo "============================================="
}

# Function to stop services
stop_services() {
    echo "Stopping services..."
    pkill -f "python main.py"
    pkill -f "ngrok"
    show_status
}

# Function to set webhook with Telegram
set_telegram_webhook() {
    local webhook_url=$1
    local token=$2
    
    echo "Setting Telegram webhook to: $webhook_url"
    response=$(curl -s "https://api.telegram.org/bot$token/setWebhook" \
        -d "url=$webhook_url" \
        -d "allowed_updates=[\"message\",\"callback_query\"]")
    
    echo "Webhook setup response: $response"
}

# Function to check webhook status
check_webhook_status() {
    local token=$1
    echo "Checking webhook status..."
    curl -s "https://api.telegram.org/bot$token/getWebhookInfo" | jq .
}

# Function to start services
start_services() {
    # Stop any existing processes
    echo "Stopping existing processes..."
    pkill -f "python main.py"
    pkill -f "ngrok"

    # Install dependencies if needed
    echo "Installing dependencies..."
    pip install -r requirements.txt

    # Start ngrok
    echo "Starting ngrok..."
    nohup ngrok http 8000 > ngrok.log 2>&1 &
    NGROK_PID=$!

    # Wait for ngrok to start
    sleep 5

    # Get the ngrok URL
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | jq -r '.tunnels[0].public_url')
    if [ -z "$NGROK_URL" ]; then
        echo "Failed to get ngrok URL. Please check ngrok.log for errors."
        kill $NGROK_PID
        exit 1
    fi

    # Set environment variables
    export WEBHOOK_MODE=true
    export WEBHOOK_URL="${NGROK_URL}/webhook"
    export PORT=8000

    # Set the webhook with Telegram
    if [ -z "$TOKEN" ]; then
        echo "Error: TOKEN environment variable is not set"
        exit 1
    fi
    set_telegram_webhook "$WEBHOOK_URL" "$TOKEN"
    check_webhook_status "$TOKEN"

    # Start the application in the background
    echo "Starting the application..."
    nohup python main.py > bot.log 2>&1 &
    BOT_PID=$!

    # Wait for the application to start
    sleep 5

    # Show initial status
    show_status
    show_urls

    echo "Services started successfully!"
    echo "To monitor logs:"
    echo "  Bot logs: tail -f bot.log"
    echo "  Ngrok logs: tail -f ngrok.log"
    echo "To stop services: ./deploy.sh stop"
}

# Function to monitor logs
monitor_logs() {
    echo "Monitoring logs (Press Ctrl+C to stop)..."
    tail -f bot.log ngrok.log
}

# Handle command line arguments
case "$1" in
    "start")
        start_services
        ;;
    "stop")
        stop_services
        ;;
    "status")
        show_status
        ;;
    "logs")
        monitor_logs
        ;;
    "urls")
        if [ -n "$NGROK_URL" ]; then
            show_urls
        else
            echo "No active ngrok tunnel found. Start the services first with ./deploy.sh start"
        fi
        ;;
    "webhook")
        if [ -z "$TOKEN" ]; then
            echo "Error: TOKEN environment variable is not set"
            exit 1
        fi
        check_webhook_status "$TOKEN"
        ;;
    *)
        echo "Usage: ./deploy.sh {start|stop|status|logs|urls|webhook}"
        echo "  start   - Start the services"
        echo "  stop    - Stop the services"
        echo "  status  - Show service status"
        echo "  logs    - Monitor logs"
        echo "  urls    - Show ngrok and webhook URLs"
        echo "  webhook - Check webhook status"
        exit 1
        ;;
esac 