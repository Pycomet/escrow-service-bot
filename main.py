import os
from api import api_bp
from config import *
from handlers import *


app = Flask(__name__)
    

@app.route("/" + TOKEN, methods=["POST"])
def checkWebhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    print(update)
    bot.process_new_updates([update])
    return "Your bot application is still active!", 200


@app.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL + "/" + TOKEN)
    return "Btcpay-Escrow Bot running!", 200


def run_web():
    if __name__ == "__main__":
        # app.register_blueprint(api_bp)
        app.run(
            host="0.0.0.0",
            threaded=True,
            port=int(os.environ.get('PORT', 5004)),
        )


def run_poll():
    webhook_info = bot.get_webhook_info()
    if webhook_info.url:
        bot.delete_webhook()
    bot.infinity_polling()
    print("Bot polling!")


if WEBHOOK_MODE == "False":
    run_poll()
else:
    run_web()
