import os
from api import api_bp
from config import *


app = Flask(__name__)


@app.route('/dashboard')
def dashboard():
    return render_template('index.html')


@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200


@app.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://payescrowbot.render.com/' + TOKEN)
    return "Btcpay-Escrow Bot Active!", 200


print("bot polling...")
bot.remove_webhook()
bot.polling(none_stop=True)

# if __name__ == "__main__":
#     app.register_blueprint(api_bp)
#     app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))


