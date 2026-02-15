import os
import requests
import time
import threading
from flask import Flask, request

TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("API_KEY")

app = Flask(__name__)
users = set()
last_alert = None

# ✅ Route باش Render يبقى صاحي
@app.route("/")
def home():
    return "Bot is running ✅"

# 🔥 جلب سعر الذهب بطريقة صحيحة
def get_gold_price():
    try:
        url = f"https://api.metals.dev/v1/latest?api_key={API_KEY}&base=USD&symbols=XAU"
        response = requests.get(url, timeout=10)
        data = response.json()

        print("API RESPONSE:", data)  # يظهر في Logs

        # Metals.dev يرجع XAU داخل rates
        if "rates" in data and "XAU" in data["rates"]:
            xau_rate = float(data["rates"]["XAU"])
            gold_price = round(1 / xau_rate, 2)  # نحولو لسعر الأونصة بالدولار
            return gold_price
        else:
            print("Unexpected API format:", data)
            return None

    except Exception as e:
        print("REAL ERROR:", e)
        return None


def send_message(chat_id, text):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": chat_id, "text": text})
    except Exception as e:
        print("Telegram error:", e)


@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    global users

    data = request.json
    if not data:
        return "no data"

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")
        users.add(chat_id)

        if text.lower() == "prix":
            price = get_gold_price()
            if price:
                send_message(chat_id, f"💰 Gold price now: {price}$ per ounce")
            else:
                send_message(chat_id, "⚠️ Error getting gold price.")

    return "ok"


# 🔔 نظام التنبيه التلقائي
def check_price():
    global last_alert

    while True:
        try:
            price = get_gold_price()

            if price:
                if price <= 2900 and last_alert != "down":
                    for u in users:
                        send_message(u, "📉 Gold dropped below 2900$")
                    last_alert = "down"

                elif price >= 3000 and last_alert != "up":
                    for u in users:
                        send_message(u, "📈 Gold is above 3000$")
                    last_alert = "up"

        except Exception as e:
            print("Monitor error:", e)

        time.sleep(300)  # كل 5 دقائق


if __name__ == "__main__":
    t = threading.Thread(target=check_price)
    t.daemon = True
    t.start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
